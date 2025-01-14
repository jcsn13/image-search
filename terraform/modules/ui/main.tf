# Cloud Run Service with VPC Access and Environment Variables
resource "google_cloud_run_v2_service" "search_ui_app" {
  name        = "image-search-ui"
  location    = var.region
  description = "Streamlit app to"

  template {
    service_account = var.service_account

    containers {
      image = var.image_name

      resources {
        limits = {
          cpu = "2"
          memory = "4Gi"
        }
      }

      ports {
        container_port = 8501
      }

      # Set environment variables
      env {
        name  = "API_ENDPOINT"
        value = var.api_endpoint
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# IAM Policy for All Organization Users
resource "google_cloud_run_service_iam_policy" "all_users" {
  project     = var.project_id
  location    = var.region
  service     = google_cloud_run_v2_service.search_ui_app.name

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