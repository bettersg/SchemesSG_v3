##### Prediction API - - - - - - - - - - - - - - - - - - - - - - - - -

run_api:
	uvicorn fast_api.api:app --reload

##### Docker - - - - - - - - - - - - - - - - - - - - - - - - -

docker_build:
	docker build -t schemesv2-api .

docker_run:
	docker run -p 8000:8000 --name api schemesv2-api

##### GCP - - - - - - - - - - - - - - - - - - - - - - - - -

gcr_new_ar:
  gcloud artifacts repositories create $(GAR_IMAGE) --repository-format=docker --location=$(GCP_REGION) --description="Repository for storing $(GAR_IMAGE) images"

build_gcr_image:
	docker build --platform linux/amd64 -t $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(GAR_IMAGE)/$(GAR_IMAGE):prod .

push_gcr_image:
	docker push $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(GAR_IMAGE)/$(GAR_IMAGE):prod

gcr_deploy:
	gcloud run deploy --image $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(GAR_IMAGE)/$(GAR_IMAGE):prod --memory $(GAR_MEMORY) --region $(GCP_REGION)
