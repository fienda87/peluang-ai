import subprocess
from pathlib import Path

from fastapi import APIRouter

from app.shared.logging import get_logger

logger = get_logger("admin.pipeline")

BACKEND_DIR = Path(__file__).resolve().parents[2]
FLAG_FILE = BACKEND_DIR / "logs" / "schedule_enabled"
FLAG_FILE.parent.mkdir(exist_ok=True)
if not FLAG_FILE.exists():
    FLAG_FILE.write_text("on")

router = APIRouter(prefix="/admin/pipeline", tags=["admin"])


@router.post("/run-now")
async def run_now():
    """Trigger crawl + extract sebagai background process terpisah."""
    bat = BACKEND_DIR / "scripts" / "daily_tasks.bat"
    if not bat.exists():
        return {"status": "error", "reason": "daily_tasks.bat not found"}
    subprocess.Popen(
        ["cmd", "/c", str(bat)],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    logger.info("pipeline_run_triggered")
    return {"status": "started", "note": "cek logs/daily.log untuk progres"}


@router.get("/schedule")
async def get_schedule():
    enabled = FLAG_FILE.read_text().strip().lower() == "on"
    return {"auto_daily": enabled}


@router.post("/schedule")
async def set_schedule(enable: bool):
    FLAG_FILE.write_text("on" if enable else "off")
    logger.info("schedule_toggled", enabled=enable)
    return {"auto_daily": enable}
