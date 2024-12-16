from google.cloud import storage
import os
import argparse

def upload_file_with_metadata(bucket_name, file_path):
    """
    Upload a file to GCP bucket with metadata including the folder name as location
    
    Args:
        bucket_name (str): Name of the GCP bucket
        file_path (str): Path to the file to upload
    """
    try:
        # Initialize the GCP storage client
        storage_client = storage.Client()
        
        # Get the bucket
        bucket = storage_client.bucket(bucket_name)
        
        # Get the folder name from the file path
        folder_name = os.path.basename(os.path.dirname(file_path))
        
        # Get the file name
        file_name = os.path.basename(file_path)
        
        # Create a blob (object) in the bucket
        blob = bucket.blob(file_name)
        
        # Set metadata
        metadata = {'location': folder_name}
        blob.metadata = metadata
        
        # Upload the file
        blob.upload_from_filename(file_path)
        
        print(f"File {file_name} uploaded successfully to {bucket_name}")
        print(f"Metadata set - location: {folder_name}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Upload file to GCP with metadata')
    parser.add_argument('--bucket', required=True, help='GCP bucket name')
    parser.add_argument('--file', required=True, help='Path to file to upload')
    
    args = parser.parse_args()
    
    # Upload the file
    upload_file_with_metadata(args.bucket, args.file)

if __name__ == "__main__":
    main()
