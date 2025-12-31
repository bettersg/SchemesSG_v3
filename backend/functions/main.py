"""
This is the main file for the Firebase Functions.

The following endpoints are available:

1. Search and Retrieval:
   - schemes_search: Search for schemes based on user query with pagination support
   - schemes: Get details of a specific scheme
   - retrieve_search_queries: Get search history for a session

2. User Interaction:
   - chat_message: Chat interface for scheme recommendations
   - feedback: Submit user feedback
   - update_scheme: Submit new schemes or request edits

3. Slack Integration:
   - slack_trigger_message: Trigger a Slack review message for a specific document
   - slack_scan_and_notify: Scan source documents and post review messages for new items
   - slack_interactive: Handle Slack interactive component events (buttons, modals)

4. New Scheme Processing (Firestore Triggers):
   - on_new_scheme_entry: Triggered on schemeEntries document creation, runs pipeline steps 1-4
     (scraping, LLM extraction, planning area), then posts to Slack for human review

5. Batch Jobs:
   - scheduled_link_check_and_reindex: Monthly scheduled job to check all scheme links,
     mark dead links inactive, post summary to Slack, and reindex embeddings

6. System:
   - health: Health check endpoint
   - keep_endpoints_warm: Scheduled task to reduce cold starts

All endpoints (except health) support warmup requests:
- GET endpoints: Add ?is_warmup=true as URL parameter
- POST endpoints: Include {"is_warmup": true} in request body

When is_warmup=true, endpoints return 200 immediately without database operations.

Local Development:
1. Run emulator: `docker compose -f docker-compose-firebase.yml up --build`
2. Test warmup: `curl http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/keep_endpoints_warm-0`

Note: Do not deploy functions using firebase deploy. Deployment is handled by Github Actions.
"""

import json
import sys

from chat.chat import chat_message  # noqa: F401
from fb_manager.firebaseManager import FirebaseManager
from feedback.feedback import feedback  # noqa: F401
from firebase_functions import https_fn, options
from loguru import logger
from schemes.schemes import schemes  # noqa: F401
from schemes.search import schemes_search  # noqa: F401
from schemes.search_queries import retrieve_search_queries  # noqa: F401
from slack_integration.slack import (  # noqa: F401
    slack_interactive,
    slack_scan_and_notify,
    slack_trigger_message,
)
from update_scheme.update_scheme import update_scheme  # noqa: F401
from utils.endpoints import keep_endpoints_warm  # noqa: F401
from new_scheme.trigger_new_scheme_pipeline import on_new_scheme_entry  # noqa: F401
from batch_jobs.run_link_check_and_reindex import scheduled_link_check_and_reindex  # noqa: F401


# Initialise logger
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    colorize=True,
)
logger.info("Logger initialised")

# Initialise the Firebase Admin SDK and Connection to firestore
firebase_manager = FirebaseManager()


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,  # Increases memory to 1GB
)
def health(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for health check endpoint

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """

    return https_fn.Response(response=json.dumps({"status": "ok"}), status=200, mimetype="application/json")
