output "topic_name" {
  description = "Name of the Pub/Sub topic"
  value       = google_pubsub_topic.stock_data_trigger.name
}

output "topic_id" {
  description = "ID of the Pub/Sub topic"
  value       = google_pubsub_topic.stock_data_trigger.id
}

output "subscription_name" {
  description = "Name of the Pub/Sub subscription"
  value       = google_pubsub_subscription.stock_data_processor.name
}

output "job_name" {
  description = "Name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.daily_stock_data.name
}

output "job_id" {
  description = "ID of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.daily_stock_data.id
}