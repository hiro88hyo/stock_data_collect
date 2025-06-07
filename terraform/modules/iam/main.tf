resource "google_service_account" "cloud_run_sa" {
  account_id   = var.cloud_run_sa_id
  display_name = "Cloud Run Service Account for Stock Data Collector"
  description  = "Service account for Cloud Run stock data collector"
}

resource "google_service_account" "pubsub_sa" {
  account_id   = var.pubsub_sa_id
  display_name = "Pub/Sub Service Account"
  description  = "Service account for Pub/Sub to invoke Cloud Run"
}

# BigQuery permissions for Cloud Run service account
resource "google_bigquery_dataset_iam_member" "cloud_run_bigquery_writer" {
  dataset_id = var.bigquery_dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Secret Manager permissions for Cloud Run service account
resource "google_secret_manager_secret_iam_member" "cloud_run_secret_accessor" {
  secret_id = var.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Logging permissions for Cloud Run service account
resource "google_project_iam_member" "cloud_run_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run invoker permission for Pub/Sub service account
resource "google_project_iam_member" "pubsub_cloud_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.pubsub_sa.email}"
}

# Create the secret (empty, will be populated manually)
resource "google_secret_manager_secret" "jquants_refresh_token" {
  secret_id = var.secret_id

  labels = var.labels

  replication {
    auto {}
  }
}