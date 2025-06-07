output "cloud_run_service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cloud_run_sa.email
}

output "cloud_run_service_account_id" {
  description = "ID of the Cloud Run service account"
  value       = google_service_account.cloud_run_sa.id
}

output "pubsub_service_account_email" {
  description = "Email of the Pub/Sub service account"
  value       = google_service_account.pubsub_sa.email
}

output "pubsub_service_account_id" {
  description = "ID of the Pub/Sub service account"
  value       = google_service_account.pubsub_sa.id
}

output "secret_id" {
  description = "ID of the J-Quants refresh token secret"
  value       = google_secret_manager_secret.jquants_refresh_token.secret_id
}