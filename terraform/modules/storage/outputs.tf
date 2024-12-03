output "raw_bucket_name" {
  value = google_storage_bucket.raw_images.name
}

output "processed_bucket_name" {
  value = google_storage_bucket.processed_images.name
}