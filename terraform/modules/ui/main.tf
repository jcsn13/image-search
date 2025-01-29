# Enable Secret Manager API
resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Create service account key
resource "google_service_account_key" "sa_key" {
  service_account_id = var.service_account
}

# Create secret for service account key
resource "google_secret_manager_secret" "sa_key_secret" {
  secret_id = "service-account-key"
  
  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

# Add the key to the secret
resource "google_secret_manager_secret_version" "sa_key_version" {
  secret = google_secret_manager_secret.sa_key_secret.id
  secret_data = base64decode(google_service_account_key.sa_key.private_key)
}

# Grant service account access to secret
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.sa_key_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account}"
}

# Cloud Run Service with VPC Access and Environment Variables
resource "google_cloud_run_v2_service" "search_ui_app" {
  name        = "image-search-ui"
  location    = var.region
  description = "Streamlit app for image search"

  template {
    service_account = var.service_account

    containers {
      image = var.image_name

      resources {
        limits = {
          cpu    = "2"
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

      # Mount the service account key secret
      volume_mounts {
        name       = "sa-key"
        mount_path = "/app/secrets"
      }
    }

    volumes {
      name = "sa-key"
      secret {
        secret = google_secret_manager_secret.sa_key_secret.secret_id
        items {
          version = "latest"
          path    = "key.json"
        }
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [google_secret_manager_secret_version.sa_key_version]
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