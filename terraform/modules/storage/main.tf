# Enable Firestore API
resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"
  disable_on_destroy = false
}

# Create Firestore Database
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.firestore]
}

# Storage Buckets
resource "google_storage_bucket" "raw_images" {
  name     = "${var.project_id}-raw-images"
  project  = var.project_id
  location = var.region
  uniform_bucket_level_access = true
  force_destroy = true
}

resource "google_storage_bucket" "processed_images" {
  name     = "${var.project_id}-processed-images"
  project  = var.project_id
  location = var.region
  uniform_bucket_level_access = true
  force_destroy = true
}