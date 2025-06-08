#!/bin/bash
# Initialize Terraform environment

set -e

ENVIRONMENT=${1:-dev}
PROJECT_ID=${2}
DATASET_OWNER_EMAIL=${3}

if [ -z "$PROJECT_ID" ] || [ -z "$DATASET_OWNER_EMAIL" ]; then
  echo "Usage: $0 <environment> <project_id> <dataset_owner_email>"
  echo "Example: $0 dev my-project-id user@example.com"
  exit 1
fi

echo "===================="
echo "Initializing Terraform for environment: $ENVIRONMENT"
echo "Project ID: $PROJECT_ID"
echo "Dataset Owner: $DATASET_OWNER_EMAIL"
echo "===================="

# Create state bucket
echo "Creating state bucket..."
gsutil mb -p $PROJECT_ID gs://terraform-state-$PROJECT_ID || echo "State bucket already exists"
gsutil versioning set on gs://terraform-state-$PROJECT_ID

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable --project=$PROJECT_ID \
  cloudresourcemanager.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  bigquery.googleapis.com \
  pubsub.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  containerregistry.googleapis.com \
  logging.googleapis.com \
  iam.googleapis.com

# Initialize Terraform
echo "Initializing Terraform..."
cd ../environments/$ENVIRONMENT
terraform init \
  -backend-config="bucket=terraform-state-$PROJECT_ID"

# Validate configuration
echo "Validating Terraform configuration..."
terraform validate

# Plan with provided variables
echo "Running Terraform plan..."
terraform plan \
  -var="project_id=$PROJECT_ID" \
  -var="dataset_owner_email=$DATASET_OWNER_EMAIL"

echo "===================="
echo "Terraform initialized successfully for $ENVIRONMENT environment"
echo "===================="
echo ""
echo "Next steps:"
echo "1. Review the plan above"
echo "2. Apply the configuration:"
echo "   cd terraform/environments/$ENVIRONMENT"
echo "   terraform apply -var=\"project_id=$PROJECT_ID\" -var=\"dataset_owner_email=$DATASET_OWNER_EMAIL\""
echo ""
echo "After applying, you'll need to:"
echo "1. Set the J-Quants refresh token secret:"
echo "   echo -n 'YOUR_REFRESH_TOKEN' | gcloud secrets versions add jquants-refresh-token --data-file=-"
echo "2. Deploy the Cloud Run service with your container image"