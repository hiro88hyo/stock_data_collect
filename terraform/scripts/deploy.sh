#!/bin/bash
# Deploy or manage Terraform infrastructure

set -e

ENVIRONMENT=${1:-dev}
PROJECT_ID=${2}
DATASET_OWNER_EMAIL=${3}
ACTION=${4:-plan}

if [ -z "$PROJECT_ID" ] || [ -z "$DATASET_OWNER_EMAIL" ]; then
  echo "Usage: $0 <environment> <project_id> <dataset_owner_email> [plan|apply|destroy]"
  echo "Example: $0 dev my-project-id user@example.com apply"
  exit 1
fi

echo "===================="
echo "Environment: $ENVIRONMENT"
echo "Project ID: $PROJECT_ID"
echo "Dataset Owner: $DATASET_OWNER_EMAIL"
echo "Action: $ACTION"
echo "===================="

cd ../environments/$ENVIRONMENT

# Ensure terraform is initialized
if [ ! -d ".terraform" ]; then
  echo "Terraform not initialized. Running init first..."
  terraform init -backend-config="bucket=terraform-state-$PROJECT_ID"
fi

# Execute the requested action
case $ACTION in
  plan)
    echo "Running Terraform plan..."
    terraform plan \
      -var="project_id=$PROJECT_ID" \
      -var="dataset_owner_email=$DATASET_OWNER_EMAIL"
    ;;
  apply)
    echo "Running Terraform apply..."
    terraform apply \
      -var="project_id=$PROJECT_ID" \
      -var="dataset_owner_email=$DATASET_OWNER_EMAIL" \
      -auto-approve
    
    echo ""
    echo "===================="
    echo "Deployment completed successfully!"
    echo "===================="
    echo ""
    echo "Next steps:"
    echo "1. Set the J-Quants refresh token secret (if not already set):"
    echo "   echo -n 'YOUR_REFRESH_TOKEN' | gcloud secrets versions add jquants-refresh-token --data-file=- --project=$PROJECT_ID"
    echo ""
    echo "2. Build and deploy the container image:"
    echo "   docker build -t gcr.io/$PROJECT_ID/stock-data-collector:latest ."
    echo "   docker push gcr.io/$PROJECT_ID/stock-data-collector:latest"
    echo ""
    echo "3. Update Cloud Run with the new image:"
    echo "   gcloud run deploy stock-data-collector-$ENVIRONMENT --image gcr.io/$PROJECT_ID/stock-data-collector:latest --region asia-northeast1 --project=$PROJECT_ID"
    ;;
  destroy)
    echo "WARNING: This will destroy all resources in the $ENVIRONMENT environment!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      terraform destroy \
        -var="project_id=$PROJECT_ID" \
        -var="dataset_owner_email=$DATASET_OWNER_EMAIL" \
        -auto-approve
    else
      echo "Destroy cancelled."
    fi
    ;;
  output)
    echo "Terraform outputs:"
    terraform output
    ;;
  *)
    echo "Invalid action: $ACTION. Use plan, apply, destroy, or output."
    exit 1
    ;;
esac