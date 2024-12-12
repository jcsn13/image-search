# Create Service Account
resource "google_service_account" "vertex_sa" {
  project = var.project_id
  account_id   = "default-sa"
  display_name = "Service Account for the services"
}

# Grant Roles to Service Accounts
resource "google_project_iam_member" "grant_sa_function_roles" {
  for_each = toset([
    "roles/bigquery.user", 
    "roles/storage.objectAdmin", 
    "roles/run.invoker",
    "roles/eventarc.eventReceiver",
    "roles/eventarc.serviceAgent",
    "roles/container.admin",
    "roles/resourcemanager.projectIamAdmin",
    "roles/compute.osLogin",
    "roles/vpcaccess.user",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/cloudbuild.builds.builder",
    "roles/cloudfunctions.developer",
    # Added roles for Cloud Build and Functions
    "roles/iam.serviceAccountUser",
    "roles/run.developer",
    "roles/artifactregistry.reader",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/logging.logWriter",
    "roles/cloudbuild.serviceAgent",
    "roles/pubsub.publisher"  # For eventarc triggers
  ])

  role    = each.key
  project = var.project_id
  member  = "serviceAccount:${google_service_account.vertex_sa.email}"
}

# Add permissions for the default Cloud Build service account
resource "google_project_iam_member" "cloudbuild_sa_permissions" {
  for_each = toset([
    "roles/cloudbuild.builds.builder",
    "roles/cloudbuild.serviceAgent",
    "roles/iam.serviceAccountUser",
    "roles/cloudfunctions.developer",
    "roles/run.developer"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${var.project_number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "functions_permissions" {
  for_each = toset([
    "roles/cloudfunctions.serviceAgent",
    "roles/iam.serviceAccountUser",
    "roles/run.serviceAgent",
    "roles/pubsub.publisher"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:service-${var.project_number}@gcf-admin-robot.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "eventarc_service_agent" {
  for_each = toset([
    "roles/eventarc.serviceAgent",
    "roles/pubsub.publisher"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:service-${var.project_number}@gcp-sa-eventarc.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "gcs_pubsub_publishing" {
  project = "image-search-442921"
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${var.project_number}@gs-project-accounts.iam.gserviceaccount.com"
}