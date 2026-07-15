"""
APScheduler configuration for automated database backups.
Runs daily at 3:00 AM and cleans old backups based on retention settings.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config.database import SessionLocal
from models.intelligence import SystemSetting

scheduler = BackgroundScheduler()

def scheduled_backup_job():
    """Run the encrypted, retention-aware backup implementation."""
    db = SessionLocal()
    try:
        setting = db.query(SystemSetting).filter(SystemSetting.key == "auto_backup").first()
        if setting and setting.value.lower() != "true":
            print("[Backup Scheduler] Automatic backups are disabled by system settings.")
            return
    finally:
        db.close()
    # Reuse the same encrypted, retention-aware implementation as manual
    # backups so the two execution paths cannot drift.
    from routers.backup import create_backup
    try:
        filename = create_backup()
        print(f"[Backup Scheduler] ✅ Encrypted backup created: {filename}")
    except Exception as exc:
        print(f"[Backup Scheduler] ❌ Backup job failed: {exc}")


def start_scheduler():
    """Start the APScheduler with daily backup at 3 AM."""
    scheduler.add_job(
        scheduled_backup_job,
        CronTrigger(hour=3, minute=0),
        id="daily_backup",
        name="Daily Database Backup",
        replace_existing=True
    )
    scheduler.start()
    print("[Backup Scheduler] ✅ Started — daily backup at 03:00 AM")


def shutdown_scheduler():
    """Gracefully shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Backup Scheduler] 🛑 Shutdown complete")
