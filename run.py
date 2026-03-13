"""
Combined entry point: Flask web server + background scheduler.

Railway (and similar PaaS) require a listening HTTP process to keep
the service alive and generate a public URL.  This module starts
the Flask app on 0.0.0.0:$PORT and runs the hourly scheduler in a
daemon thread so both coexist in a single container.
"""
import logging
import os
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def _run_scheduler():
    """Run the hourly scheduler in the current thread (blocking)."""
    import schedule
    import time
    import asyncio
    from main import full_update
    from flood_tracker import is_flood_wait_active, get_flood_wait_remaining

    def run_update():
        remaining = get_flood_wait_remaining()
        if remaining > 0:
            logger.info(
                "Skipping scheduled update: FloodWait still active for %d s",
                remaining,
            )
            return
        try:
            logger.info("Scheduled update triggered")
            asyncio.run(full_update())
        except Exception as e:
            logger.error("Scheduled update failed: %s", e, exc_info=True)

    schedule.every().hour.at(":00").do(run_update)

    logger.info("Background scheduler started (runs every hour at :00)")

    logger.info("Running initial update...")
    run_update()

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    from web_app import app

    scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
    scheduler_thread.start()

    port = int(os.environ.get("PORT", 8010))
    logger.info("Starting web server on 0.0.0.0:%s", port)
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
