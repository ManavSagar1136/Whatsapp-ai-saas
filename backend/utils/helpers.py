from datetime import datetime
from typing import Optional

def setup_logs_directory():
    import os
    if not os.path.exists("logs"):
        os.makedirs("logs")

def parse_iso_datetime(date_string: str) -> Optional[datetime]:
    """Safely parse a datetime string, commonly returned by LLM or Webhook."""
    try:
        # Handling basic ISO formats
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None

def format_time_slot(dt: datetime) -> str:
    """Format datetime into a user-friendly 12-hour string, e.g. 10:30 AM"""
    return dt.strftime("%I:%M %p")
