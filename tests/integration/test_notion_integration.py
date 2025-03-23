"""
NotionSync - Notion API Integration Tests

These tests use the actual Notion API to verify the integration functionality.
Requires a valid .env file with NOTION_API_KEY and either NOTION_PAGE_URL or NOTION_DATABASE_ID.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv
import re

from notionsync.core.sync import NotionSync
from notionsync.utils.helpers import load_env_variables

# Skip all tests if environment variables are not properly configured
pytestmark = pytest.mark.skipif(
    not (os.getenv("NOTION_API_KEY") and (os.getenv("NOTION_PAGE_URL") or os.getenv("NOTION_DATABASE_ID"))),
    reason="Notion API credentials not configured in .env file"
)

class TestNotionIntegration:
    """Integration tests with actual Notion API"""
    
    def setup_method(self):
        """Set up test environment"""
        # Load environment variables
        load_dotenv()
        
        # Get environment variables directly
        self.api_key = os.getenv("NOTION_API_KEY")
        self.page_url = os.getenv("NOTION_PAGE_URL")
        self.page_id = None
        
        if self.page_url:
            # クエリパラメータからページIDを抽出
            if "?p=" in self.page_url:
                self.page_id = self.page_url.split("?p=")[1].split("&")[0]
            else:
                # 従来の形式のURLからIDを抽出
                pattern = r"notion\.so/(?:[^/]+/)?([a-zA-Z0-9-]+)(?:\?|$)"
                match = re.search(pattern, self.page_url)
                if match:
                    self.page_id = match.group(1)
        
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a test config directory
        self.config_dir = Path(self.test_dir) / ".notionsync"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize NotionSync with real credentials but custom config directory
        self.notion_sync = NotionSync(
            api_key=self.api_key,
            page_id=self.page_id,
            database_id=self.database_id
        )
    
    def teardown_method(self):
        """Clean up after tests"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_connection(self):
        """Test basic connection to Notion API"""
        # Test if we can connect to Notion API
        if self.page_id:
            # Get page details to test connection
            page = self.notion_sync.notion_client.get_page(self.page_id)
            assert page is not None
            assert "id" in page
            assert page["id"]
        
        if self.database_id:
            # Query database to test connection
            result = self.notion_sync.notion_client.query_database(self.database_id)
            assert result is not None
            assert "results" in result
    
    def test_create_page_content(self):
        """Test creating a new page with content"""
        # Skip if no page_id is provided
        if not self.page_id:
            pytest.skip("No page_id configured in .env")
        
        # Create a test markdown file
        test_content = "# Test Page\n\nThis is a test page created by NotionSync integration tests."
        with open("test_integration.md", "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Create a simple commit
        commit_result = self.notion_sync.commit("Integration test commit")
        assert commit_result is not None
        
        # Push to Notion
        push_result = self.notion_sync.push()
        assert push_result is True
        
        # Verify the page was created (would need to check manually or implement a method to verify)
    
    def test_pull_page_content(self):
        """Test pulling content from Notion page"""
        # Skip if no page_id is provided
        if not self.page_id:
            pytest.skip("No page_id configured in .env")
        
        # Test pulling from Notion
        pull_result = self.notion_sync.pull()
        assert pull_result is True
        
        # Verify that index.md was created
        assert Path("index.md").exists()
        
        # Read the content to verify it matches what's in Notion
        with open("index.md", "r", encoding="utf-8") as f:
            content = f.read()
            assert "# " in content  # Should at least have a title
    
    @pytest.mark.skipif(not os.getenv("NOTION_DATABASE_ID"), reason="No database ID configured")
    def test_database_integration(self):
        """Test integration with Notion database"""
        # Skip if no database_id is provided
        if not self.database_id:
            pytest.skip("No database_id configured in .env")
        
        # Create a test markdown file with front matter
        test_content = """---
title: Integration Test Entry
tags: test, integration
priority: high
---

# Integration Test Entry

This is a test database entry created by NotionSync integration tests.
"""
        with open("test_db_entry.md", "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Create a simple commit
        commit_result = self.notion_sync.commit("Database integration test commit")
        assert commit_result is not None
        
        # Push to Notion database
        push_result = self.notion_sync.push()
        assert push_result is True
        
        # Pull from database to see if we can retrieve entries
        pull_result = self.notion_sync.pull()
        assert pull_result is True
        
        # Verify that database entries were pulled
        assert Path("notion_db").exists()
        assert any(Path("notion_db").glob("*.md")) 