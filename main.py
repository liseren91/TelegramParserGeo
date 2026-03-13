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


def _normalize_delay_range(min_seconds, max_seconds):
    """Return a safe (min, max) delay tuple in seconds."""
    min_seconds = max(0, int(min_seconds))
    max_seconds = max(0, int(max_seconds))
    if min_seconds > max_seconds:
        min_seconds, max_seconds = max_seconds, min_seconds
    return min_seconds, max_seconds


def normalize_channel_usernames(raw_channels):
    """
    Normalize user-provided Telegram channel identifiers.

    Supports:
    - @username
    - username
    - https://t.me/username
    - t.me/username
    """
    normalized = []
    seen = set()

    for raw in raw_channels:
        value = (raw or "").strip()
        if not value:
            continue

        if value.startswith("https://t.me/"):
            value = value[len("https://t.me/"):]
        elif value.startswith("http://t.me/"):
            value = value[len("http://t.me/"):]
        elif value.startswith("t.me/"):
            value = value[len("t.me/"):]

        value = value.split("?")[0].split("/")[0].strip()
        if value.startswith("@"):
            value = value[1:]

        if not value or value in seen:
            continue

        seen.add(value)
        normalized.append(value)

    return normalized


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
        per_channel_delay_range = _normalize_delay_range(
            config.PARSER_CHANNEL_DELAY_MIN_SEC,
            config.PARSER_CHANNEL_DELAY_MAX_SEC
        )
        between_batch_delay_range = _normalize_delay_range(
            config.PARSER_BATCH_DELAY_MIN_SEC,
            config.PARSER_BATCH_DELAY_MAX_SEC
        )
        all_posts = await parser.get_all_posts(
            config.TELEGRAM_CHANNELS,
            days=days,
            batch_size=config.PARSER_BATCH_SIZE,
            per_channel_delay_range=per_channel_delay_range,
            between_batch_delay_range=between_batch_delay_range
        )
        
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


async def update_posts_for_channels(channels, lookback_hours=10):
    """
    Run a single batch update for a provided channels list.

    Args:
        channels: Iterable of channel usernames/links
        lookback_hours: How many hours back to fetch posts
    """
    logger.info("=" * 50)
    logger.info(
        "Starting custom posts update (%s channels, last %s hours)",
        len(channels),
        lookback_hours
    )
    logger.info("=" * 50)

    normalized_channels = normalize_channel_usernames(channels)
    if not normalized_channels:
        logger.info("No valid channels provided for custom update")
        return {
            "channels_requested": len(channels),
            "channels_processed": 0,
            "posts_found": 0,
            "updated_count": 0,
            "appended_count": 0,
            "deleted_changes": 0,
            "flood_wait_seconds": 0
        }

    parser = None
    try:
        config.validate_config()

        parser = TelegramParser(
            config.TELEGRAM_API_ID,
            config.TELEGRAM_API_HASH,
            config.TELEGRAM_PHONE,
            session_name=config.TELEGRAM_SESSION_NAME
        )
        await parser.start()

        sheets = SheetsManager(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            config.GOOGLE_SHEET_ID
        )
        sheets.ensure_sheet_exists(config.POSTS_SHEET_NAME, config.POSTS_HEADERS)

        per_channel_delay_range = _normalize_delay_range(
            config.PARSER_CHANNEL_DELAY_MIN_SEC,
            config.PARSER_CHANNEL_DELAY_MAX_SEC
        )
        between_batch_delay_range = _normalize_delay_range(
            config.PARSER_BATCH_DELAY_MIN_SEC,
            config.PARSER_BATCH_DELAY_MAX_SEC
        )
        all_posts = await parser.get_all_posts(
            normalized_channels,
            hours=lookback_hours,
            batch_size=config.PARSER_BATCH_SIZE,
            per_channel_delay_range=per_channel_delay_range,
            between_batch_delay_range=between_batch_delay_range
        )

        updated_count, appended_count = sheets.append_posts(config.POSTS_SHEET_NAME, all_posts)
        active_links = {post['link'] for post in all_posts if post.get('link')}
        min_date = datetime.now() - timedelta(hours=lookback_hours + 2)
        deleted_changes = sheets.mark_deleted_posts(
            config.POSTS_SHEET_NAME,
            active_links,
            min_date=min_date
        )

        return {
            "channels_requested": len(channels),
            "channels_processed": len(normalized_channels),
            "posts_found": len(all_posts),
            "updated_count": updated_count,
            "appended_count": appended_count,
            "deleted_changes": deleted_changes,
            "flood_wait_seconds": parser.last_flood_wait_seconds
        }
    except Exception:
        logger.error("Error during custom channel update", exc_info=True)
        raise
    finally:
        if parser is not None:
            try:
                await parser.stop()
            except Exception:
                logger.warning("Failed to stop Telegram client cleanly", exc_info=True)


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

