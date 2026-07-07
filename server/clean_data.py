from config.database import SessionLocal
from models.user import User

def cleanup():
    db = SessionLocal()
    try:
        # 查找那个显眼的脏数据
        target = db.query(User).filter(User.email == 'test2@mail').first()
        if target:
            print(f"🗑️ Found invalid user: {target.email}, removing...")
            db.delete(target)
            db.commit()
            print("✅ Cleanup complete.")
        else:
            print("💡 No invalid data found.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()