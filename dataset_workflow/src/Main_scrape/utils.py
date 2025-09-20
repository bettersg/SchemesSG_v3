
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

def check_if_scraped_require_refresh(firestore_dt):
    # Current time in UTC
    now = datetime.now(timezone.utc)

    # One month ago
    one_month_ago = now - relativedelta(months=1)

    # Return True if the data is older than one month (needs refresh)
    # Return False if the data is newer than one month (no refresh needed)
    is_older_than_a_month = firestore_dt < one_month_ago
    return is_older_than_a_month
