"""
NotionSync - Notion API Client Tests

This module contains tests for the Notion API client functionality.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

from notionsync.core.notion_client import NotionApiClient

class TestNotionApiClient:
    """Test the Notion API client functionality"""
    
    @patch.dict(os.environ, {"NOTION_API_KEY": "test_api_key"})
    def test_init_with_env_var(self):
        """Test initialization with environment variable"""
        client = NotionApiClient()
        assert client.api_key == "test_api_key"
    
    def test_init_with_params(self):
        """Test initialization with parameters"""
        client = NotionApiClient(api_key="test_api_key", page_id="test_page_id", database_id="test_db_id")
        assert client.api_key == "test_api_key"
        assert client.page_id == "test_page_id"
        assert client.database_id == "test_db_id"
    
    def test_init_without_api_key(self):
        """Test initialization without API key"""
        with pytest.raises(ValueError):
            NotionApiClient(api_key=None)
    
    @patch('notionsync.core.notion_client.Client')
    def test_get_page(self, mock_client):
        """Test get_page method"""
        # Setup mock
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.pages.retrieve.return_value = {"id": "test_page_id", "properties": {}}
        
        # Test
        client = NotionApiClient(api_key="test_api_key")
        result = client.get_page("test_page_id")
        
        # Assertions
        mock_instance.pages.retrieve.assert_called_once_with(page_id="test_page_id")
        assert result["id"] == "test_page_id"
    
    @patch('notionsync.core.notion_client.Client')
    def test_update_page(self, mock_client):
        """Test update_page method"""
        # Setup mock
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Test
        client = NotionApiClient(api_key="test_api_key")
        properties = {"title": {"text": [{"content": "New Title"}]}}
        content = [{"type": "paragraph", "paragraph": {"text": [{"content": "New content"}]}}]
        
        result = client.update_page("test_page_id", properties, content)
        
        # Assertions
        mock_instance.pages.update.assert_called_once_with(page_id="test_page_id", properties=properties)
        mock_instance.blocks.children.append.assert_called_once_with(
            block_id="test_page_id",
            children=content
        )
        assert result is True
    
    # Additional tests can be added here for other methods 