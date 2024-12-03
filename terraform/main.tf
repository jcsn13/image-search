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
  project = var.project_id
  region  = var.region
  zone    = "${var.region}-a"
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
    "eventarc.googleapis.com"
  ])

  project                    = var.project_id
  service                    = each.key
  disable_dependent_services = true

  depends_on = [
    google_project_service.resource_manager,
    time_sleep.wait_for_resource_manager
  ]
}

module "policies" {
  source     = "./modules/policy"
  project_id = var.project_id

  depends_on = [
    time_sleep.wait_for_resource_manager
  ]
}

module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id
  project_number = var.project_number
  region     = var.region

  depends_on = [
    time_sleep.wait_for_resource_manager
  ]
}

resource "time_sleep" "wait_for_policies" {
  create_duration = "30s"

  depends_on = [
    module.policies,
    google_project_service.required_apis
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
  source         = "./modules/vector_search"
  project_id     = var.project_id
  project_number = var.project_number
  region         = var.region
  index_name     = "image-search-index"
  dimensions     = 1408
  service_account_email = module.iam.service_account_email

  depends_on = [
    module.storage
  ]
}

module "functions" {
  source = "./modules/functions"
  project_id = var.project_id
  region     = var.region
  raw_bucket_name = module.storage.raw_bucket_name
  processed_bucket_name = module.storage.processed_bucket_name
  vector_search_index_id = module.vector_search.index_endpoint_id
  service_account_email = module.iam.service_account_email

  depends_on = [
    module.vector_search
  ]
}

# module "api_service" {
#   source = "./modules/api_service"
#   project_id = var.project_id
#   region     = var.region
# #   vector_search_index_id = module.vector_search.index_id
# }
