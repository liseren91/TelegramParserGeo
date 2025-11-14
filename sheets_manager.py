"""
Google Sheets Manager module
Handles all interactions with Google Sheets API
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SheetsManager:
    def __init__(self, service_account_file, spreadsheet_id):
        """
        Initialize Google Sheets client
        
        Args:
            service_account_file: Path to service account JSON file
            spreadsheet_id: Google Spreadsheet ID
        """
        self.spreadsheet_id = spreadsheet_id
        
        # Define the scopes
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Authenticate and create client
        creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        
        logger.info(f"Connected to Google Spreadsheet: {self.spreadsheet.title}")
    
    def ensure_sheet_exists(self, sheet_name, headers):
        """
        Ensure a worksheet exists with proper headers
        
        Args:
            sheet_name: Name of the worksheet
            headers: List of column headers
        """
        try:
            # Try to get existing sheet
            worksheet = self.spreadsheet.worksheet(sheet_name)
            logger.info(f"Sheet '{sheet_name}' already exists")
            
            # Check if headers need to be updated
            existing_headers = worksheet.row_values(1)
            if not existing_headers or existing_headers != headers:
                worksheet.update('A1:' + self._col_letter(len(headers)) + '1', [headers])
                logger.info(f"Updated headers for sheet '{sheet_name}'")
                
        except gspread.exceptions.WorksheetNotFound:
            # Create new sheet
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
            worksheet.update('A1:' + self._col_letter(len(headers)) + '1', [headers])
            logger.info(f"Created new sheet '{sheet_name}' with headers")
        
        return worksheet
    
    def _col_letter(self, n):
        """Convert column number to letter (1->A, 2->B, etc.)"""
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string
    
    def update_channels_info(self, sheet_name, channels_data):
        """
        Update channels information sheet
        
        Args:
            sheet_name: Name of the worksheet
            channels_data: List of dictionaries with channel information
        """
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            
            # Prepare data rows
            rows = []
            for channel in channels_data:
                row = [
                    channel.get('name', ''),
                    channel.get('link', ''),
                    channel.get('subscribers', 0),
                    channel.get('description', ''),
                    channel.get('updated_at', '')
                ]
                rows.append(row)
            
            # Clear existing data (except headers)
            worksheet.delete_rows(2, worksheet.row_count)
            
            # Update with new data
            if rows:
                worksheet.append_rows(rows, value_input_option='USER_ENTERED')
                logger.info(f"Updated {len(rows)} channels in '{sheet_name}'")
            
        except Exception as e:
            logger.error(f"Error updating channels info: {e}")
            raise
    
    def append_posts(self, sheet_name, posts_data):
        """
        Append posts to the posts sheet
        
        Args:
            sheet_name: Name of the worksheet
            posts_data: List of dictionaries with post information
        """
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            
            # Prepare data rows
            rows = []
            for post in posts_data:
                row = [
                    post.get('channel_name', ''),
                    post.get('time', ''),
                    post.get('date', ''),
                    post.get('rubric', ''),
                    post.get('content', ''),
                    post.get('has_media', 'Нет'),
                    post.get('link', ''),
                    post.get('views', 0),
                    post.get('likes', 0),
                    post.get('comments', 0)
                ]
                rows.append(row)
            
            # Append rows
            if rows:
                worksheet.append_rows(rows, value_input_option='USER_ENTERED')
                logger.info(f"Appended {len(rows)} posts to '{sheet_name}'")
            
        except Exception as e:
            logger.error(f"Error appending posts: {e}")
            raise
    
    def clear_old_posts(self, sheet_name, days_to_keep=30):
        """
        Clear posts older than specified days
        
        Args:
            sheet_name: Name of the worksheet
            days_to_keep: Number of days to keep (default: 30)
        """
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            
            # Get all data
            all_data = worksheet.get_all_values()
            
            if len(all_data) <= 1:  # Only headers or empty
                return
            
            headers = all_data[0]
            date_col_index = headers.index('Дата публикации') if 'Дата публикации' in headers else 2
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            # Find rows to keep
            rows_to_keep = [headers]
            for row in all_data[1:]:
                if len(row) > date_col_index:
                    post_date = row[date_col_index]
                    if post_date >= cutoff_str:
                        rows_to_keep.append(row)
            
            # Update sheet if rows were removed
            if len(rows_to_keep) < len(all_data):
                worksheet.clear()
                worksheet.update('A1', rows_to_keep, value_input_option='USER_ENTERED')
                logger.info(f"Cleaned old posts from '{sheet_name}', kept {len(rows_to_keep)-1} rows")
            
        except Exception as e:
            logger.error(f"Error clearing old posts: {e}")
            # Non-critical error, continue
    
    def get_existing_post_links(self, sheet_name):
        """
        Get set of existing post links to avoid duplicates
        
        Args:
            sheet_name: Name of the worksheet
            
        Returns:
            set: Set of existing post links
        """
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            all_data = worksheet.get_all_values()
            
            if len(all_data) <= 1:
                return set()
            
            headers = all_data[0]
            link_col_index = headers.index('Ссылка на пост') if 'Ссылка на пост' in headers else 6
            
            links = set()
            for row in all_data[1:]:
                if len(row) > link_col_index and row[link_col_index]:
                    links.add(row[link_col_index])
            
            return links
            
        except Exception as e:
            logger.error(f"Error getting existing posts: {e}")
            return set()

