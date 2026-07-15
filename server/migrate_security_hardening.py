"""Idempotent production schema upgrade for the security hardening release.

Run automatically at API startup after `Base.metadata.create_all`, and safe to
run manually with `python migrate_security_hardening.py`.
"""
from sqlalchemy import text
from config.database import engine


POSTGRES_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS ix_experiments_group_deleted_updated ON experiments (group_id, is_deleted, updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_daily_logs_experiment_created ON daily_logs (experiment_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_daily_logs_author ON daily_logs (author_id)",
    "CREATE INDEX IF NOT EXISTS ix_lab_events_group_start ON lab_events (group_id, start_date)",
    "CREATE INDEX IF NOT EXISTS ix_activity_logs_group_created ON activity_logs (group_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_notices_group_type_created ON notices (group_id, type, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_group_users_group_user ON group_users (group_id, user_id)",
    "DO $$ BEGIN ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK (role IN ('sys_admin', 'team_admin', 'member')); EXCEPTION WHEN duplicate_object THEN NULL; END $$",
    "DO $$ BEGIN ALTER TABLE users ADD CONSTRAINT ck_users_status CHECK (status IN ('active', 'pending', 'rejected')); EXCEPTION WHEN duplicate_object THEN NULL; END $$",
    "DO $$ BEGIN ALTER TABLE experiments ADD CONSTRAINT ck_experiments_status CHECK (status IN ('running', 'paused', 'completed', 'archived')); EXCEPTION WHEN duplicate_object THEN NULL; END $$",
    "DO $$ BEGIN ALTER TABLE lab_events ADD CONSTRAINT ck_lab_events_date_range CHECK (end_date IS NULL OR end_date >= start_date); EXCEPTION WHEN duplicate_object THEN NULL; END $$",
)


def migrate_security_hardening() -> None:
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as connection:
        for statement in POSTGRES_STATEMENTS:
            try:
                connection.execute(text(statement))
            except Exception as exc:
                print(f"Security migration warning: {exc}")


if __name__ == "__main__":
    migrate_security_hardening()
