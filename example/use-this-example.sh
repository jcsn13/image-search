#!/bin/bash

# Set the project ID
PROJECT_ID="projectid"

# Set the region
REGION="us-central1"

# Set the bucket name #the bucket name is the PROJECT_ID + "-raw-images"
BUCKET_NAME="${PROJECT_ID}-raw-images"

# Set the directory path to location_images
IMAGES_DIR="./location_images"

# Run the upload script
python upload.py --bucket "$BUCKET_NAME" --dir "$IMAGES_DIR"