from pathlib import Path
import json
from datetime import datetime
import os

class MockStorageClient:
    def __init__(self):
        self.uploaded_files = []
    
    def upload_file(self, bucket_name, file_path, location):
        """Mock upload and store the information"""
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        upload_info = {
            "file_name": file_name,
            "bucket_path": f"{location}/{file_name}",
            "location_metadata": location,
            "size_bytes": file_size,
            "upload_timestamp": datetime.now().isoformat(),
            "bucket": bucket_name
        }
        
        self.uploaded_files.append(upload_info)
        return upload_info

def mock_upload_process(bucket_name, base_dir):
    """
    Mock the upload process and generate a report
    
    Args:
        bucket_name (str): Name of the GCP bucket
        base_dir (str): Path to the base directory containing location subfolders
    """
    base_path = Path(base_dir)
    mock_client = MockStorageClient()
    
    # Statistics for the report
    stats = {
        "total_files": 0,
        "total_size_bytes": 0,
        "locations_processed": 0,
        "files_by_location": {},
        "start_time": datetime.now().isoformat(),
        "bucket_name": bucket_name
    }
    
    if not base_path.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return
    
    print(f"\n🚀 Starting mock upload process for {bucket_name}")
    print(f"📁 Processing directory: {base_dir}\n")
    
    # Process each location subfolder
    for location_dir in base_path.iterdir():
        if location_dir.is_dir() and not location_dir.name.startswith('.'):
            location_name = location_dir.name
            location_files = []
            print(f"📍 Processing location: {location_name}")
            
            # Process each image in the location directory
            for image_file in location_dir.glob('*'):
                if image_file.is_file() and not image_file.name.startswith('.'):
                    upload_info = mock_client.upload_file(bucket_name, str(image_file), location_name)
                    location_files.append(upload_info)
                    
                    stats["total_files"] += 1
                    stats["total_size_bytes"] += upload_info["size_bytes"]
                    print(f"  ↳ 📸 Would upload: {image_file.name} → {upload_info['bucket_path']}")
            
            if location_files:
                stats["locations_processed"] += 1
                stats["files_by_location"][location_name] = {
                    "file_count": len(location_files),
                    "total_size_bytes": sum(f["size_bytes"] for f in location_files)
                }
    
    stats["end_time"] = datetime.now().isoformat()
    
    # Generate the report
    generate_report(stats, mock_client.uploaded_files)

def generate_report(stats, uploaded_files):
    """Generate a detailed report of the mock upload process"""
    
    print("\n📊 MOCK UPLOAD REPORT")
    print("=" * 50)
    print(f"🪣  Target Bucket: {stats['bucket_name']}")
    print(f"⏱  Start Time: {stats['start_time']}")
    print(f"⏱  End Time: {stats['end_time']}")
    print(f"📁 Total Files Processed: {stats['total_files']}")
    print(f"📍 Total Locations: {stats['locations_processed']}")
    print(f"💾 Total Size: {stats['total_size_bytes'] / 1024 / 1024:.2f} MB")
    
    print("\n📍 Files by Location:")
    print("-" * 50)
    for location, data in stats["files_by_location"].items():
        print(f"\n{location}:")
        print(f"  Files: {data['file_count']}")
        print(f"  Size: {data['total_size_bytes'] / 1024 / 1024:.2f} MB")
    
    # Save detailed report to JSON
    report = {
        "summary": stats,
        "detailed_uploads": uploaded_files
    }
    
    report_file = "mock_upload_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Mock test for image upload process')
    parser.add_argument('--bucket', required=True, help='GCP bucket name')
    parser.add_argument('--dir', required=True, help='Path to location_images directory')
    
    args = parser.parse_args()
    
    mock_upload_process(args.bucket, args.dir) 