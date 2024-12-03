import functions_framework
from google.cloud import storage
from analyzer import GeminiImageAnalyzer
from embeddings import EmbeddingGenerator
from vector_store import VectorSearchClient
import logging
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
storage_client = storage.Client()
analyzer = GeminiImageAnalyzer()
embedding_generator = EmbeddingGenerator()
vector_search = VectorSearchClient()

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
        
        # Store in Vector Search
        metadata = {
            'file_name': file_name,
            'original_bucket': bucket_name,
            'content_type': blob.content_type,
            'size': blob.size,
            'context': analysis.context_description,
            'characteristics': analysis.visual_characteristics,
            'objects': ','.join(analysis.object_annotations),
            'processed_image_path': f"gs://{PROCESSED_BUCKET}/{file_name}"
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