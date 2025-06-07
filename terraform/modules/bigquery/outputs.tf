output "dataset_id" {
  description = "ID of the BigQuery dataset"
  value       = google_bigquery_dataset.stock_data.dataset_id
}

output "table_id" {
  description = "ID of the BigQuery table"
  value       = google_bigquery_table.daily_stock_prices.table_id
}

output "table_full_id" {
  description = "Full ID of the BigQuery table"
  value       = "${google_bigquery_dataset.stock_data.project}.${google_bigquery_dataset.stock_data.dataset_id}.${google_bigquery_table.daily_stock_prices.table_id}"
}