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


def epoch_ist(value):
    """Format a Unix epoch (usage events) as IST."""
    if value in (None, ""):
        return "-"
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone(IST).strftime(
            "%d %b %Y, %I:%M %p"
        )
    except (TypeError, ValueError, OSError):
        return value


def money(value):
    """Format USD without hiding tiny per-call costs behind $0.0000."""
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        return "$0.00"
    if v == 0:
        return "$0.00"
    if abs(v) < 0.01:
        return f"${v:.6f}"
    if abs(v) < 1:
        return f"${v:.4f}"
    return f"${v:,.2f}"


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)
env.filters["ist"] = ist
env.filters["epoch_ist"] = epoch_ist
env.filters["money"] = money
