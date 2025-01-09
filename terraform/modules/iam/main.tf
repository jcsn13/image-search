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
    "roles/pubsub.publisher",  # For eventarc triggers
    "roles/secretmanager.secretAccessor"
  ])

  role    = each.key
  project = var.project_id
  member  = "serviceAccount:${google_service_account.vertex_sa.email}"
}