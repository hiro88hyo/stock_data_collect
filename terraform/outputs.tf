output "cloud_run_service_url" {
  description = "URL of the Cloud Run service"
  value       = module.cloud_run.service_url
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  value       = module.bigquery.dataset_id
}

output "bigquery_table_id" {
  description = "BigQuery table ID"
  value       = module.bigquery.table_id
}

output "cloud_run_service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = module.iam.cloud_run_service_account_email
}

output "pubsub_service_account_email" {
  description = "Email of the Pub/Sub service account"
  value       = module.iam.pubsub_service_account_email
}

output "pubsub_topic_name" {
  description = "Name of the Pub/Sub topic"
  value       = module.scheduler.topic_name
}

output "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  value       = module.scheduler.job_name
}