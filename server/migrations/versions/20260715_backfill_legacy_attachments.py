"""Backfill attachment metadata for files uploaded before the attachment table.

Older rows store attachment names in JSON, while the secured download endpoint
uses the normalized attachments table. This one-time migration preserves
existing links without weakening the new authorization checks.
"""
import hashlib
import json
import mimetypes
from pathlib import Path

from alembic import op
from sqlalchemy.orm import Session

from models.daily_log import Attachment, DailyLog
from models.event import LabEvent
from models.user import User

revision = "20260715_backfill_attach"
down_revision = "20260715_initial_schema"
branch_labels = None
depends_on = None

UPLOAD_ROOT = Path("/app/uploads").resolve()


def _add_attachment(session, name, owner_id, group_id=None, daily_log_id=None):
    if not isinstance(name, str) or not name or Path(name).name != name:
        return
    if session.query(Attachment.id).filter(Attachment.storage_name == name).first():
        return
    path = (UPLOAD_ROOT / name).resolve()
    if UPLOAD_ROOT not in path.parents or not path.is_file():
        return
    media_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
    session.add(Attachment(
        storage_name=name,
        original_name=name,
        media_type=media_type,
        size_bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        owner_id=owner_id,
        group_id=group_id,
        daily_log_id=daily_log_id,
    ))


def upgrade():
    session = Session(bind=op.get_bind())
    try:
        for log in session.query(DailyLog).all():
            try:
                names = json.loads(log.attachments_json or "[]")
            except (TypeError, json.JSONDecodeError):
                names = []
            group_id = log.experiment.group_id if log.experiment else None
            for name in names:
                _add_attachment(session, name, log.author_id, group_id, log.id)

        for event in session.query(LabEvent).all():
            try:
                items = json.loads(event.attachments_json or "[]")
            except (TypeError, json.JSONDecodeError):
                items = []
            for item in items:
                name = item.get("name") if isinstance(item, dict) else item
                _add_attachment(session, name, event.author_id, event.group_id)

        for user in session.query(User).filter(User.avatar_node.isnot(None)).all():
            _add_attachment(session, user.avatar_node, user.id)
        session.commit()
    finally:
        session.close()


def downgrade():
    # Metadata is intentionally retained: it protects legacy files too.
    pass
