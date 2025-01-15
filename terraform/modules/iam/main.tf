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
    "roles/datastore.user",
    
    # Added Vector Search specific roles
    "roles/aiplatform.user",
    "roles/aiplatform.serviceAgent",
    "roles/datastore.owner"
  ])
  
  role    = each.key
  project = var.project_id
  member  = "serviceAccount:${google_service_account.vertex_sa.email}"
}

resource "google_project_service_identity" "service_agents" {
  provider = google-beta
  for_each = toset([
    "storage.googleapis.com",
    "cloudbuild.googleapis.com",
    "eventarc.googleapis.com",
    "compute.googleapis.com"
  ])
  
  project = var.project_id
  service = each.value
}

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
  
  depends_on = [
    google_project_service_identity.service_agents
  ]
}

resource "google_project_iam_member" "compute_eventarc_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${var.project_number}-compute@developer.gserviceaccount.com"
  
  depends_on = [
    google_project_service_identity.service_agents
  ]
}

resource "google_project_iam_member" "storage_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${var.project_number}@gs-project-accounts.iam.gserviceaccount.com"

  depends_on = [ 
    google_project_service_identity.service_agents
  ]
}

resource "google_project_iam_member" "eventarc_agent" {
  project = var.project_id
  role    = "roles/eventarc.serviceAgent"
  member  = "serviceAccount:service-${var.project_number}@gcp-sa-eventarc.iam.gserviceaccount.com"
  
  depends_on = [
    google_project_service_identity.service_agents
  ]
}