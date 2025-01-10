# Cloud Storage Bucket
resource "google_storage_bucket" "temp_images" {
  name          = "${var.project_id}-temp-images"
  location      = var.region
  force_destroy = true # Optional, use with caution in production
}

# Cloud Run Service with VPC Access and Environment Variables
resource "google_cloud_run_v2_service" "search_api_app" {
  name        = "image-search-api"
  location    = var.region
  description = "Streamlit app to"

  template {
    service_account = var.service_account

    containers {
      image = var.image_name

      resources {
        limits = {
          cpu = "2"
          memory = "2Gi"
        }
      }

      # Set environment variables
      env {
        name  = "BUCKET_NAME"
        value = google_storage_bucket.temp_images.name
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "REGION"
        value = var.region
      }
      env {
        name  = "VECTOR_SEARCH_INDEX"
        value = var.vector_search_index_id
      }
      env {
        name  = "DEPLOYED_INDEX_ID"
        value = var.deployed_index_id
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# IAM Policy for Cloud Run Service Account to Access the Bucket
resource "google_storage_bucket_iam_member" "run_service_account_object_admin" {
  bucket = google_storage_bucket.temp_images.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_cloud_run_v2_service.search_api_app.template[0].service_account}"
}

# IAM Policy for All Organization Users
resource "google_cloud_run_service_iam_policy" "all_users" {
  project     = var.project_id
  location    = var.region
  service     = google_cloud_run_v2_service.search_api_app.name

  policy_data = jsonencode({
    bindings = [
      {
        role = "roles/run.invoker"
        members = [
          "allUsers"
        ]
      }
    ]
  })
}