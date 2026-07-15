"""Baseline schema migration for new deployments and existing unversioned DBs."""
from alembic import op
from config.database import Base
import models.user, models.experiment, models.daily_log, models.event, models.intelligence  # noqa: F401
from migrate_security_hardening import migrate_security_hardening

revision = "20260715_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind())
    migrate_security_hardening()

def downgrade():
    raise RuntimeError("Baseline migration is intentionally irreversible.")
