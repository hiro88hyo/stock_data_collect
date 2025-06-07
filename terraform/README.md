# Terraform Infrastructure for Stock Data Collector

This directory contains the Terraform configuration for deploying the Japanese stock data collection infrastructure on Google Cloud Platform.

## Architecture

The infrastructure includes:
- **BigQuery**: Dataset and table for storing daily stock prices
- **Cloud Run**: Serverless container service for the data collection application
- **Cloud Scheduler**: Cron job to trigger daily data collection
- **Pub/Sub**: Message queue between Scheduler and Cloud Run
- **IAM**: Service accounts and permissions
- **Secret Manager**: Secure storage for API credentials

## Directory Structure

```
terraform/
├── modules/              # Reusable Terraform modules
│   ├── bigquery/        # BigQuery dataset and table
│   ├── cloud_run/       # Cloud Run service configuration
│   ├── scheduler/       # Cloud Scheduler and Pub/Sub
│   └── iam/            # Service accounts and IAM bindings
├── environments/        # Environment-specific configurations
│   ├── dev/            # Development environment
│   └── prod/           # Production environment
└── scripts/            # Deployment and management scripts
```

## Prerequisites

1. Google Cloud SDK installed and authenticated
2. Terraform 1.0+ installed
3. A GCP project with billing enabled
4. Appropriate permissions to create resources

## Quick Start

### 1. Initialize Development Environment

```bash
cd terraform/scripts
./init.sh dev YOUR_PROJECT_ID your-email@example.com
```

### 2. Deploy Infrastructure

```bash
./deploy.sh dev YOUR_PROJECT_ID your-email@example.com apply
```

### 3. Set J-Quants API Token

```bash
echo -n 'YOUR_REFRESH_TOKEN' | gcloud secrets versions add jquants-refresh-token --data-file=- --project=YOUR_PROJECT_ID
```

### 4. Deploy Application Container

```bash
# Build and push container (from project root)
docker build -t gcr.io/YOUR_PROJECT_ID/stock-data-collector:latest .
docker push gcr.io/YOUR_PROJECT_ID/stock-data-collector:latest

# Update Cloud Run service
cd terraform/scripts
./update-container.sh dev YOUR_PROJECT_ID latest
```

## Environment Configuration

### Development (`dev`)
- Smaller resource allocations (1 CPU, 1GB RAM)
- Separate BigQuery dataset (`stock_data_dev`)
- Environment-specific service names

### Production (`prod`)
- Larger resource allocations (2 CPU, 2GB RAM)
- Production BigQuery dataset (`stock_data`)
- Production service names

## Managing Infrastructure

### View Current State
```bash
cd terraform/environments/dev
terraform show
```

### Update Infrastructure
```bash
cd terraform/scripts
./deploy.sh dev YOUR_PROJECT_ID your-email@example.com plan  # Preview changes
./deploy.sh dev YOUR_PROJECT_ID your-email@example.com apply # Apply changes
```

### Destroy Infrastructure
```bash
./deploy.sh dev YOUR_PROJECT_ID your-email@example.com destroy
```

## Customization

### Modify Schedule
Edit `schedule` in `environments/*/terraform.tfvars`:
```hcl
schedule = "30 16 * * 1-5"  # 16:30 JST on weekdays
```

### Change Resource Limits
Edit resource limits in `environments/*/terraform.tfvars`:
```hcl
cpu_limit    = "2"
memory_limit = "2Gi"
```

### Add Labels
Modify labels in `environments/*/terraform.tfvars`:
```hcl
labels = {
  environment = "dev"
  project     = "stock-data-collector"
  team        = "data-team"
}
```

## Troubleshooting

### State Lock Issues
If Terraform state is locked:
```bash
terraform force-unlock LOCK_ID
```

### API Not Enabled
The init script enables required APIs, but if you encounter API errors:
```bash
gcloud services enable APINAME.googleapis.com --project=YOUR_PROJECT_ID
```

### Permission Issues
Ensure your user account has these roles:
- Project Editor or Owner
- BigQuery Admin
- Cloud Run Admin
- Pub/Sub Admin
- Secret Manager Admin

## Security Notes

1. Never commit `terraform.tfvars` with sensitive data
2. Use Secret Manager for all credentials
3. Follow principle of least privilege for service accounts
4. Regularly rotate API tokens
5. Enable audit logging for production environments