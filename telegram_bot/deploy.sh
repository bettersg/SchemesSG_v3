#!/bin/bash

# Set variables
PROJECT_ID="schemessg-v3-dev"
APP_NAME="SchemesSG_v3-telegram-bot"
REGION="asia-southeast1"
ENV_VARS_FILE="env_vars.yaml"  # YAML file to store environment variables

# Define environment variables
declare -A ENV_VARS=(
    ["API_KEY"]=""
    ["BACKEND_URL"]=""
)

# Function to create the environment variables YAML file
create_env_vars_file() {
    echo "Creating environment variables file: $ENV_VARS_FILE..."
    echo "env_variables:" > $ENV_VARS_FILE
    for key in "${!ENV_VARS[@]}"; do
        echo "  $key: \"${ENV_VARS[$key]}\"" >> $ENV_VARS_FILE
    done
    echo "Environment variables file created successfully."
}

# Step 1: Authenticate with Google Cloud
echo "Authenticating with Google Cloud..."
gcloud auth login
gcloud config set project $PROJECT_ID

# Step 2: Set the region for the App Engine application
echo "Setting up region..."
gcloud app create --region=$REGION

# Step 3: Create the environment variables YAML file
create_env_vars_file

# Step 4: Install dependencies (if not done already)
echo "Installing dependencies..."
pip install -r requirements.txt

# Step 5: Deploy the application with environment variables
echo "Deploying to Google Cloud App Engine with environment variables..."
gcloud app deploy --quiet --project=$PROJECT_ID --version=$APP_NAME --env-vars-file=$ENV_VARS_FILE

# Step 6: Wait for deployment to complete
echo "Deployment in progress... Please wait."
gcloud app browse

# Step 7: Monitor deployment status
echo "Monitoring deployment status..."
gcloud app browse

echo "Deployment completed successfully!"
