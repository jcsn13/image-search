"""
 Copyright 2024 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 """

import functions_framework
from google.cloud import storage
from analyzer import GeminiImageAnalyzer
from embedding import EmbeddingGenerator
from vector_store import VectorSearchClient
import logging
import os
from typing import Dict, Any
from location_service import LocationService
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Force all loggers to INFO level
logging.getLogger('location_service').setLevel(logging.INFO)
logging.getLogger('google.cloud.storage').setLevel(logging.INFO)

# Initialize clients
logger.info("Initializing services...")
storage_client = storage.Client()
analyzer = GeminiImageAnalyzer()
embedding_generator = EmbeddingGenerator()
vector_search = VectorSearchClient()
location_service = LocationService()
logger.info("All services initialized successfully")

PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET')
logger.info(f"Using processed bucket: {PROCESSED_BUCKET}")

@functions_framework.cloud_event
def process_image(cloud_event: Dict[str, Any]) -> tuple[str, int]:
    """Process uploaded images with Gemini and generate embeddings"""
    try:
        logger.info("Starting image processing function")
        logger.info(f"Cloud event: {json.dumps(cloud_event)}")
        
        # Extract data from cloud event
        if not hasattr(cloud_event, 'data'):
            logger.error("No data in cloud event")
            return "No data in cloud event", 400
            
        data = cloud_event.data
        logger.info(f"Event data: {json.dumps(data)}")
        
        bucket_name = data.get("bucket")
        file_name = data.get("name")
        
        if not bucket_name or not file_name:
            logger.error(f"Missing required data - bucket: {bucket_name}, file: {file_name}")
            return "Missing required data", 400
        
        logger.info(f"Processing image: {file_name} from bucket: {bucket_name}")
        
        # Download image
        logger.info("Getting bucket and blob...")
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        # Reload the blob to ensure we have the latest metadata
        blob.reload()
        
        logger.info(f"Blob metadata: {blob.metadata}")
        logger.info(f"Blob: {blob}")
        
        local_path = f"/tmp/{file_name}"
        logger.info(f"Downloading to {local_path}")
        blob.download_to_filename(local_path)
        logger.info("File downloaded successfully")
        
        # Get location from metadata
        logger.info("Extracting location from metadata")
        location_name = None
        if blob.metadata:
            location_name = blob.metadata.get('location')
            logger.info(f"Found location in metadata: {location_name}")
        
        # Try to get location from file path if metadata is missing
        if not location_name:
            logger.info("No location in metadata, trying file path")
            # The file_name format is "Location_Name/filename.jpg", so we extract the location
            location_name = file_name.split('/')[0] if '/' in file_name else None
            logger.info(f"Extracted location name from path: {location_name}")
        
        # Get location details
        location_info = None
        if location_name:
            try:
                logger.info(f"Calling location service with name: {location_name}")
                location_info = location_service.get_location_details(location_name)
                logger.info(f"Retrieved location info: {location_info}")
            except Exception as e:
                logger.error(f"Error getting location details: {str(e)}", exc_info=True)
                # Continue processing even if location lookup fails
        else:
            logger.warning("No location name found in metadata or path")
        
        # Analyze with Gemini
        analysis = analyzer.analyze_image(local_path)
        logger.info(f"Generated analysis for {file_name}")
        
        # Generate embedding
        embedding = embedding_generator.generate_embedding(
            image_path=local_path,
            text_context=analysis.to_combined_text()
        )
        logger.info(f"Generated embedding for {file_name}")
        
        # Store in Vector Search
        metadata = {
            'file_name': file_name,
            'original_bucket': bucket_name,
            'content_type': blob.content_type,
            'size': blob.size,
            'context': analysis.context_description,
            'characteristics': analysis.visual_characteristics,
            'objects': ','.join(analysis.object_annotations),
            'processed_image_path': f"gs://{PROCESSED_BUCKET}/{file_name}",
            'location': location_info if location_info else None
        }
        
        vector_search.upsert_embedding(
            embedding=embedding,
            id=file_name,
            metadata=metadata
        )
        logger.info(f"Stored embedding in Vector Search for {file_name}")
        
        # Move to processed bucket
        processed_bucket = storage_client.bucket(PROCESSED_BUCKET)
        processed_blob = processed_bucket.blob(file_name)
        processed_blob.rewrite(blob)
        blob.delete()
        logger.info(f"Moved {file_name} to processed bucket")
        
        return 'Success', 200
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        return str(e), 500