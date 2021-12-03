### Da Vinci Code

# Motivation
At Convex Labs, we’re NFT fanatics. We believe that NFTs represent a revolution in the art and collectibles spaces. This repo is a demonstration of the image and metadata generation process.

The current version of the script only has the capabilitiy to change colors and add one extra layer. The generated images are simple images. You can update the rarity sheet locally with different colors and add more trait images. We plan to include more sophisticated images and update the code base with a more advanced image generation script.


# Installation
Install the package locally using pip, or clone our repo
pip install opencv-python
pip install numpy

# Simple Tutorial
From the command line, run "python3 generate.py" to generate images using rarity sheet, base image and traits

From the command line, run "python3 generate.py --mode=metadata" to generate metadata using rarity sheet
