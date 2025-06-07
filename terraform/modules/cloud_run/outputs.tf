output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.stock_data_collector.name
}

output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.stock_data_collector.uri
}

output "service_id" {
  description = "ID of the Cloud Run service"
  value       = google_cloud_run_v2_service.stock_data_collector.id
}