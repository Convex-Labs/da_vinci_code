#pip install opencv-python
#pip install numpy

import datetime
import argparse
import os, glob
import sys
import csv
from PIL import Image
import numpy as np
import colorsys
import cv2
import re
from concurrent.futures import ThreadPoolExecutor
import random
import json

parser = argparse.ArgumentParser()
parser.add_argument('--threads', help='number of threads', default='3')
parser.add_argument('--cutoff', help='serial number cutoff for processing', default='0')
parser.add_argument('--input_sheet', help='input CSV file', default='rarity_sheet.csv')
parser.add_argument('--image_dir', help='Directory containing all the images', default='Traits')
parser.add_argument('--base_image', help='Path to base image', default='Traits/base-image.png')
parser.add_argument('--output_dir', help='Output directory', default='output')
parser.add_argument('--mode', help='Generate image or metadata', default='image')
args = parser.parse_args()

if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)

if not os.path.exists(args.image_dir):
    sys.exit("Image directory " + args.image_dir + " doesn't exist.")

if not os.path.isfile(args.base_image):
    sys.exit("Invalid base image " + args.base_image)


# helper function to read data from a csv file
def readCsv(file_name):
    rows = []
    with open(file_name, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            nrow = {}
            for x in row:
                nrow[x] = row[x].strip()
            rows.append(nrow)
            line_count += 1
    print(f'Processed {line_count} lines.')
    return rows

# helper function to add another layer on top of the image
def pasteImages(layers, output = "output/temp.png"):
    im1 = Image.new("RGBA", (500, 500), (255, 255, 255))
    for overlay in layers:
        im2 = Image.open(overlay).convert("RGBA")
        im1.paste(im2, (0, 0), im2)
    im1 = im1.convert("RGB")
    im1.save(output, format="JPEG", quality=50)


# helper function to convert hex to rgb
def convertHexToRgb(hex):
    h = hex.lstrip('#')
    # we need to reverse the RGB representation as it is required by the cv2 library
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))[::-1]


# function to take input from rarity sheet and change colors 
def floodFill(input_img, output_img, hex, hex2):
    flood = cv2.imread(input_img)
    loDiff = (5, 5, 5, 5)
    upDiff = (5, 5, 5, 5)

    ncolor = convertHexToRgb(hex)
    ncolor2 = convertHexToRgb(hex2)

    # upper circle: head
    seed = (250, 150)
    cv2.floodFill(flood, None, seedPoint=seed, newVal=ncolor, loDiff=loDiff,
                  upDiff=upDiff)

    # lower circle: body
    seed = (250, 250)
    cv2.floodFill(flood, None, seedPoint=seed, newVal=ncolor2, loDiff=loDiff,
                  upDiff=upDiff)

    cv2.imwrite(output_img, flood)


# function to generate new images based on traits and base image
def generate_image(image):
    print("Generating image " + image['Number'])
    startTime = datetime.datetime.now()
    print('startTime ', startTime)
    token_dir = args.output_dir + "/" + image['Number']
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)
    output_image = token_dir + "/base.jpg"
    try:
        temp = token_dir + "/temp.png"

        floodFill(args.base_image, temp, image['Head_Color'], image['Body_Color'])
        layers = [
            'Eye/' + image['Eye']
        ]
    
        # convert to absolute path
        pruned_layers = []
        for layer in layers:
            full_path = args.image_dir + '/' + layer + '.png'
            pruned_layers.append(full_path)

        # add actual layer
        pruned_layers = [temp] + pruned_layers
        pasteImages(pruned_layers, output_image)

        # Delete all temporary files
        for filename in glob.glob(token_dir + "/temp*"):
            os.remove(filename)

    except Exception as ex:
        print("=== Expection: ", ex)
    print('Processing time: ', datetime.datetime.now() - startTime)


# helper function to convert string to json format
def stdTrait(str):
    str = re.sub(r"(_|-)", " ", str)
    str = str.title()
    return str


# function to generate json files
def generate_metadata(image):
    print("creating json file at " + args.output_dir + '/' + image['Number'] + '/base.json')
    save_metadata(image, args.output_dir + '/' + image['Number'] + '/base.json', image['Number'] + "/base.jpg")


# function to convert strings to json format and saves the file as .json
def save_metadata(image, output_file, image_path):
    attributes = []
    for attribute in ['Head_Color', 'Body_Color', 'Eye']:
        if len(image[attribute]) > 0:
            attributes.append({
                "trait_type": stdTrait(attribute),
                "value": stdTrait(image[attribute])
            })

    metadata = {
        "name": image['Number'],
        "description": image['Number'],
        "attributes": attributes,
        "image": "ipfs://####IPFSPREFIX####/" + image_path  # TODO: IPFSPREFIX to be replaced before uploading
    }
    with open(output_file, 'w') as outfile:
        json.dump(metadata, outfile, indent=4)


schema_obj = readCsv(args.input_sheet)
print('Overall start time: ', datetime.datetime.now())
with ThreadPoolExecutor(max_workers=int(args.threads)) as exe:
    for image in schema_obj:
        if int(image["Number"]) > int(args.cutoff):
            if args.mode == "image":
                exe.submit(generate_image, image)
            elif args.mode == "metadata":
                exe.submit(generate_metadata, image)
