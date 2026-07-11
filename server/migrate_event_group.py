"""
Migration script: Add group_id column to lab_events table.
Run after starting PostgreSQL:
    cd server && source venv/bin/activate && python migrate_event_group.py
"""
from config.database import engine, SessionLocal
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='lab_events' AND column_name='group_id'
        """))
        if result.fetchone():
            print("✅ Column 'group_id' already exists in lab_events. Skipping.")
            return
        
        # Get the first group_id to use as default for existing rows
        groups = db.execute(text("SELECT id FROM groups ORDER BY id LIMIT 1")).fetchone()
        default_group_id = groups[0] if groups else 1
        
        # Add column with a temporary default
        db.execute(text(f"ALTER TABLE lab_events ADD COLUMN group_id INTEGER"))
        db.execute(text(f"UPDATE lab_events SET group_id = {default_group_id}"))
        db.execute(text("ALTER TABLE lab_events ALTER COLUMN group_id SET NOT NULL"))
        db.execute(text("""
            ALTER TABLE lab_events ADD CONSTRAINT fk_lab_events_group_id 
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
        """))
        db.commit()
        print(f"✅ Migration complete. Added 'group_id' column to lab_events. Existing events assigned to group #{default_group_id}.")
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
