#!/bin/bash
#
# Deploy scheme-processor to Cloud Run
#
# Usage:
#   ./deploy.sh dev    # Deploy to dev project (schemessg-v3-dev)
#   ./deploy.sh prod   # Deploy to prod project (schemessg)

set -e

# Validate environment argument
ENV=$1
if [ "$ENV" != "dev" ] && [ "$ENV" != "prod" ]; then
    echo "Usage: ./deploy.sh [dev|prod]"
    echo ""
    echo "  dev  - Deploy to schemessg-v3-dev"
    echo "  prod - Deploy to schemessg"
    exit 1
fi

# Set project-specific variables
if [ "$ENV" = "prod" ]; then
    PROJECT_ID="schemessg"
    ENV_FILE="../functions/.env.prod"
    # Firebase Admin SDK service account for prod
    FIREBASE_SA="firebase-adminsdk-jt0tt@schemessg.iam.gserviceaccount.com"
else
    PROJECT_ID="schemessg-v3-dev"
    ENV_FILE="../functions/.env"
    # Firebase Admin SDK service account for dev
    FIREBASE_SA="firebase-adminsdk-fehbb@schemessg-v3-dev.iam.gserviceaccount.com"
fi

REGION="asia-southeast1"
SERVICE_NAME="scheme-processor"

echo "============================================"
echo "Deploying scheme-processor to $ENV"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "============================================"

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file not found: $ENV_FILE"
    exit 1
fi

# Set the project
echo "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Read env vars from .env file and format for Cloud Run
echo "Reading environment variables..."
ENV_VARS=""
while IFS='=' read -r key value || [ -n "$key" ]; do
    # Skip comments and empty lines
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue

    # Remove quotes from value if present
    value=$(echo "$value" | sed 's/^"//;s/"$//')

    # Skip if key or value is empty
    [[ -z $key || -z $value ]] && continue

    # Add to env vars string
    if [ -z "$ENV_VARS" ]; then
        ENV_VARS="$key=$value"
    else
        ENV_VARS="$ENV_VARS,$key=$value"
    fi
done < "$ENV_FILE"

# Deploy to Cloud Run from source (auto-builds and creates repo)
echo "Building and deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --port 8081 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 10 \
    --min-instances 0 \
    --max-instances 3 \
    --set-env-vars "$ENV_VARS" \
    --no-allow-unauthenticated

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "============================================"
echo "Deployment complete!"
echo "============================================"
echo "Service URL: $SERVICE_URL"

# Check and setup IAM binding for Firebase Functions to call Cloud Run
echo ""
echo "Checking IAM permissions..."

# Check if the service account already has invoker role
IAM_CHECK=$(gcloud run services get-iam-policy $SERVICE_NAME --region $REGION --format json 2>/dev/null | grep -c "$FIREBASE_SA" || true)

if [ "$IAM_CHECK" = "0" ]; then
    echo "First-time setup: Granting Cloud Run invoker role to Firebase service account..."
    gcloud run services add-iam-policy-binding $SERVICE_NAME \
        --region=$REGION \
        --member="serviceAccount:$FIREBASE_SA" \
        --role="roles/run.invoker" \
        --project=$PROJECT_ID
    echo "IAM binding added successfully."
else
    echo "IAM binding already exists for $FIREBASE_SA"
fi

echo ""
echo "============================================"
echo "Next steps:"
echo "============================================"
echo ""
echo "1. Add PROCESSOR_SERVICE_URL to your .env file:"
if [ "$ENV" = "prod" ]; then
    echo "   Edit: functions/.env.prod"
else
    echo "   Edit: functions/.env"
fi
echo "   Add:  PROCESSOR_SERVICE_URL=$SERVICE_URL"
echo ""
echo "2. Deploy Firebase Functions (if needed):"
echo "   firebase deploy --only functions --project $PROJECT_ID"
echo ""
