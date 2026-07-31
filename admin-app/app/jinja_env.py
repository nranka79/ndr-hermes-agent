from datetime import datetime, timedelta, timezone
from pathlib import Path
import jinja2

TEMPLATES_DIR = Path(__file__).parent / "templates"

IST = timezone(timedelta(hours=5, minutes=30))


def ist(value):
    """Format an ISO-8601 UTC timestamp as IST, e.g. '31 Jul 2026, 02:45 PM'.

    Returns '-' for falsy input and the raw string for anything that
    doesn't parse as a timestamp (defensive -- vault always sends ISO)."""
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).strftime("%d %b %Y, %I:%M %p")


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)
env.filters["ist"] = ist
