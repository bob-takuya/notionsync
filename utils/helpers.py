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
    
    # Get API key
    api_key = os.getenv("NOTION_API_KEY")
    
    # Get page ID from URL if available
    page_id = None
    page_url = os.getenv("NOTION_PAGE_URL")
    if page_url:
        # Extract page ID from URL
        pattern = r"notion\.so/(?:[^/]+/)?([a-zA-Z0-9]+)"
        match = re.search(pattern, page_url)
        if match:
            page_id = match.group(1)
    
    # Get database ID if available
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    return {
        "api_key": api_key,
        "page_id": page_id,
        "database_id": database_id
    }

def extract_front_matter(content):
    """Extract front matter from markdown content
    
    Args:
        content (str): Markdown content
        
    Returns:
        tuple: (front_matter, content) where front_matter is a dict and content is the rest of the markdown
    """
    front_matter = {}
    markdown_content = content
    
    # Check for front matter between --- delimiters
    front_matter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    front_matter_match = re.search(front_matter_pattern, content, re.DOTALL)
    
    if front_matter_match:
        # Extract front matter
        front_matter_str = front_matter_match.group(1)
        
        # Parse front matter (simple key: value format)
        for line in front_matter_str.split("\n"):
            line = line.strip()
            if line and ":" in line:
                key, value = line.split(":", 1)
                front_matter[key.strip()] = value.strip()
        
        # Extract content after front matter
        markdown_content = content[front_matter_match.end():]
    
    return front_matter, markdown_content

def get_file_changes(last_commit_files, current_files):
    """Compare last commit files to current files
    
    Args:
        last_commit_files (dict): Dictionary of file paths to content from last commit
        current_files (list): List of Path objects for current markdown files
        
    Returns:
        dict: Dictionary with lists of added, modified, and deleted files
    """
    # Convert current_files to a list of strings
    current_paths = [str(f) for f in current_files]
    
    # Find added files (in current but not in last commit)
    added = [f for f in current_paths if f not in last_commit_files]
    
    # Find deleted files (in last commit but not in current)
    deleted = [f for f in last_commit_files if f not in current_paths]
    
    # Find modified files (in both but with different content)
    modified = []
    for file_path in current_paths:
        if file_path in last_commit_files:
            # Read current file content
            with open(file_path, "r", encoding="utf-8") as f:
                current_content = f.read()
            
            # Compare with last commit content
            if current_content != last_commit_files[file_path]:
                modified.append(file_path)
    
    return {
        "added": added,
        "modified": modified,
        "deleted": deleted
    } 