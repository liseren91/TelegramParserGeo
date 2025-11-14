"""
Telegram Parser module
Handles all interactions with Telegram API using Telethon
"""
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, MessageMediaWebPage
from datetime import datetime, timedelta
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TelegramParser:
    def __init__(self, api_id, api_hash, phone):
        """
        Initialize Telegram client
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            phone: Phone number for authentication
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = TelegramClient('session', api_id, api_hash)
    
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
            
        except Exception as e:
            logger.error(f"Error getting info for channel {channel_username}: {e}")
            return {
                'name': channel_username,
                'username': channel_username,
                'link': f'https://t.me/{channel_username}',
                'subscribers': 0,
                'description': f'Error: {str(e)}',
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    async def get_recent_posts(self, channel_username, days=1):
        """
        Get recent posts from a channel
        
        Args:
            channel_username: Channel username (without @)
            days: Number of days to look back (default: 1)
            
        Returns:
            list: List of posts with all required information
        """
        try:
            channel = await self.client.get_entity(channel_username)
            
            # Calculate the date threshold
            date_threshold = datetime.now() - timedelta(days=days)
            
            posts = []
            async for message in self.client.iter_messages(channel, limit=100):
                # Stop if message is older than threshold
                if message.date < date_threshold:
                    break
                
                # Skip service messages
                if not message.message and not message.media:
                    continue
                
                # Check if message has media
                has_media = self._has_media(message)
                
                # Extract rubric (category) from message text or hashtags
                rubric = self._extract_rubric(message)
                
                # Get reactions (likes)
                likes = 0
                if hasattr(message, 'reactions') and message.reactions:
                    likes = sum(reaction.count for reaction in message.reactions.results)
                
                # Get comments count
                comments = 0
                if hasattr(message, 'replies') and message.replies:
                    comments = message.replies.replies if hasattr(message.replies, 'replies') else 0
                
                # Build post data
                post = {
                    'channel_name': channel.title,
                    'time': message.date.strftime('%H:%M:%S'),
                    'date': message.date.strftime('%Y-%m-%d'),
                    'rubric': rubric,
                    'content': message.message or '[Медиа без текста]',
                    'has_media': 'Да' if has_media else 'Нет',
                    'link': f'https://t.me/{channel_username}/{message.id}',
                    'views': message.views or 0,
                    'likes': likes,
                    'comments': comments
                }
                
                posts.append(post)
            
            logger.info(f"Retrieved {len(posts)} posts from {channel_username}")
            return posts
            
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
    
    def _extract_rubric(self, message):
        """Extract rubric/category from message"""
        if not message.message:
            return 'Без рубрики'
        
        # Look for hashtags
        hashtags = [word for word in message.message.split() if word.startswith('#')]
        if hashtags:
            return ', '.join(hashtags[:3])  # Return first 3 hashtags
        
        # If no hashtags, try to extract from first line
        first_line = message.message.split('\n')[0]
        if len(first_line) < 100:  # If first line is short, it might be a title/rubric
            return first_line
        
        return 'Без рубрики'
    
    async def get_all_channels_info(self, channels):
        """
        Get information for all channels
        
        Args:
            channels: List of channel usernames
            
        Returns:
            list: List of channel information dictionaries
        """
        all_info = []
        for channel in channels:
            info = await self.get_channel_info(channel)
            all_info.append(info)
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        return all_info
    
    async def get_all_posts(self, channels, days=1):
        """
        Get posts from all channels
        
        Args:
            channels: List of channel usernames
            days: Number of days to look back
            
        Returns:
            list: List of all posts from all channels
        """
        all_posts = []
        for channel in channels:
            posts = await self.get_recent_posts(channel, days)
            all_posts.extend(posts)
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        # Sort posts by date and time (newest first)
        all_posts.sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)
        
        return all_posts

