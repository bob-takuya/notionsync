"""
NotionSync - Helper Utilities

This module provides utility functions for NotionSync.
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

def load_env_variables():
    """Load environment variables from .env file"""
    load_dotenv()
    
    # Get Notion API configuration
    api_key = os.getenv("NOTION_API_KEY")
    page_url = os.getenv("NOTION_PAGE_URL")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    # Extract page ID from URL if it exists
    page_id = None
    if page_url:
        try:
            if "?p=" in page_url:
                # Extract the page ID from a URL with query parameters
                page_id_raw = page_url.split("?p=")[1].split("&")[0]
                # Remove any dashes from the ID
                page_id = page_id_raw.replace("-", "")
            elif "/so/" in page_url:
                # Traditional Notion URL format
                parts = page_url.split("/")
                # The last part should be the page ID
                page_id_raw = parts[-1]
                # Check if it has dashes
                if "-" in page_id_raw:
                    page_id = page_id_raw.replace("-", "")
                else:
                    page_id = page_id_raw
        except Exception as e:
            print(f"Error extracting page ID from URL: {e}")
    
    return {
        "api_key": api_key,
        "page_url": page_url,
        "page_id": page_id,
        "database_id": database_id
    }

def extract_front_matter(markdown_content):
    """Extract front matter from markdown content"""
    front_matter = {}
    content = markdown_content
    
    # Check if the content starts with '---'
    if markdown_content.startswith('---'):
        # Find the second '---'
        second_marker = markdown_content[3:].find('---')
        if second_marker != -1:
            # Extract front matter content
            front_matter_content = markdown_content[3:second_marker+3].strip()
            
            # Parse front matter content
            for line in front_matter_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    front_matter[key.strip()] = value.strip()
            
            # Extract remaining content
            content = markdown_content[second_marker+6:].strip()
    
    return front_matter, content

def get_file_changes(last_commit_files, current_files):
    """Get changes between the last commit and current files"""
    changes = {
        "added": [],
        "modified": [],
        "deleted": []
    }
    
    # Convert current files to a dictionary for easier comparison
    current_files_dict = {str(f): f for f in current_files}
    
    # Find added and modified files
    for file_path in current_files_dict:
        if file_path not in last_commit_files:
            changes["added"].append(file_path)
        else:
            # Check if content has changed
            with open(file_path, "r", encoding="utf-8") as f:
                current_content = f.read()
            
            if current_content != last_commit_files[file_path]:
                changes["modified"].append(file_path)
    
    # Find deleted files
    for file_path in last_commit_files:
        if file_path not in current_files_dict:
            changes["deleted"].append(file_path)
    
    return changes 