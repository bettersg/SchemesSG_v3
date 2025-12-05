FROM python:3.10
WORKDIR /dataset_workflow
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
ENTRYPOINT ["python", "-m", "src.run_data_pipeline"]
CMD ["dev"]
RUN mkdir output

