import os
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timezone
import uuid
import json

# Initialize a BigQuery client
project = os.getenv('GCP_PROJECT')
client = bigquery.Client(project=project)

def save_query(query_text,response):
    dataset_id = os.getenv('BQ_DATASET')
    table_id = os.getenv('BQ_USER_QUERY_T')
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)  # Make an API request to fetch the table
    query_id = uuid.uuid4()
    json_string = json.dumps(response)  # Convert JSON to a string

    rows_to_insert = [
        { "user_id": str(query_id), "query_text": query_text, "query_timestamp": datetime.now(timezone.utc).isoformat(), "schemes_response":json_string }
    ]

    errors = client.insert_rows_json(table, rows_to_insert)  # Make an API request
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))

    return query_id


def save_chat_history(query_uuid, chat_text):
    dataset_id = os.getenv('BQ_DATASET')
    table_id = os.getenv('BQ_CHAT_HISTORY_T')
    full_table_id = f"{client.project}.{dataset_id}.{table_id}"


    # Ensure query_uuid is a string
    query_uuid_str = str(query_uuid)

    # Prepare the chat history JSON and ensure it is properly escaped
    chat_history_json = json.dumps(chat_text, ensure_ascii=False)

    # Construct a parameterized query
    query = f"""
    MERGE `{full_table_id}` T
    USING (SELECT @query_uuid AS query_uuid, @chat_text AS chat_text, @chat_timestamp AS chat_timestamp) S
    ON T.query_uuid = S.query_uuid
    WHEN MATCHED THEN
        UPDATE SET T.chat_text = CONCAT(T.chat_text, '\\n', S.chat_text), T.chat_timestamp = S.chat_timestamp
    WHEN NOT MATCHED THEN
        INSERT (query_uuid, chat_text, chat_timestamp) VALUES (query_uuid, chat_text, chat_timestamp)
    """

    # Set up the query parameters
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("query_uuid", "STRING", query_uuid_str),
            bigquery.ScalarQueryParameter("chat_text", "STRING", chat_history_json),
            bigquery.ScalarQueryParameter("chat_timestamp", "TIMESTAMP", datetime.now(timezone.utc).isoformat())
        ]
    )

    # Execute the query
    job = client.query(query, job_config=job_config)
    job.result()  # Wait for the query to finish

    print("Chat history saved or updated.")
