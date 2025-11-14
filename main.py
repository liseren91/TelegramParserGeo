"""
Main script for Telegram Parser
Orchestrates data collection and updates to Google Sheets
"""
import asyncio
import logging
from datetime import datetime, timedelta
import config
from telegram_parser import TelegramParser
from sheets_manager import SheetsManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def update_channels_info():
    """Update channel information in Google Sheets"""
    logger.info("=" * 50)
    logger.info("Starting channels info update")
    logger.info("=" * 50)
    
    try:
        # Validate configuration
        config.validate_config()
        
        # Initialize Telegram parser
        parser = TelegramParser(
            config.TELEGRAM_API_ID,
            config.TELEGRAM_API_HASH,
            config.TELEGRAM_PHONE,
            session_name=config.TELEGRAM_SESSION_NAME
        )
        await parser.start()
        
        # Initialize Google Sheets manager
        sheets = SheetsManager(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            config.GOOGLE_SHEET_ID
        )
        
        # Ensure channels sheet exists
        sheets.ensure_sheet_exists(config.CHANNELS_SHEET_NAME, config.CHANNELS_HEADERS)
        
        # Get all channels info
        logger.info(f"Fetching info for {len(config.TELEGRAM_CHANNELS)} channels...")
        channels_info = await parser.get_all_channels_info(config.TELEGRAM_CHANNELS)
        
        # Update Google Sheets
        sheets.update_channels_info(config.CHANNELS_SHEET_NAME, channels_info)
        
        logger.info(f"✓ Successfully updated info for {len(channels_info)} channels")
        
        # Stop Telegram client
        await parser.stop()
        
    except Exception as e:
        logger.error(f"Error updating channels info: {e}", exc_info=True)
        raise


async def update_posts(days=1):
    """
    Update posts in Google Sheets
    
    Args:
        days: Number of days to look back for posts (default: 1)
    """
    logger.info("=" * 50)
    logger.info(f"Starting posts update (last {days} day(s))")
    logger.info("=" * 50)
    
    try:
        # Validate configuration
        config.validate_config()
        
        # Initialize Telegram parser
        parser = TelegramParser(
            config.TELEGRAM_API_ID,
            config.TELEGRAM_API_HASH,
            config.TELEGRAM_PHONE,
            session_name=config.TELEGRAM_SESSION_NAME
        )
        await parser.start()
        
        # Initialize Google Sheets manager
        sheets = SheetsManager(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            config.GOOGLE_SHEET_ID
        )
        
        # Ensure posts sheet exists
        sheets.ensure_sheet_exists(config.POSTS_SHEET_NAME, config.POSTS_HEADERS)
        
        # Get all posts
        logger.info(f"Fetching posts from {len(config.TELEGRAM_CHANNELS)} channels...")
        all_posts = await parser.get_all_posts(config.TELEGRAM_CHANNELS, days)
        
        logger.info(f"Processing {len(all_posts)} posts for upsert")
        
        updated_count, appended_count = sheets.append_posts(config.POSTS_SHEET_NAME, all_posts)
        if updated_count or appended_count:
            logger.info(
                f"✓ Updated stats for {updated_count} posts and added {appended_count} new posts"
            )
        else:
            logger.info("No posts required updates or additions")

        active_links = {post['link'] for post in all_posts if post.get('link')}
        min_date = datetime.now() - timedelta(days=days + 1)
        deleted_changes = sheets.mark_deleted_posts(
            config.POSTS_SHEET_NAME,
            active_links,
            min_date=min_date
        )
        logger.info(f"Checked deleted posts; {deleted_changes} rows updated")
        
        # Clean up old posts (optional, keeps last 30 days)
        # sheets.clear_old_posts(config.POSTS_SHEET_NAME, days_to_keep=30)
        
        # Stop Telegram client
        await parser.stop()
        
    except Exception as e:
        logger.error(f"Error updating posts: {e}", exc_info=True)
        raise


async def full_update():
    """Perform full update: channels info and posts"""
    logger.info("=" * 70)
    logger.info(f"STARTING FULL UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    try:
        # Update channels info
        await update_channels_info()
        
        # Wait a bit between updates
        await asyncio.sleep(5)
        
        # Update posts
        await update_posts(days=1)
        
        logger.info("=" * 70)
        logger.info("FULL UPDATE COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error("FULL UPDATE FAILED", exc_info=True)
        raise


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'channels':
            # Update only channels info
            asyncio.run(update_channels_info())
        elif command == 'posts':
            # Update only posts
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            asyncio.run(update_posts(days))
        elif command == 'full':
            # Full update
            asyncio.run(full_update())
        else:
            print("Unknown command. Use: channels, posts [days], or full")
            sys.exit(1)
    else:
        # Default: full update
        asyncio.run(full_update())


if __name__ == '__main__':
    main()

