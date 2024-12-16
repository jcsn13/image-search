#!/bin/bash

# Set the project ID
PROJECT_ID="projectid"

# Set the region
REGION="us-central1"

# Set the bucket name #the bucket name is the PROJECT_ID + "-raw-images"
BUCKET_NAME="${PROJECT_ID}-raw-images"

# Set the file path
FILE_PATH="./largo da batata/image001.jpg"

# Run the upload script
python upload.py --bucket "$BUCKET_NAME" --file "$FILE_PATH"