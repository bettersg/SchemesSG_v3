##### Front end - - - - - - - - - - - - - - - - - - - - - - - - -

run_app_locally:
	streamlit run app.py

##### Docker - - - - - - - - - - - - - - - - - - - - - - - - -

docker_build_dev:
	docker build --tag=$(GAR_IMAGE):dev .

docker_run_dev:
	docker run -it -e PORT=8080 -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/FILE_NAME.json \
	-v $(GOOGLE_APPLICATION_CREDENTIALS):/tmp/keys/FILE_NAME.json:ro -p 8080:8080 --env-file .env $(GAR_IMAGE):dev

docker_run_dev_noenv:
	docker run -it -e PORT=8080 -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/FILE_NAME.json \
	-v $(GOOGLE_APPLICATION_CREDENTIALS):/tmp/keys/FILE_NAME.json:ro -p 8080:8080 $(GAR_IMAGE):dev

docker_run_dev_sh:
	docker run -it --entrypoint sh -e PORT=8501 -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/FILE_NAME.json \
	-v $(GOOGLE_APPLICATION_CREDENTIALS):/tmp/keys/FILE_NAME.json:ro \
	-p 8080:8080 $(GAR_IMAGE):dev

##### GCP - - - - - - - - - - - - - - - - - - - - - - - - -

build_gcr_image:
	docker build --platform linux/amd64 -t  $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(GAR_IMAGE)/$(GAR_IMAGE):prod .

gcr_new_ar:
  gcloud artifacts repositories create $(GAR_IMAGE) --repository-format=docker --location=$(GCP_REGION) --description="Repository for storing $(GAR_IMAGE) images"

push_gcr_image:
	docker push $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(GAR_IMAGE)/$(GAR_IMAGE):prod

gcr_deploy:
	gcloud run deploy --image $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(GAR_IMAGE)/$(GAR_IMAGE):prod --memory $(GAR_MEMORY) --region $(GCP_REGION) --env-vars-file .env.yaml

rebuild_and_deploy:
	make build_gcr_image
	make push_gcr_image
	make gcr_deploy

##### BigQuery - - - - - - - - - - - - - - - - - - - - - - - - -

create_bq_env:
	make create_bq_ds
	make create_bq_tables

create_bq_ds:
	bq mk --project_id $(GCP_PROJECT) --data_location $(BQ_REGION) $(BQ_DATASET)

create_bq_tables:
	bq mk --location=$(GCP_REGION) --schema=user_queries_schema.json $(BQ_DATASET).$(BQ_USER_QUERY_T)
	bq mk --location=$(GCP_REGION) --schema=chat_history_schema.json $(BQ_DATASET).$(BQ_CHAT_HISTORY_T)

delete_bq_ds:
	bq rm -r -f -d --project_id $(GCP_PROJECT) $(BQ_DATASET)

reset_bq:
	make delete_bq_ds
	make create_bq_ds
	make create_bq_tables
