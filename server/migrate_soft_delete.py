"""
Migration: Add is_deleted and deleted_at columns to experiments table.
"""
from config.database import engine, SessionLocal
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='experiments' AND column_name='is_deleted'
        """))
        if result.fetchone():
            print("✅ 'is_deleted' column already exists. Skipping.")
            return
        
        db.execute(text("ALTER TABLE experiments ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL"))
        db.execute(text("ALTER TABLE experiments ADD COLUMN deleted_at TIMESTAMP NULL"))
        db.commit()
        print("✅ Added is_deleted and deleted_at columns to experiments table.")
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
