# Cloud Storage bucket for function source code
resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-function-source"
  location = var.region
  uniform_bucket_level_access = true
}

data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../src/image_processor"
  output_path = "${path.module}/tmp/function.zip"
}

# Upload the function source code to GCS
resource "google_storage_bucket_object" "function_source" {
  name   = "function-source-${data.archive_file.function_zip.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.function_zip.output_path
}

# Create a default Cloud Build worker pool
resource "google_cloudbuild_worker_pool" "default_pool" {
  name     = "default-pool"
  location = var.region
  project  = var.project_id

  worker_config {
    disk_size_gb = 100
    machine_type = "e2-medium"
    no_external_ip = false
  }
}

# Cloud Function
resource "google_cloudfunctions2_function" "image_processor" {
  name        = "image-processor"
  location    = var.region
  description = "Function to process images using Gemini and generate embeddings"

  build_config {
    runtime     = "python311"
    entry_point = "process_image"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket.name
        object = google_storage_bucket_object.function_source.name
      }
    }
    worker_pool = google_cloudbuild_worker_pool.default_pool.id
  }

  service_config {
    max_instance_count = var.max_instances
    min_instance_count = var.min_instances
    available_memory   = var.memory
    timeout_seconds    = var.timeout_seconds
    
    service_account_email = var.service_account_email
    
    environment_variables = {
      PROJECT_ID           = var.project_id
      REGION               = var.region
      PROCESSED_BUCKET     = var.processed_bucket_name
      VECTOR_SEARCH_INDEX  = var.vector_search_index_id
    }

    secret_environment_variables {
      key        = "GOOGLE_MAPS_API_KEY"
      project_id = var.project_id
      secret     = var.maps_api_key_secret_id
      version    = "latest"
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.storage.object.v1.finalized"
    retry_policy   = "RETRY_POLICY_RETRY"
    service_account_email = var.service_account_email
    
    event_filters {
      attribute = "bucket"
      value     = var.raw_bucket_name
    }
  }

  depends_on = [
    google_cloudbuild_worker_pool.default_pool
  ]  
}