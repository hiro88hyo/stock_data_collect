module "stock_data_collector" {
  source = "../../"

  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  dataset_owner_email = var.dataset_owner_email

  # BigQuery
  bigquery_dataset_id = var.bigquery_dataset_id
  bigquery_table_id   = var.bigquery_table_id
  bigquery_location   = var.bigquery_location

  # Cloud Run
  cloud_run_service_name = var.cloud_run_service_name
  container_image        = var.container_image
  cpu_limit              = var.cpu_limit
  memory_limit           = var.memory_limit
  timeout_seconds        = var.timeout_seconds
  log_level              = var.log_level

  # Pub/Sub
  pubsub_topic_name        = var.pubsub_topic_name
  pubsub_subscription_name = var.pubsub_subscription_name

  # Cloud Scheduler
  scheduler_job_name = var.scheduler_job_name
  schedule           = var.schedule

  # Secret Manager
  jquants_secret_id = var.jquants_secret_id

  # Labels
  labels = var.labels
}