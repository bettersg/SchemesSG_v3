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
    ENV_FILE="../functions/.env.dev"
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

    # The content check job reads these from Secret Manager, and Cloud Run rejects a
    # name set both ways.
    case "$key" in AZURE_OPENAI_API_KEY_SEA | SLACK_BOT_TOKEN) continue ;; esac
    JOB_ENV_VARS="${JOB_ENV_VARS:+$JOB_ENV_VARS,}$key=$value"
done < "$ENV_FILE"

# Secret Manager secrets for the job (bettersg/schemessg-infra envs/<env>/secrets.tf).
JOB_SECRETS="AZURE_OPENAI_API_KEY_SEA=AZURE_OPENAI_API_KEY_SEA:latest,SLACK_BOT_TOKEN=SLACK_BOT_TOKEN:latest"

# Deploy to Cloud Run from source (auto-builds and creates repo)
echo "Building and deploying to Cloud Run..."
# One request per instance: each scrape runs a headless browser, and three at once
# exceeded 2Gi and killed the instance (503s). Up to 10 scrapes run in parallel.
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --port 8081 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "$ENV_VARS" \
    --no-allow-unauthenticated

# Get the service URL and image
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
SERVICE_IMAGE=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(spec.template.spec.containers[0].image)')

echo ""
echo "============================================"
echo "Deployment complete!"
echo "============================================"
echo "Service URL: $SERVICE_URL"
echo "Image: $SERVICE_IMAGE"

# Deploy Cloud Run Job for monthly content check (reusing the built container image)
JOB_NAME="scheme-content-check"
echo ""
echo "============================================"
echo "Deploying Cloud Run Job: $JOB_NAME"
echo "============================================"
gcloud run jobs deploy $JOB_NAME \
    --image "$SERVICE_IMAGE" \
    --region $REGION \
    --command "uv" \
    --args "run,python,-m,app.run_content_check" \
    --memory 2Gi \
    --cpu 2 \
    --task-timeout 86400 \
    --max-retries 1 \
    --set-env-vars "$JOB_ENV_VARS" \
    --set-secrets "$JOB_SECRETS"

# Schedule the Cloud Run Job with Cloud Scheduler (0 10 1 * * = 10am SGT on 1st of every month)
SCHEDULER_JOB="scheduled-content-check"
SCHEDULE="0 10 1 * *"
TIMEZONE="Asia/Singapore"

echo ""
echo "============================================"
echo "Configuring Cloud Scheduler: $SCHEDULER_JOB"
echo "============================================"
if gcloud scheduler jobs describe $SCHEDULER_JOB --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    gcloud scheduler jobs update http $SCHEDULER_JOB \
        --location=$REGION \
        --project=$PROJECT_ID \
        --schedule="$SCHEDULE" \
        --time-zone="$TIMEZONE" \
        --uri="https://${REGION}-run.googleapis.com/v2/projects/${PROJECT_ID}/locations/${REGION}/jobs/${JOB_NAME}:run" \
        --http-method=POST \
        --oauth-service-account-email="$FIREBASE_SA"
else
    gcloud scheduler jobs create http $SCHEDULER_JOB \
        --location=$REGION \
        --project=$PROJECT_ID \
        --schedule="$SCHEDULE" \
        --time-zone="$TIMEZONE" \
        --uri="https://${REGION}-run.googleapis.com/v2/projects/${PROJECT_ID}/locations/${REGION}/jobs/${JOB_NAME}:run" \
        --http-method=POST \
        --oauth-service-account-email="$FIREBASE_SA"
fi

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

# Ensure service account has invoker role on the Cloud Run Job (for Cloud Scheduler)
JOB_IAM_CHECK=$(gcloud run jobs get-iam-policy $JOB_NAME --region $REGION --project $PROJECT_ID --format json 2>/dev/null | grep -c "$FIREBASE_SA" || true)
if [ "$JOB_IAM_CHECK" = "0" ]; then
    echo "Granting Cloud Run Job invoker role to service account..."
    gcloud run jobs add-iam-policy-binding $JOB_NAME \
        --region=$REGION \
        --member="serviceAccount:$FIREBASE_SA" \
        --role="roles/run.invoker" \
        --project=$PROJECT_ID
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
