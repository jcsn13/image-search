#!/bin/bash

# Set the project ID
PROJECT_ID="mock-project"

# Set the bucket name
BUCKET_NAME="${PROJECT_ID}-raw-images"

# Set the directory path to location_images
IMAGES_DIR="./location_images"

# Run the mock upload test
python mock_upload_test.py --bucket "$BUCKET_NAME" --dir "$IMAGES_DIR" 