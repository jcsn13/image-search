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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
storage_client = storage.Client()
analyzer = GeminiImageAnalyzer()
embedding_generator = EmbeddingGenerator()
vector_search = VectorSearchClient()
location_service = LocationService()

PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET')

@functions_framework.cloud_event
def process_image(cloud_event: Dict[str, Any]) -> tuple[str, int]:
    """Process uploaded images with Gemini and generate embeddings"""
    try:
        data = cloud_event.data
        bucket_name = data["bucket"]
        file_name = data["name"]
        
        logger.info(f"Processing image: {file_name} from bucket: {bucket_name}")
        
        # Download image
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        local_path = f"/tmp/{file_name}"
        blob.download_to_filename(local_path)
        
        # Analyze with Gemini
        analysis = analyzer.analyze_image(local_path)
        logger.info(f"Generated analysis for {file_name}")
        
        # Generate embedding
        embedding = embedding_generator.generate_embedding(
            image_path=local_path,
            text_context=analysis.to_combined_text()
        )
        logger.info(f"Generated embedding for {file_name}")
        
        # Get location information
        location_info = location_service.extract_location_from_image(local_path)
        
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