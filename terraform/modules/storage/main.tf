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