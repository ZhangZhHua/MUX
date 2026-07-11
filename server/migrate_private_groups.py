"""
Migration: Add is_private/owner_id to groups table, create private groups for existing users.
"""
from config.database import SessionLocal
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # 1. Add columns
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='groups' AND column_name='is_private'
        """))
        if not result.fetchone():
            db.execute(text("ALTER TABLE groups ADD COLUMN is_private BOOLEAN DEFAULT FALSE NOT NULL"))
            db.execute(text("ALTER TABLE groups ADD COLUMN owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE"))
            db.commit()
            print("✅ Added is_private and owner_id columns to groups table.")
        else:
            print("✅ Columns already exist. Skipping ALTER TABLE.")
        
        # 2. Create private groups for existing users who don't have one
        users = db.execute(text("""
            SELECT u.id, u.first_name, u.last_name FROM users u
            WHERE u.id NOT IN (
                SELECT g.owner_id FROM groups g WHERE g.is_private = TRUE AND g.owner_id IS NOT NULL
            )
        """)).fetchall()
        
        for user_row in users:
            uid, first, last = user_row
            name = f"[Private] {first} {last}"
            counter = 1
            while db.execute(text("SELECT id FROM groups WHERE name = :n"), {"n": name}).fetchone():
                name = f"[Private] {first} {last} ({counter})"
                counter += 1
            
            db.execute(text("""
                INSERT INTO groups (name, description, is_private, owner_id) 
                VALUES (:name, :desc, TRUE, :owner)
            """), {"name": name, "desc": f"Personal workspace for {first} {last}", "owner": uid})
            
            # Get the new group id
            gid = db.execute(text("SELECT id FROM groups WHERE name = :n"), {"n": name}).fetchone()[0]
            
            # Add user as member
            db.execute(text("""
                INSERT INTO group_users (user_id, group_id) VALUES (:uid, :gid)
                ON CONFLICT DO NOTHING
            """), {"uid": uid, "gid": gid})
            
            print(f"  Created private group '{name}' for user #{uid}")
        
        db.commit()
        print(f"✅ Migration complete. Created private groups for {len(users)} users.")
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
