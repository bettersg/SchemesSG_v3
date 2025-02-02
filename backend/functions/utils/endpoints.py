"""
Utility functions and scheduled tasks for managing Firebase Cloud Function endpoints.

This module provides utilities for:
1. Generating endpoint URLs based on environment (local/staging/prod)
2. Making warmup requests to keep endpoints active
3. Scheduled task to periodically warm up all endpoints to reduce cold starts

The scheduled warmup task runs every 4 minutes and keeps the following endpoints warm:
- schemes_search: POST endpoint for searching schemes
- schemes: GET endpoint for retrieving individual schemes
- chat_message: POST endpoint for chat interactions
- feedback: POST endpoint for user feedback
- update_scheme: POST endpoint for scheme update requests
- search_queries: GET endpoint for retrieving search history

All endpoints support an `is_warmup` parameter that, when true, will return a 200 status
immediately without performing any database operations. This helps reduce unnecessary
load during warmup requests.

For GET endpoints (schemes, search_queries), the warmup parameter is passed as a URL query:
  ?is_warmup=true

For POST endpoints (schemes_search, chat_message, feedback, update_scheme), the warmup
parameter is included in the request body:
  { "is_warmup": true }

For local testing:
1. Start the Firebase emulator using Docker Compose:
   ```
   cd backend
   docker compose -f docker-compose-firebase.yml up --build
   ```

2. Trigger the warmup function manually:
   ```
   curl http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/keep_endpoints_warm-0
   ```

Note: The '-0' suffix in the URL is required for scheduled functions when testing locally.
"""

import os
from typing import Dict, Optional

import requests
from firebase_functions import options, scheduler_fn
from loguru import logger


def get_endpoint_url(function_name: str) -> str:
    """
    Get the appropriate endpoint URL based on environment and function name.

    Args:
        function_name (str): Name of the cloud function

    Returns:
        str: The complete URL for the endpoint
    """
    env = os.getenv("ENVIRONMENT")
    project_id = os.getenv("FB_PROJECT_ID")
    region = "asia-southeast1"

    if env == "local":
        host = os.getenv("FUNCTIONS_HOST", "127.0.0.1")
        port = os.getenv("FUNCTIONS_PORT", "5001")
        return f"http://{host}:{port}/schemessg-v3-dev/{region}/{function_name}"

    if project_id:
        return f"https://{region}-{project_id}.cloudfunctions.net/{function_name}"

    return f"http://127.0.0.1:5001/schemessg-v3-dev/{region}/{function_name}"


def make_warmup_request(url: str, method: str = "GET", json_data: Optional[Dict] = None) -> bool:
    """
    Make a warmup request to the specified endpoint.

    Args:
        url (str): The endpoint URL
        method (str): HTTP method (GET or POST)
        json_data (Optional[Dict]): JSON data for POST requests

    Returns:
        bool: True if request was successful (should always be 200 for warmup requests), False otherwise
    """
    try:
        logger.info(f"Making warm-up request to: {url}")

        response = requests.request(
            method=method,
            url=url,
            json=json_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        # For warmup requests, we expect 200 status code
        # The endpoints will return immediately without database operations
        if response.status_code == 200:
            logger.info(f"Successfully kept {url} warm")
            return True

        logger.error(f"Failed to keep {url} warm. Status code: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return False

    except requests.exceptions.Timeout:
        logger.error(f"Timeout while trying to keep {url} warm")
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while trying to keep {url} warm")
    except Exception as e:
        logger.exception(f"Error making warmup request to {url}", e)

    return False


@scheduler_fn.on_schedule(
    schedule="*/4 * * * *",  # Run every 4 minutes
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,
    concurrency=1,  # Only allow one instance at a time
    min_instances=0,  # Don't keep instances warm
    max_instances=1,  # Maximum one instance
    retry_count=0,  # Don't retry on failure
)
def keep_endpoints_warm(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Scheduled function to keep the endpoints warm by making simple requests.
    This helps reduce cold starts by periodically initializing the functions.

    Each endpoint supports an `is_warmup` parameter that, when true, will:
    1. Return a 200 status immediately
    2. Skip any database operations
    3. Still initialize the function's runtime environment

    Args:
        event (scheduler_fn.ScheduledEvent): The event object
    """
    try:
        # Define endpoints configuration
        endpoints = [
            {
                "name": "schemes_search",
                "method": "POST",
                "url": get_endpoint_url("schemes_search"),
                "data": {
                    "query": "education",
                    "top_k": 1,
                    "similarity_threshold": 0,
                    "is_warmup": True,  # Endpoint will return 200 immediately
                },
            },
            {
                "name": "schemes",
                "method": "GET",
                "url": f"{get_endpoint_url('schemes')}/1?is_warmup=true",  # Endpoint will return 200 immediately
                "data": None,
            },
            {
                "name": "chat_message",
                "method": "POST",
                "url": get_endpoint_url("chat_message"),
                "data": {
                    "message": "Hello",
                    "sessionID": "warmup-test-session",
                    "is_warmup": True,  # Endpoint will return 200 immediately
                },
            },
            {
                "name": "feedback",
                "method": "POST",
                "url": get_endpoint_url("feedback"),
                "data": {
                    "feedbackText": "Warmup test",
                    "userName": "Warmup User",
                    "userEmail": "warmup@test.com",
                    "is_warmup": True,  # Endpoint will return 200 immediately
                },
            },
            {
                "name": "update_scheme",
                "method": "POST",
                "url": get_endpoint_url("update_scheme"),
                "data": {
                    "Changes": "Warmup test",
                    "Description": "Warmup test",
                    "Link": "https://warmup.test",
                    "Scheme": "Warmup Scheme",
                    "Status": "Warmup",
                    "entryId": "warmup-1",
                    "userName": "Warmup User",
                    "userEmail": "warmup@test.com",
                    "typeOfRequest": "warmup",
                    "is_warmup": True,  # Endpoint will return 200 immediately
                },
            },
            {
                "name": "search_queries",
                "method": "GET",
                "url": f"{get_endpoint_url('retrieve_search_queries')}/warmup-session?is_warmup=true",  # Endpoint will return 200 immediately
                "data": None,
            },
        ]

        # Make warmup requests to all endpoints
        results = [
            make_warmup_request(url=endpoint["url"], method=endpoint["method"], json_data=endpoint["data"])
            for endpoint in endpoints
        ]

        # Log overall status
        if all(results):
            logger.info("Successfully kept all endpoints warm")
        else:
            logger.warning(f"Failed to keep some endpoints warm. Success rate: {sum(results)}/{len(results)}")

    except Exception as e:
        logger.exception("Error in keep_endpoints_warm function", e)

    return None  # Always return None to avoid retries
