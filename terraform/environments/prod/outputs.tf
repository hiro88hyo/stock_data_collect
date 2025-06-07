output "cloud_run_service_url" {
  description = "URL of the Cloud Run service"
  value       = module.stock_data_collector.cloud_run_service_url
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  value       = module.stock_data_collector.bigquery_dataset_id
}

output "bigquery_table_id" {
  description = "BigQuery table ID"
  value       = module.stock_data_collector.bigquery_table_id
}

output "cloud_run_service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = module.stock_data_collector.cloud_run_service_account_email
}

output "pubsub_service_account_email" {
  description = "Email of the Pub/Sub service account"
  value       = module.stock_data_collector.pubsub_service_account_email
}