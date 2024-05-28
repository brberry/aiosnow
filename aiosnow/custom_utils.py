from datetime import datetime, timezone

import pytz


def query_date(dt: datetime | str) -> str:
    """
    Ensures the given datetime is in UTC.

    Args:
        dt: The datetime object to check and convert if necessary.

    Returns:
        A string formatted for use in a ServiceNow query
    """
    if isinstance(dt, str):
        # Convert string to datetime
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")

        # Convert datetime to UTC
        dt = dt.astimezone(timezone.utc)

    # Check if the datetime is timezone-aware
    if dt.tzinfo is None:
        # Replace 'US/Eastern' with the actual timezone the naive datetime represents
        tz = pytz.timezone("US/Eastern")
        dt = tz.localize(dt)

    # Convert the datetime to UTC
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%d %H:%M:%S")
