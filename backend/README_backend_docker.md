# How to set up a docker file for schemes backend

## Create .env file
1. Ensure your terminal is inside the backend directory!
2. Ensure dotenv is installed in your local python environment
3. Use the .env.sample as a template to create a .env file
4. Update the values in .env file - these should already be set up when you did the ML Ops > Predict in production

## Docker build
1. Ensure the docker application is running on your computer
2. Run `make build_gcr_image` to build the docker file (this should take a while)

## Set up a new artifact repository in GCP
1. If you already set up the artifact repository before, you can skip this step.
2. Assuming you have completed ML Ops > Predict in production exercise, the below steps should just work
3. Create a new artifact repository in GCP for this project by running `make gcr_new_ar`
4. If it doesnt work, run this commeand directly in terminal
   'gcloud artifacts repositories create $GAR_IMAGE --repository-format=docker --location=$GCP_REGION --description="Repository for storing $GAR_IMAGE images"'

## Push (upload) docker image to GCP artifact repository
1. Ensure the docker image has finished building
2. Run `make push_gcr_image` to push the docker image to GCP

## Run docker image on GCP artifact repository
1. Ensure the docker image has finished uploading
2. Run `make gcr_deploy` to run the docker image on GCP
3. Go to "https://console.cloud.google.com/run" in your browser, click on schemesv2-api
4. In the schemesv2-api page, you should be able to see a URL - this is the URL for your API

ALL DONE!!!
