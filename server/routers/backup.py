"""
Database Backup & Restore Router
- Manual trigger backup
- List available backups
- Restore from backup
- Scheduled automatic daily backups via APScheduler
"""
import os
import subprocess
import glob
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from models.user import User
from models.intelligence import SystemSetting
from routers.auth import get_current_user

router = APIRouter(prefix="/backup", tags=["Backup"])

BACKUP_DIR = os.environ.get("BACKUP_DIR", "/backups")

def _ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)

def _get_db_url_parts() -> dict:
    """Parse DATABASE_URL env var into connection parts for pg_dump/psql."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://lab_user:lab_password_2026@localhost:5432/lab_logs")
    # Format: postgresql://user:password@host:port/dbname
    url = db_url.replace("postgresql://", "")
    # Split user:password@host:port/dbname
    auth_host, dbname = url.rsplit("/", 1)
    user_pass, host_port = auth_host.split("@")
    user, password = user_pass.split(":")
    host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "dbname": dbname
    }

def _run_pg_dump(output_path: str) -> bool:
    """Run pg_dumpall to backup the database. Returns True on success."""
    parts = _get_db_url_parts()
    env = os.environ.copy()
    env["PGPASSWORD"] = parts["password"]
    
    try:
        with open(output_path, "w") as f:
            result = subprocess.run(
                [
                    "pg_dumpall",
                    "-h", parts["host"],
                    "-p", parts["port"],
                    "-U", parts["user"],
                    "--no-password",
                ],
                stdout=f,
                stderr=subprocess.PIPE,
                env=env,
                timeout=600  # 10 minutes timeout
            )
        return result.returncode == 0
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def _run_psql_restore(backup_path: str) -> bool:
    """Run psql to restore from a backup file. Returns True on success."""
    parts = _get_db_url_parts()
    env = os.environ.copy()
    env["PGPASSWORD"] = parts["password"]
    
    try:
        with open(backup_path, "r") as f:
            result = subprocess.run(
                [
                    "psql",
                    "-h", parts["host"],
                    "-p", parts["port"],
                    "-U", parts["user"],
                    "-d", parts["dbname"],
                    "--no-password",
                ],
                stdin=f,
                stderr=subprocess.PIPE,
                env=env,
                timeout=600
            )
        return result.returncode == 0
    except Exception as e:
        print(f"Restore failed: {e}")
        return False


def create_backup() -> str:
    """Create a backup file. Returns the filename on success, raises on failure."""
    _ensure_backup_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"mux_backup_{timestamp}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    success = _run_pg_dump(filepath)
    if not success:
        # Clean up failed file
        if os.path.exists(filepath):
            os.remove(filepath)
        raise RuntimeError("pg_dumpall failed. Check database connectivity.")
    
    # Get file size
    size_bytes = os.path.getsize(filepath)
    
    # Clean old backups based on retention setting
    _cleanup_old_backups()
    
    return filename


def _cleanup_old_backups():
    """Remove backups older than the retention period."""
    _ensure_backup_dir()
    retention_days = 7  # Default
    
    files = glob.glob(os.path.join(BACKUP_DIR, "mux_backup_*.sql"))
    cutoff = datetime.now() - timedelta(days=retention_days)
    
    for fpath in files:
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if mtime < cutoff:
                os.remove(fpath)
                print(f"Cleaned old backup: {os.path.basename(fpath)}")
        except Exception as e:
            print(f"Failed to clean {fpath}: {e}")


# --- API Endpoints ---

@router.post("/trigger")
def trigger_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger a database backup. Sys admin only."""
    if current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="Only System Admin can trigger backups.")
    
    try:
        filename = create_backup()
        return {
            "status": "success",
            "message": f"Backup created: {filename}",
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/list")
def list_backups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available backup files with size and date info."""
    if current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="Only System Admin can view backups.")
    
    _ensure_backup_dir()
    files = glob.glob(os.path.join(BACKUP_DIR, "mux_backup_*.sql"))
    backups = []
    for fpath in sorted(files, reverse=True):
        stat = os.stat(fpath)
        backups.append({
            "filename": os.path.basename(fpath),
            "size_bytes": stat.st_size,
            "size_display": _format_size(stat.st_size),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    return {"backups": backups, "backup_dir": BACKUP_DIR}


@router.post("/restore/{filename}")
def restore_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore database from a backup file. Sys admin only."""
    if current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="Only System Admin can restore backups.")
    
    # Sanitize filename
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid backup filename.")
    
    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Backup file '{filename}' not found.")
    
    try:
        success = _run_psql_restore(filepath)
        if not success:
            raise HTTPException(status_code=500, detail="Restore with psql failed. Backup may be corrupt.")
        return {"status": "success", "message": f"Database restored from {filename}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.get("/settings")
def get_backup_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get backup configuration settings."""
    if current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="Only System Admin can view backup settings.")
    
    auto_backup = db.query(SystemSetting).filter(SystemSetting.key == "auto_backup").first()
    retention = db.query(SystemSetting).filter(SystemSetting.key == "backup_retention_days").first()
    
    return {
        "auto_backup": auto_backup.value if auto_backup else "true",
        "retention_days": int(retention.value) if retention else 7
    }


@router.put("/settings")
def update_backup_settings(
    auto_backup: str = "true",
    retention_days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update backup configuration."""
    if current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="Only System Admin can modify backup settings.")
    
    for key, value in [("auto_backup", auto_backup), ("backup_retention_days", str(retention_days))]:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not setting:
            setting = SystemSetting(key=key, value=value)
            db.add(setting)
        else:
            setting.value = value
    
    db.commit()
    return {"status": "success", "auto_backup": auto_backup, "retention_days": retention_days}


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
