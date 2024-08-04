FROM python:3.10.6-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# require download spacy en core web sm.run
RUN python -m spacy download en_core_web_sm

# might face issue with library version conflict. run:
# export KMP_DUPLICATE_LIB_OK=TRUE

# You can add --port $PORT if you need to set PORT as a specific env variable
CMD uvicorn fast_api.api:app --host 0.0.0.0 --port $PORT
