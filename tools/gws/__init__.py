"""
tools.gws — Google Workspace service handlers package.

Each module exposes a single public function handle_<service>() that accepts
(parts: list, account_email: str) and returns a JSON string or error string.
"""

from .gmail    import handle_gmail
from .drive    import handle_drive
from .sheets   import handle_sheets
from .calendar import handle_calendar
from .contacts import handle_contacts
from .tasks    import handle_tasks
from .docs     import handle_docs
from .admin    import handle_admin

__all__ = [
    "handle_gmail",
    "handle_drive",
    "handle_sheets",
    "handle_calendar",
    "handle_contacts",
    "handle_tasks",
    "handle_docs",
    "handle_admin",
]
