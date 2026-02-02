"""
Google Drive & Sheets Integration Module
Handles authentication, file uploads, and sheet operations
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

def check_google_libraries():
    """Check if required Google libraries are installed"""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import gspread
        return True, None
    except ImportError as e:
        missing_lib = str(e).split("'")[1] if "'" in str(e) else "google libraries"
        return False, f"Missing: {missing_lib}"


def get_google_credentials():
    """Authenticate and get Google API credentials"""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request

        SCOPES = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/spreadsheets'
        ]

        creds = None
        token_path = 'token.json'
        creds_path = 'credentials.json'

        # Check if we have saved credentials
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    return None, "credentials.json not found. Please upload it first."

                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                # Try local server first, fall back to console flow if it fails
                try:
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Local server authentication failed: {e}")
                    print("Falling back to console authentication...")
                    creds = flow.run_console()

            # Save credentials for next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        return creds, None

    except Exception as e:
        return None, f"Authentication error: {str(e)}"


def upload_file_to_drive(file_path: str, folder_id: str, file_name: str = None) -> tuple:
    """
    Upload a file to Google Drive

    Returns: (file_url, error_message)
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds, error = get_google_credentials()
        if error:
            return None, error

        service = build('drive', 'v3', credentials=creds)

        # Use original filename if not specified
        if file_name is None:
            file_name = os.path.basename(file_path)

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        media = MediaFileUpload(file_path, resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        file_url = file.get('webViewLink')
        return file_url, None

    except Exception as e:
        return None, f"Upload error: {str(e)}"


def read_sheet_data(sheet_url: str, sheet_name: str = 'Sheet1') -> tuple:
    """
    Read data from Google Sheets

    Returns: (data_list, error_message)
    """
    try:
        import gspread
        import re

        creds, error = get_google_credentials()
        if error:
            return None, error

        # Extract sheet ID from URL
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            return None, "Invalid sheet URL format"

        sheet_id = match.group(1)

        # Open the sheet
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)

        # Get all records as list of dicts
        records = worksheet.get_all_records()

        return records, None

    except Exception as e:
        return None, f"Sheet read error: {str(e)}"


def update_sheet_row(sheet_url: str, row_number: int, updates: Dict, sheet_name: str = 'Sheet1') -> tuple:
    """
    Update a specific row in Google Sheets

    Args:
        sheet_url: Google Sheet URL
        row_number: Row number (1-indexed, including header)
        updates: Dict with column names and values to update
        sheet_name: Name of the worksheet

    Returns: (success, error_message)
    """
    try:
        import gspread
        import re

        creds, error = get_google_credentials()
        if error:
            return False, error

        # Extract sheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            return False, "Invalid sheet URL format"

        sheet_id = match.group(1)

        # Open the sheet
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)

        # Get header row to find column indices
        headers = worksheet.row_values(1)

        # Update each column
        for col_name, value in updates.items():
            if col_name in headers:
                col_index = headers.index(col_name) + 1  # 1-indexed
                worksheet.update_cell(row_number, col_index, value)

        return True, None

    except Exception as e:
        return False, f"Sheet update error: {str(e)}"


def batch_upload_to_drive(file_paths: List[str], folder_id: str, progress_callback=None) -> Dict:
    """
    Upload multiple files to Google Drive

    Returns: Dict with results {filename: url or error}
    """
    results = {}
    total = len(file_paths)

    for idx, file_path in enumerate(file_paths):
        file_name = os.path.basename(file_path)

        if progress_callback:
            progress_callback(idx + 1, total, file_name)

        url, error = upload_file_to_drive(file_path, folder_id, file_name)

        if error:
            results[file_name] = {'status': 'error', 'message': error}
        else:
            results[file_name] = {'status': 'success', 'url': url}

    return results


def get_pending_products(sheet_url: str, status_column: str = 'Status', pending_value: str = 'Pending') -> tuple:
    """
    Get products with 'Pending' status from sheet

    Returns: (products_list, error_message)
    """
    records, error = read_sheet_data(sheet_url)
    if error:
        return None, error

    # Filter for pending products
    pending_products = []
    for idx, record in enumerate(records):
        if record.get(status_column, '').strip().lower() == pending_value.lower():
            # Add row number (2-indexed: 1 for header, +1 for current)
            record['_row_number'] = idx + 2
            pending_products.append(record)

    return pending_products, None


def update_sheet_with_drive_links(sheet_url: str, product_name: str, drive_link: str,
                                    row_number: int = None, sheet_name: str = 'Sheet1') -> tuple:
    """
    Update Google Sheet with Drive link and completion status for a product

    Args:
        sheet_url: Google Sheet URL
        product_name: Name of the product to update
        drive_link: Google Drive link to the generated ad
        row_number: Specific row number to update (if known)
        sheet_name: Name of the worksheet

    Returns: (success, error_message)
    """
    try:
        from datetime import datetime

        # Prepare updates
        updates = {
            'Ad URL': drive_link,
            'Status': 'Complete',
            'Generated At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # If row number provided, use it directly
        if row_number:
            success, error = update_sheet_row(sheet_url, row_number, updates, sheet_name)
            return success, error

        # Otherwise, find the row by product name
        import gspread
        import re

        creds, error = get_google_credentials()
        if error:
            return False, error

        # Extract sheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            return False, "Invalid sheet URL format"

        sheet_id = match.group(1)

        # Open the sheet
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)

        # Find the product row
        records = worksheet.get_all_records()
        for idx, record in enumerate(records):
            if record.get('Product Name', '').strip() == product_name.strip():
                row_num = idx + 2  # +2 for header and 1-indexed
                success, error = update_sheet_row(sheet_url, row_num, updates, sheet_name)
                return success, error

        return False, f"Product '{product_name}' not found in sheet"

    except Exception as e:
        return False, f"Sheet update error: {str(e)}"


def batch_update_sheet_with_links(sheet_url: str, products_with_links: List[Dict],
                                   sheet_name: str = 'Sheet1') -> Dict:
    """
    Batch update Google Sheet with Drive links for multiple products

    Args:
        sheet_url: Google Sheet URL
        products_with_links: List of dicts with 'product_name', 'drive_link', and optional 'row_number'
        sheet_name: Name of the worksheet

    Returns: Dict with 'succeeded', 'failed', and 'errors'
    """
    results = {
        'succeeded': 0,
        'failed': 0,
        'errors': []
    }

    for product_info in products_with_links:
        product_name = product_info.get('product_name', '')
        drive_link = product_info.get('drive_link', '')
        row_number = product_info.get('row_number')

        success, error = update_sheet_with_drive_links(
            sheet_url,
            product_name,
            drive_link,
            row_number,
            sheet_name
        )

        if success:
            results['succeeded'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"{product_name}: {error}")

    return results


def append_ads_to_sheet(sheet_url: str, ads_data: List[Dict], sheet_name: str = 'Sheet1') -> Dict:
    """
    Append generated ads with Drive links to Google Sheet (adds new rows)

    Args:
        sheet_url: Google Sheet URL
        ads_data: List of dicts with 'product_name', 'drive_link', 'size', 'generated_at'
        sheet_name: Name of the worksheet

    Returns: Dict with 'succeeded', 'failed', and 'errors'
    """
    try:
        import gspread
        import re
        from datetime import datetime

        creds, error = get_google_credentials()
        if error:
            return {'succeeded': 0, 'failed': len(ads_data), 'errors': [error]}

        # Extract sheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            return {'succeeded': 0, 'failed': len(ads_data), 'errors': ["Invalid sheet URL format"]}

        sheet_id = match.group(1)

        # Open the sheet
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)

        # Try to get the specified worksheet, or use first available sheet
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except:
            # Sheet doesn't exist, try to get first sheet or create one
            try:
                worksheet = spreadsheet.get_worksheet(0)  # Get first sheet
                if worksheet is None:
                    # No sheets exist, create one
                    worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=10)
            except:
                # Create a new sheet
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=10)

        # Check if sheet has headers, if empty add them
        try:
            headers = worksheet.row_values(1)
            if not headers or len(headers) == 0:
                # Add headers
                headers = ['Product Name', 'Ad Size', 'Generated At', 'Status', 'Ad URL']
                worksheet.append_row(headers)
        except:
            # Sheet is empty, add headers
            headers = ['Product Name', 'Ad Size', 'Generated At', 'Status', 'Ad URL']
            worksheet.append_row(headers)

        # Prepare rows to append
        results = {
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }

        for ad_info in ads_data:
            try:
                product_name = ad_info.get('product_name', 'Unknown Product')
                ad_size = ad_info.get('size', 'Unknown Size')
                drive_link = ad_info.get('drive_link', '')
                generated_at = ad_info.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

                # Append row
                row = [product_name, ad_size, generated_at, 'Complete', drive_link]
                worksheet.append_row(row)
                results['succeeded'] += 1

            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{product_name}: {str(e)}")

        return results

    except Exception as e:
        error_msg = f"Sheet append error: {str(e)}"
        # Add more context for common errors
        if "not found" in str(e).lower():
            error_msg += "\nHint: Make sure the Google Sheet exists and you have edit permissions."
        elif "permission" in str(e).lower():
            error_msg += "\nHint: Check that you have edit access to this Google Sheet."
        return {
            'succeeded': 0,
            'failed': len(ads_data),
            'errors': [error_msg]
        }


def get_worksheet_names(sheet_url: str) -> tuple:
    """
    Get all worksheet/tab names from a Google Spreadsheet

    Args:
        sheet_url: Google Sheet URL

    Returns: (list of worksheet names, error_message)
    """
    try:
        import gspread
        import re

        creds, error = get_google_credentials()
        if error:
            return None, error

        # Extract sheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            return None, "Invalid sheet URL format"

        sheet_id = match.group(1)

        # Open the sheet
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)

        # Get all worksheet names
        worksheets = spreadsheet.worksheets()
        worksheet_names = [ws.title for ws in worksheets]

        return worksheet_names, None

    except Exception as e:
        return None, f"Error getting worksheets: {str(e)}"


def get_worksheet_headers(sheet_url: str, sheet_name: str) -> tuple:
    """
    Get existing column headers from a specific worksheet

    Args:
        sheet_url: Google Sheet URL
        sheet_name: Name of the worksheet

    Returns: (list of header names, error_message)
    """
    try:
        import gspread
        import re

        creds, error = get_google_credentials()
        if error:
            return None, error

        # Extract sheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            return None, "Invalid sheet URL format"

        sheet_id = match.group(1)

        # Open the sheet
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)

        # Get headers from first row
        try:
            headers = worksheet.row_values(1)
            # Filter out empty headers
            headers = [h for h in headers if h.strip()]
            return headers, None
        except:
            # Sheet is empty or has no headers
            return [], None

    except Exception as e:
        return None, f"Error getting headers: {str(e)}"


def append_ads_to_sheet_custom(sheet_url: str, ads_data: List[Dict],
                                sheet_name: str = 'Sheet1',
                                column_mapping: Dict = None,
                                enabled_columns: List[str] = None) -> Dict:
    """
    Append ads to sheet with custom column mapping and selective columns

    Args:
        sheet_url: Google Sheet URL
        ads_data: List of dicts with ad data
        sheet_name: Specific worksheet name to use
        column_mapping: Dict mapping internal keys to custom column names
                       e.g., {'product_name': 'Product', 'size': 'Dimensions', ...}
        enabled_columns: List of column keys to include (e.g., ['product_name', 'size', 'drive_link'])

    Returns: Dict with 'succeeded', 'failed', and 'errors'
    """
    try:
        import gspread
        import re
        from datetime import datetime

        # Default column mapping if none provided
        if column_mapping is None:
            column_mapping = {
                'product_name': 'Product Name',
                'size': 'Ad Size',
                'generated_at': 'Generated At',
                'status': 'Status',
                'drive_link': 'Ad URL'
            }

        # Default enabled columns if none provided (all columns)
        if enabled_columns is None:
            enabled_columns = ['product_name', 'size', 'generated_at', 'status', 'drive_link']

        creds, error = get_google_credentials()
        if error:
            return {'succeeded': 0, 'failed': len(ads_data), 'errors': [error]}

        # Extract sheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            return {'succeeded': 0, 'failed': len(ads_data), 'errors': ["Invalid sheet URL format"]}

        sheet_id = match.group(1)

        # Open the specific worksheet by name
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)

        # Build headers list based on enabled columns
        headers = []
        for col_key in enabled_columns:
            headers.append(column_mapping.get(col_key, col_key))

        # Check if sheet has headers, if empty add them
        try:
            existing_headers = worksheet.row_values(1)
            if not existing_headers or len(existing_headers) == 0:
                worksheet.append_row(headers)
        except:
            # Sheet is empty, add headers
            worksheet.append_row(headers)

        # Prepare rows to append
        results = {
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }

        for ad_info in ads_data:
            try:
                # Build row based on enabled columns
                row = []
                for col_key in enabled_columns:
                    if col_key == 'product_name':
                        row.append(ad_info.get('product_name', 'Unknown Product'))
                    elif col_key == 'size':
                        row.append(ad_info.get('size', 'Unknown Size'))
                    elif col_key == 'drive_link':
                        row.append(ad_info.get('drive_link', ''))
                    elif col_key == 'generated_at':
                        row.append(ad_info.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    elif col_key == 'status':
                        row.append('Complete')
                    else:
                        row.append('')  # Unknown column type

                worksheet.append_row(row)
                results['succeeded'] += 1

            except Exception as e:
                results['failed'] += 1
                product_name = ad_info.get('product_name', 'Unknown')
                results['errors'].append(f"{product_name}: {str(e)}")

        return results

    except Exception as e:
        error_msg = f"Sheet append error: {str(e)}"
        if "not found" in str(e).lower():
            error_msg += f"\nHint: Worksheet '{sheet_name}' not found. Check the tab name."
        elif "permission" in str(e).lower():
            error_msg += "\nHint: Check that you have edit access to this Google Sheet."
        return {
            'succeeded': 0,
            'failed': len(ads_data),
            'errors': [error_msg]
        }
