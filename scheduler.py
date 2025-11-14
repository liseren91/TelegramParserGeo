"""
Scheduler script for automatic daily updates
Runs the parser at specified times every day
"""
import schedule
import time
import asyncio
import logging
from datetime import datetime
from main import full_update

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_update():
    """Wrapper function to run the async update"""
    try:
        logger.info(f"Scheduled update triggered at {datetime.now()}")
        asyncio.run(full_update())
    except Exception as e:
        logger.error(f"Scheduled update failed: {e}", exc_info=True)


def start_scheduler():
    """Start the scheduler"""
    # Schedule daily update at 9:00 AM
    schedule.every().day.at("09:00").do(run_update)
    
    # You can add multiple schedule times if needed:
    # schedule.every().day.at("18:00").do(run_update)  # Evening update
    
    logger.info("Scheduler started. Waiting for scheduled times...")
    logger.info("Scheduled updates:")
    for job in schedule.get_jobs():
        logger.info(f"  - {job}")
    
    # Run immediately on start (optional, comment out if not needed)
    logger.info("Running initial update...")
    run_update()
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == '__main__':
    try:
        start_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)

