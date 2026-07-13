"""
APScheduler configuration for automated database backups.
Runs daily at 3:00 AM and cleans old backups based on retention settings.
"""
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

def _get_db_url_parts():
    db_url = os.environ.get("DATABASE_URL", "postgresql://lab_user:lab_password_2026@localhost:5432/lab_logs")
    url = db_url.replace("postgresql://", "")
    auth_host, dbname = url.rsplit("/", 1)
    user_pass, host_port = auth_host.split("@")
    user, password = user_pass.split(":")
    host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")
    return {"user": user, "password": password, "host": host, "port": port, "dbname": dbname}

def scheduled_backup_job():
    """Daily backup job that uses pg_dumpall."""
    import subprocess, glob
    from datetime import timedelta
    
    backup_dir = os.environ.get("BACKUP_DIR", "/backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    parts = _get_db_url_parts()
    env = os.environ.copy()
    env["PGPASSWORD"] = parts["password"]
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"mux_backup_{timestamp}.sql"
    filepath = os.path.join(backup_dir, filename)
    
    try:
        with open(filepath, "w") as f:
            result = subprocess.run(
                ["pg_dumpall", "-h", parts["host"], "-p", parts["port"], "-U", parts["user"], "--no-password"],
                stdout=f, stderr=subprocess.PIPE, env=env, timeout=600
            )
        if result.returncode == 0:
            print(f"[Backup Scheduler] ✅ Backup created: {filename}")
            
            # Cleanup old backups (keep 7 days)
            retention_days = 7
            cutoff = datetime.now() - timedelta(days=retention_days)
            for fpath in glob.glob(os.path.join(backup_dir, "mux_backup_*.sql")):
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                    if mtime < cutoff:
                        os.remove(fpath)
                        print(f"[Backup Scheduler] 🗑️ Cleaned old backup: {os.path.basename(fpath)}")
                except Exception as e:
                    print(f"[Backup Scheduler] ⚠️ Failed to clean {fpath}: {e}")
        else:
            print(f"[Backup Scheduler] ❌ pg_dumpall failed with code {result.returncode}")
            if os.path.exists(filepath):
                os.remove(filepath)
    except Exception as e:
        print(f"[Backup Scheduler] ❌ Backup job failed: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)


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
