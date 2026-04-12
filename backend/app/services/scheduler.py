"""
APScheduler setup untuk scheduled WhatsApp notifications.
Cek semua tenant yang punya whatsapp_notify=True, kirim report sesuai jadwal.
"""
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models.tenant_settings import TenantSettings

scheduler = BackgroundScheduler()


def _run_wa_reports():
    """Check semua tenant, kirim WA report kalau jadwalnya match."""
    from datetime import datetime
    import pytz

    db = SessionLocal()
    try:
        now = datetime.now(pytz.timezone("Asia/Jakarta"))
        current_hour = now.hour
        current_minute = now.minute

        tenants = db.query(TenantSettings).filter(
            TenantSettings.whatsapp_notify == True,
            TenantSettings.whatsapp_group_id.isnot(None),
        ).all()

        for t in tenants:
            sched_hour = t.whatsapp_schedule_hour or 21
            sched_minute = t.whatsapp_schedule_minute or 30

            # Check if current time matches schedule (within 5 min window)
            if sched_hour == current_hour and abs(sched_minute - current_minute) <= 2:
                from app.services.whatsapp import send_scheduled_report
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(send_scheduled_report(t.tenant_id))
                finally:
                    loop.close()
    except Exception as e:
        print(f"[Scheduler ERROR]: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler — runs every 5 minutes."""
    scheduler.add_job(
        _run_wa_reports,
        CronTrigger(minute="*/5"),
        id="wa_daily_report",
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] WhatsApp report scheduler started (checks every 5 min)")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Scheduler] Stopped")
