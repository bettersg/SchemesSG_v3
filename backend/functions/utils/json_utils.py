"""JSON utilities for handling Firestore data types."""

import json
import math
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
from datetime import datetime


class FirestoreJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Firestore data types.

    This encoder converts Firestore-specific data types to JSON-serializable formats:
    - Firestore Timestamp objects are converted to ISO format strings
    - DatetimeWithNanoseconds objects are converted to ISO format strings
    - Other datetime objects are converted to ISO format strings
    - NaN and Infinity values are converted to None (null in JSON)
    """

    def default(self, obj):
        """Convert Firestore data types to JSON-serializable formats.

        Args:
            obj: The object to serialize

        Returns:
            JSON-serializable representation of the object
        """
        # Handle Firestore Timestamp objects
        if hasattr(obj, 'timestamp') and hasattr(obj, 'isoformat'):
            return obj.isoformat()

        # Handle DatetimeWithNanoseconds (Firestore datetime type)
        if isinstance(obj, DatetimeWithNanoseconds):
            return obj.isoformat()

        # Handle standard datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Let the base class handle other types
        return super().default(obj)

    def encode(self, obj):
        """Override encode to handle NaN/Infinity in nested structures."""
        return super().encode(self._sanitize(obj))

    def _sanitize(self, obj):
        """Recursively replace NaN/Infinity with None."""
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize(item) for item in obj]
        return obj


def safe_json_dumps(data, **kwargs):
    """Safely serialize data to JSON, handling Firestore data types.
    
    Args:
        data: The data to serialize
        **kwargs: Additional arguments to pass to json.dumps
        
    Returns:
        str: JSON string representation of the data
    """
    return json.dumps(data, cls=FirestoreJSONEncoder, **kwargs)