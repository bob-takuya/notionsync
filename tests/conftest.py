"""
NotionSync - pytest configuration

This module contains pytest fixtures and configuration for NotionSync tests.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    os.chdir(test_dir)
    
    yield test_dir
    
    os.chdir(original_dir)
    shutil.rmtree(test_dir)

@pytest.fixture
def mock_notion_client():
    """Create a mocked Notion client"""
    with patch('notionsync.core.notion_client.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Setup common mock responses
        mock_instance.pages.retrieve.return_value = {"id": "test_page_id", "properties": {}}
        mock_instance.pages.update.return_value = {"id": "test_page_id"}
        mock_instance.blocks.children.append.return_value = {"results": []}
        
        yield mock_instance

@pytest.fixture
def setup_env_vars():
    """Setup environment variables for testing"""
    original_vars = {}
    test_vars = {
        "NOTION_API_KEY": "test_api_key",
        "NOTION_PAGE_URL": "https://www.notion.so/test-page-123456",
        "NOTION_DATABASE_ID": "test_db_id"
    }
    
    # Save original variables
    for key in test_vars:
        if key in os.environ:
            original_vars[key] = os.environ[key]
    
    # Set test variables
    for key, value in test_vars.items():
        os.environ[key] = value
    
    yield
    
    # Restore original variables
    for key in test_vars:
        if key in original_vars:
            os.environ[key] = original_vars[key]
        else:
            del os.environ[key] 