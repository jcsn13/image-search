from google.cloud import storage
import os
import argparse
from pathlib import Path

def upload_file_with_metadata(bucket_name, file_path, location):
    """
    Upload a file to GCP bucket with metadata including the location
    
    Args:
        bucket_name (str): Name of the GCP bucket
        file_path (str): Path to the file to upload
        location (str): Location name to be used as metadata
    """
    try:
        # Initialize the GCP storage client
        storage_client = storage.Client()
        
        # Get the bucket
        bucket = storage_client.bucket(bucket_name)
        
        # Get the file name
        file_name = os.path.basename(file_path)
        
        # Create a blob (object) in the bucket with location prefix
        blob = bucket.blob(f"{location}/{file_name}")
        
        # Set metadata
        metadata = {'location': location}
        blob.metadata = metadata
        
        # Upload the file
        blob.upload_from_filename(file_path)
        
        print(f"File {file_name} uploaded successfully to {bucket_name}/{location}")
        print(f"Metadata set - location: {location}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def process_location_directory(bucket_name, base_dir):
    """
    Process all images in the location_images directory
    
    Args:
        bucket_name (str): Name of the GCP bucket
        base_dir (str): Path to the base directory containing location subfolders
    """
    base_path = Path(base_dir)
    
    # Skip if base directory doesn't exist
    if not base_path.exists():
        print(f"Directory {base_dir} does not exist")
        return
    
    # Process each location subfolder
    for location_dir in base_path.iterdir():
        if location_dir.is_dir() and not location_dir.name.startswith('.'):
            location_name = location_dir.name
            print(f"\nProcessing location: {location_name}")
            
            # Process each image in the location directory
            for image_file in location_dir.glob('*'):
                if image_file.is_file() and not image_file.name.startswith('.'):
                    print(f"Processing file: {image_file.name}")
                    upload_file_with_metadata(bucket_name, str(image_file), location_name)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Upload files to GCP with location metadata')
    parser.add_argument('--bucket', required=True, help='GCP bucket name')
    parser.add_argument('--dir', required=True, help='Path to location_images directory')
    
    args = parser.parse_args()
    
    # Process the directory
    process_location_directory(args.bucket, args.dir)

if __name__ == "__main__":
    main()
