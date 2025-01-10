# Create Service Account
resource "google_service_account" "vertex_sa" {
  project      = var.project_id
  account_id   = "default-sa"
  display_name = "Service Account for the services"
}

# Grant Roles to Service Account
resource "google_project_iam_member" "grant_sa_function_roles" {
  for_each = toset([
    # Existing roles
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
    "roles/cloudbuild.builds.builder",
    "roles/cloudfunctions.developer",
    "roles/iam.serviceAccountUser",
    "roles/run.developer",
    "roles/artifactregistry.reader",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/logging.logWriter",
    "roles/cloudbuild.serviceAgent",
    "roles/pubsub.publisher",
    "roles/secretmanager.secretAccessor",
    
    # Added Vector Search specific roles
    "roles/aiplatform.user",
    "roles/aiplatform.serviceAgent",
    "roles/datastore.owner"
  ])
  
  role    = each.key
  project = var.project_id
  member  = "serviceAccount:${google_service_account.vertex_sa.email}"
}