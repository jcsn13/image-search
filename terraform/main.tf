# terraform/main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.10.0"
    }
  }
}

provider "google" {
  project               = var.project_id
  region                = var.region
  zone                  = "${var.region}-a"
  user_project_override = true
}

# Enable APIs
resource "google_project_service" "resource_manager" {
  project                    = var.project_id
  service                    = "cloudresourcemanager.googleapis.com"
  disable_dependent_services = true
}

resource "time_sleep" "wait_for_resource_manager" {
  create_duration = "30s"

  depends_on = [
    google_project_service.resource_manager
  ]
}

module "policies" {
  source     = "./modules/policy"
  project_id = var.project_id

  depends_on = [
    time_sleep.wait_for_resource_manager
  ]
}

resource "time_sleep" "wait_for_policies" {
  create_duration = "30s"

  depends_on = [
    module.policies
  ]
}

resource "google_project_service" "required_apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "containerregistry.googleapis.com",
    "servicenetworking.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "vpcaccess.googleapis.com",
    "eventarc.googleapis.com",
    "maps-backend.googleapis.com",
    "maps-embed-backend.googleapis.com",
    "places-backend.googleapis.com",
    "geocoding-backend.googleapis.com",
    "secretmanager.googleapis.com",
    "apikeys.googleapis.com"
  ])

  project                    = var.project_id
  service                    = each.key
  disable_dependent_services = true

  depends_on = [
    time_sleep.wait_for_policies
  ]
}

module "iam" {
  source         = "./modules/iam"
  project_id     = var.project_id
  project_number = var.project_number
  region         = var.region

  depends_on = [
    time_sleep.wait_for_resource_manager,
    google_project_service.required_apis,
    time_sleep.wait_for_policies

  ]
}

# Create API key
resource "google_apikeys_key" "maps_api_key" {
  name         = "maps-api-key"
  display_name = "Google Maps API Key"
  project      = var.project_id

  restrictions {
    api_targets {
      service = "maps-backend.googleapis.com"
    }
    api_targets {
      service = "maps-embed-backend.googleapis.com"
    }
    api_targets {
      service = "places-backend.googleapis.com"
    }
    api_targets {
      service = "geocoding-backend.googleapis.com"
    }
  }

  depends_on = [
    google_project_service.required_apis,
    time_sleep.wait_for_resource_manager
  ]
}

# Create secret container
resource "google_secret_manager_secret" "maps_api_key" {
  secret_id = "maps-api-key"
  project   = var.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [
    google_project_service.required_apis,
    time_sleep.wait_for_resource_manager,
    google_apikeys_key.maps_api_key
  ]
}

# Create secret version with API key
resource "google_secret_manager_secret_version" "maps_api_key" {
  secret      = google_secret_manager_secret.maps_api_key.id
  secret_data = google_apikeys_key.maps_api_key.key_string

  depends_on = [
    google_secret_manager_secret.maps_api_key,
    google_apikeys_key.maps_api_key
  ]
}

# Grant access to the Cloud Function service account
resource "google_secret_manager_secret_iam_member" "maps_api_key_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.maps_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.iam.service_account_email}"

  depends_on = [
    google_secret_manager_secret.maps_api_key,
    google_secret_manager_secret_version.maps_api_key,
    module.iam
  ]
}

module "storage" {
  source     = "./modules/storage"
  project_id = var.project_id
  region     = var.region

  depends_on = [
    time_sleep.wait_for_policies,
    module.iam
  ]
}

module "vector_search" {
  source                = "./modules/vector_search"
  project_id            = var.project_id
  project_number        = var.project_number
  region                = var.region
  index_name            = "image-search-index"
  dimensions            = 1408
  service_account_email = module.iam.service_account_email

  depends_on = [
    module.storage
  ]
}

module "functions" {
  source                 = "./modules/functions"
  project_id             = var.project_id
  region                 = var.region
  project_number         = var.project_number  
  raw_bucket_name        = module.storage.raw_bucket_name
  processed_bucket_name  = module.storage.processed_bucket_name
  vector_search_index_id = module.vector_search.index_id
  service_account_email  = module.iam.service_account_email
  maps_api_key_secret_id = google_secret_manager_secret.maps_api_key.secret_id

  depends_on = [
    module.vector_search,
    google_secret_manager_secret.maps_api_key,
    google_secret_manager_secret_version.maps_api_key,
    google_secret_manager_secret_iam_member.maps_api_key_access
  ]
}

# module "api_service" {
#   source = "./modules/api_service"
#   project_id = var.project_id
#   region     = var.region
# #   vector_search_index_id = module.vector_search.index_id
# }
