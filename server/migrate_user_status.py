from config.database import SessionLocal
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        r = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='status'"))
        if not r.fetchone():
            db.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR DEFAULT 'active' NOT NULL"))
            db.execute(text("ALTER TABLE users ADD COLUMN last_active_at TIMESTAMP NULL"))
            db.commit()
            print("Added status and last_active_at columns to users.")
        else:
            print("Columns already exist.")
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
