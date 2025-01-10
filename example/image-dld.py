import os
import requests
import json
from pathlib import Path
import time
from typing import List, Dict
import re
from PIL import Image
import io
import math

class WikipediaImageDownloader:
    def __init__(self):
        """
        Initialize the downloader with Wikipedia API endpoint
        """
        self.api_endpoint = "https://en.wikipedia.org/w/api.php"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_page_images(self, title: str, num_images: int = 3) -> List[str]:
        """
        Get images from a Wikipedia page using the API
        """
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "images",
            "imlimit": "50"  # Request more images than needed to filter out non-relevant ones
        }

        try:
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract page ID
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return []

            page_id = list(pages.keys())[0]
            images = pages[page_id].get("images", [])

            # Filter out non-image files and get image titles
            image_titles = [
                img["title"] for img in images 
                if any(ext in img["title"].lower() for ext in [".jpg", ".jpeg", ".png"]) 
                and not any(skip in img["title"].lower() for skip in ["logo", "icon", "map", "symbol", "flag"])
            ]

            # Now get the actual URLs for these images
            image_urls = []
            for title in image_titles[:num_images]:
                img_url = self.get_image_url(title)
                if img_url:
                    image_urls.append(img_url)

            return image_urls[:num_images]

        except Exception as e:
            print(f"Error getting images for {title}: {str(e)}")
            return []

    def get_image_url(self, image_title: str) -> str:
        """
        Get the actual URL for an image using its title
        """
        params = {
            "action": "query",
            "format": "json",
            "titles": image_title,
            "prop": "imageinfo",
            "iiprop": "url"
        }

        try:
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return ""

            page_id = list(pages.keys())[0]
            image_info = pages[page_id].get("imageinfo", [])
            
            if image_info:
                return image_info[0].get("url", "")

        except Exception as e:
            print(f"Error getting image URL for {image_title}: {str(e)}")
        
        return ""

    def resize_image_to_max_size(self, img: Image.Image, max_size_mb: float = 5.0) -> Image.Image:
        """
        Resize an image to ensure its file size is under the specified maximum size in MB
        """
        # Convert max size to bytes
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Save to a temporary buffer to check size
        temp_buffer = io.BytesIO()
        img.save(temp_buffer, format='JPEG', quality=95)
        current_size = temp_buffer.tell()
        
        # If size is already OK, return original
        if current_size <= max_size_bytes:
            return img
        
        # Calculate scaling factor based on size ratio
        scale_factor = math.sqrt(max_size_bytes / current_size)
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)
        
        # Resize image
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Fine-tune quality if still too large
        quality = 95
        while quality > 50:
            temp_buffer = io.BytesIO()
            resized_img.save(temp_buffer, format='JPEG', quality=quality)
            if temp_buffer.tell() <= max_size_bytes:
                break
            quality -= 5
        
        return resized_img

    def download_image(self, url: str, filepath: Path, max_size_mb: float = 5.0) -> bool:
        """
        Download an image from URL, resize if necessary, and save it to the specified path
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            # Ensure the directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Load image into PIL
            img = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary (handles PNG with transparency)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
            
            # Resize if needed
            img = self.resize_image_to_max_size(img, max_size_mb)
            
            # Save the image
            img.save(filepath, 'JPEG', quality=95)
            return True

        except Exception as e:
            print(f"Error downloading/processing {url}: {str(e)}")
            return False

    def create_location_folders(self, base_path: str, locations: Dict[str, str], images_per_location: int = 3) -> None:
        """
        Create folders for each location and download images into them
        """
        base_path = Path(base_path)
        base_path.mkdir(exist_ok=True)

        for folder_name, wiki_title in locations.items():
            print(f"\nProcessing location: {folder_name}")
            location_path = base_path / folder_name
            
            # Get images for the location
            image_urls = self.get_page_images(wiki_title, images_per_location)
            
            successful_downloads = 0
            for idx, image_url in enumerate(image_urls):
                if image_url:
                    # Create filename with location and index
                    file_extension = image_url.split('.')[-1]
                    if len(file_extension) > 4:  # Handle cases where URL has parameters
                        file_extension = 'jpg'
                    filename = f"{folder_name}_{idx + 1}.{file_extension}"
                    filepath = location_path / filename
                    
                    print(f"Downloading image {idx + 1} for {folder_name}...")
                    if self.download_image(image_url, filepath):
                        successful_downloads += 1
                    
                    # Add a small delay between downloads
                    time.sleep(1)
            
            print(f"Successfully downloaded {successful_downloads} images for {folder_name}")

def main():
    # Dictionary mapping folder names to Wikipedia page titles
    locations = {
        "Eiffel_Tower": "Eiffel_Tower",
        "Statue_of_Liberty": "Statue_of_Liberty",
        "Sensoji_Temple": "Sensō-ji",
        "Tower_Bridge": "Tower_Bridge",
        "Sydney_Opera_House": "Sydney_Opera_House",
        "Colosseum": "Colosseum",
        "Sagrada_Familia": "Sagrada_Família",
        "Burj_Khalifa": "Burj_Khalifa",
        "Marina_Bay_Sands": "Marina_Bay_Sands",
        "Stanley_Park": "Stanley_Park",
        "Taj_Mahal": "Taj_Mahal",
        "Petra_Treasury": "Al-Khazneh",
        "Christ_the_Redeemer": "Christ_the_Redeemer_(statue)",
        "Acropolis_Athens": "Acropolis_of_Athens",
        "Forbidden_City": "Forbidden_City"
    }
    
    # Initialize downloader
    downloader = WikipediaImageDownloader()
    
    # Set up base directory for images
    base_directory = "location_images"
    
    try:
        # Create folders and download images
        downloader.create_location_folders(base_directory, locations, images_per_location=3)
        print("\nDownload completed successfully!")
        
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()