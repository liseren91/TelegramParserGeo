"""
Telegram Parser module
Handles all interactions with Telegram API using Telethon
"""
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UsernameInvalidError, UsernameNotOccupiedError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaWebPage,
    ReactionEmoji,
    ReactionCustomEmoji
)
from datetime import datetime, timedelta, timezone
import logging
import asyncio
import random

from flood_tracker import record_flood_wait

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TelegramParser:
    def __init__(self, api_id, api_hash, phone, session_name='session'):
        """
        Initialize Telegram client
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            phone: Phone number for authentication
            session_name: Session storage name/path (without .session)
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_name = session_name
        self.client = TelegramClient(self.session_name, api_id, api_hash)
        self.last_flood_wait_seconds = 0
    
    def _build_error_channel_info(self, channel_username, message):
        """Build fallback channel info payload for failed requests."""
        return {
            'name': channel_username,
            'username': channel_username,
            'link': f'https://t.me/{channel_username}',
            'subscribers': 0,
            'description': message,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    async def start(self):
        """Start the Telegram client"""
        await self.client.start(phone=self.phone)
        logger.info("Telegram client started successfully")
    
    async def stop(self):
        """Stop the Telegram client"""
        await self.client.disconnect()
        logger.info("Telegram client stopped")
    
    async def get_channel_info(self, channel_username):
        """
        Get channel information
        
        Args:
            channel_username: Channel username (without @)
            
        Returns:
            dict: Channel information including subscribers and description
        """
        try:
            # Get the channel entity
            channel = await self.client.get_entity(channel_username)
            
            # Get full channel info
            full_channel = await self.client(GetFullChannelRequest(channel))
            
            # Extract information
            info = {
                'name': channel.title,
                'username': channel_username,
                'link': f'https://t.me/{channel_username}',
                'subscribers': full_channel.full_chat.participants_count if hasattr(full_channel.full_chat, 'participants_count') else 0,
                'description': full_channel.full_chat.about or '',
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"Retrieved info for channel: {channel_username}")
            return info
            
        except FloodWaitError:
            # Let the caller decide how to handle global throttling.
            raise
        except (UsernameInvalidError, UsernameNotOccupiedError) as e:
            logger.warning(f"Channel {channel_username} is invalid or unavailable: {e}")
            return self._build_error_channel_info(channel_username, f'Channel unavailable: {str(e)}')
        except Exception as e:
            logger.error(f"Error getting info for channel {channel_username}: {e}")
            return self._build_error_channel_info(channel_username, f'Error: {str(e)}')
    
    async def get_recent_posts(self, channel_username, days=1, hours=None):
        """
        Get recent posts from a channel
        
        Args:
            channel_username: Channel username (without @)
            days: Number of days to look back (default: 1)
            hours: Number of hours to look back (overrides days when set)
            
        Returns:
            list: List of posts with all required information
        """
        try:
            channel = await self.client.get_entity(channel_username)
            
            # Calculate the date threshold (timezone-aware to match Telegram timestamps)
            if hours is not None:
                date_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
            else:
                date_threshold = datetime.now(timezone.utc) - timedelta(days=days)
            
            collected_messages = []
            async for message in self.client.iter_messages(channel, limit=100):
                message_date = self._normalize_message_date(message.date)

                if message_date < date_threshold:
                    break
                
                # Skip service messages (no text and no media)
                if not message.message and not message.media:
                    continue

                collected_messages.append((message, message_date))

            group_captions = self._build_group_caption_map(collected_messages)
            message_metrics, group_metrics = self._build_group_metrics(collected_messages)

            posts = []
            for message, message_date in collected_messages:
                grouped_id = getattr(message, 'grouped_id', None)

                # Check if message has media
                has_media = self._has_media(message)
                
                # Determine content with grouped media support
                content_text = self._get_message_content(message, group_captions)
                
                # Extract rubric (category) from message text or fallback content
                rubric = self._extract_rubric(message, fallback_text=content_text)

                metrics = message_metrics.get(message.id, {
                    'likes': 0,
                    'reactions_detail': '',
                    'comments': 0
                })
                likes = metrics['likes']
                reactions_detail = metrics['reactions_detail']
                comments = metrics['comments']

                if grouped_id and grouped_id in group_metrics:
                    group_data = group_metrics[grouped_id]
                    likes = group_data['likes']
                    reactions_detail = group_data['reactions_detail']
                    comments = max(comments, group_data['comments'])
                
                # Build post data
                post = {
                    'channel_name': channel.title,
                    'time': message_date.strftime('%H:%M:%S'),
                    'date': message_date.strftime('%Y-%m-%d'),
                    'rubric': rubric,
                    'content': content_text,
                    'has_media': 'Да' if has_media else 'Нет',
                    'link': f'https://t.me/{channel_username}/{message.id}',
                    'views': message.views or 0,
                    'likes': likes,
                    'reactions_detail': reactions_detail,
                    'comments': comments
                }
                
                posts.append(post)
            
            logger.info(f"Retrieved {len(posts)} posts from {channel_username}")
            return posts
            
        except FloodWaitError:
            # Let caller handle global throttling strategy.
            raise
        except Exception as e:
            logger.error(f"Error getting posts from channel {channel_username}: {e}")
            return []
    
    def _has_media(self, message):
        """Check if message has media"""
        if not message.media:
            return False
        
        # Check for various media types
        media_types = (MessageMediaPhoto, MessageMediaDocument)
        return isinstance(message.media, media_types)
    
    def _extract_rubric(self, message, fallback_text=None):
        """Extract rubric/category from message"""
        text_source = message.message or fallback_text
        if not text_source:
            return 'Без рубрики'
        
        # Look for hashtags
        hashtags = [word for word in text_source.split() if word.startswith('#')]
        if hashtags:
            return ', '.join(hashtags[:3])  # Return first 3 hashtags
        
        # If no hashtags, try to extract from first line
        first_line = text_source.split('\n')[0]
        if len(first_line) < 100:  # If first line is short, it might be a title/rubric
            return first_line
        
        return 'Без рубрики'
    
    def _parse_reactions(self, message):
        """Calculate total reactions and build details string"""
        reactions = getattr(message, 'reactions', None)
        if not reactions or not getattr(reactions, 'results', None):
            return 0, ''

        total = 0
        details = []
        for result in reactions.results:
            count = getattr(result, 'count', 0) or 0
            reaction_obj = getattr(result, 'reaction', None)
            label = self._format_reaction_label(reaction_obj)

            if count:
                total += count

            if label:
                details.append(f"{label}: {count}")

        return total, ', '.join(details)

    def _format_reaction_label(self, reaction):
        """Format reaction object to human-friendly label"""
        if not reaction:
            return ''

        emoticon = getattr(reaction, 'emoticon', None)
        if emoticon:
            return emoticon

        # Custom emoji reactions have document_id
        document_id = getattr(reaction, 'document_id', None)
        if document_id:
            return f'custom_{document_id}'

        # Fallback to class name
        return reaction.__class__.__name__

    def _get_comments_count(self, message):
        """Extract comments count from message replies"""
        replies = getattr(message, 'replies', None)
        if not replies:
            return 0

        replies_count = getattr(replies, 'replies', None)
        if isinstance(replies_count, int):
            return max(replies_count, 0)

        comments_count = getattr(replies, 'comments', None)
        if isinstance(comments_count, int):
            return max(comments_count, 0)

        return 0

    def _normalize_message_date(self, message_date):
        """Normalize message date to timezone-aware datetime"""
        if isinstance(message_date, datetime):
            if message_date.tzinfo is None:
                return message_date.replace(tzinfo=timezone.utc)
            return message_date
        return datetime.now(timezone.utc)

    def _build_group_caption_map(self, collected_messages):
        """Build map of grouped_id -> caption text"""
        captions = {}
        for message, _ in collected_messages:
            grouped_id = getattr(message, 'grouped_id', None)
            text = (message.message or '').strip()
            if grouped_id and text and grouped_id not in captions:
                captions[grouped_id] = message.message
        return captions

    def _get_message_content(self, message, group_captions):
        """Return message content considering grouped media captions"""
        if message.message:
            return message.message
        
        grouped_id = getattr(message, 'grouped_id', None)
        if grouped_id and grouped_id in group_captions:
            return group_captions[grouped_id]
        
        if message.media:
            return '[Медиа без текста]'
        
        return ''

    def _build_group_metrics(self, collected_messages):
        """Build per-message metrics cache and grouped media aggregates"""
        message_metrics = {}
        group_metrics = {}

        for message, _ in collected_messages:
            likes, reactions_detail = self._parse_reactions(message)
            comments = self._get_comments_count(message)

            message_metrics[message.id] = {
                'likes': likes,
                'reactions_detail': reactions_detail,
                'comments': comments
            }

            grouped_id = getattr(message, 'grouped_id', None)
            if not grouped_id:
                continue

            if likes == 0 and comments == 0 and not reactions_detail:
                continue

            current = group_metrics.get(grouped_id)
            should_replace = (
                current is None
                or likes > current['likes']
                or comments > current['comments']
                or (likes == current['likes'] and comments == current['comments']
                    and reactions_detail and not current['reactions_detail'])
            )

            if should_replace:
                group_metrics[grouped_id] = {
                    'likes': likes,
                    'reactions_detail': reactions_detail,
                    'comments': comments
                }

        return message_metrics, group_metrics

    async def get_all_channels_info(self, channels):
        """
        Get information for all channels
        
        Args:
            channels: List of channel usernames
            
        Returns:
            list: List of channel information dictionaries
        """
        all_info = []
        flood_wait_seconds = None

        for idx, channel in enumerate(channels):
            if flood_wait_seconds is not None:
                all_info.append(
                    self._build_error_channel_info(
                        channel,
                        f'Skipped due to Telegram FloodWait ({flood_wait_seconds}s)'
                    )
                )
                continue

            try:
                info = await self.get_channel_info(channel)
            except FloodWaitError as e:
                flood_wait_seconds = getattr(e, 'seconds', None) or 0
                record_flood_wait(flood_wait_seconds)
                remaining = len(channels) - idx - 1
                logger.error(
                    "Telegram FloodWait while resolving '%s': %ss. "
                    "Skipping remaining %s channels in this run.",
                    channel,
                    flood_wait_seconds,
                    remaining
                )
                info = self._build_error_channel_info(
                    channel,
                    f'FloodWait: need to wait {flood_wait_seconds}s'
                )

            all_info.append(info)
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        return all_info
    
    async def get_all_posts(
        self,
        channels,
        days=1,
        hours=None,
        batch_size=0,
        per_channel_delay_range=(1, 1),
        between_batch_delay_range=(0, 0)
    ):
        """
        Get posts from all channels
        
        Args:
            channels: List of channel usernames
            days: Number of days to look back
            hours: Number of hours to look back (overrides days when set)
            
        Returns:
            list: List of all posts from all channels
        """
        all_posts = []
        self.last_flood_wait_seconds = 0
        channels_list = list(channels)

        if batch_size <= 0:
            batch_size = len(channels_list) or 1

        min_delay, max_delay = per_channel_delay_range
        if min_delay > max_delay:
            min_delay, max_delay = max_delay, min_delay

        batch_min_delay, batch_max_delay = between_batch_delay_range
        if batch_min_delay > batch_max_delay:
            batch_min_delay, batch_max_delay = batch_max_delay, batch_min_delay

        for batch_start in range(0, len(channels_list), batch_size):
            batch = channels_list[batch_start:batch_start + batch_size]

            for channel in batch:
                try:
                    posts = await self.get_recent_posts(channel, days=days, hours=hours)
                except FloodWaitError as e:
                    self.last_flood_wait_seconds = getattr(e, 'seconds', None) or 0
                    record_flood_wait(self.last_flood_wait_seconds)
                    logger.error(
                        "Telegram FloodWait while fetching posts for '%s': %ss. "
                        "Stopping current run.",
                        channel,
                        self.last_flood_wait_seconds
                    )
                    return all_posts

                all_posts.extend(posts)

                if max_delay > 0:
                    await asyncio.sleep(random.uniform(min_delay, max_delay))

            is_last_batch = (batch_start + batch_size) >= len(channels_list)
            if not is_last_batch and batch_max_delay > 0:
                await asyncio.sleep(random.uniform(batch_min_delay, batch_max_delay))
        
        # Sort posts by date and time (newest first)
        all_posts.sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)
        
        return all_posts

