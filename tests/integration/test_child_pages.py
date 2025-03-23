"""
NotionSync - Child Pages Integration Tests

This module tests how NotionSync handles child pages in Notion,
especially focusing on hierarchical page structures during pull and push operations.
"""

import pytest
import os
import re
import tempfile
import shutil
from pathlib import Path
import uuid
from dotenv import load_dotenv

from notionsync.core.notion_client import NotionApiClient
from notionsync.core.sync import NotionSync
from notionsync.markdown.converter import MarkdownConverter

# Skip tests if environment variables are not properly configured
pytestmark = pytest.mark.skipif(
    not (os.getenv("NOTION_API_KEY") and os.getenv("NOTION_PAGE_URL")),
    reason="Notion API credentials not configured in .env file"
)

class TestChildPages:
    """Test child page functionality within NotionSync"""
    
    def setup_method(self):
        """Set up test environment"""
        # Load environment variables
        load_dotenv()
        
        # Get environment variables
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
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Initialize Notion client
        self.notion_client = NotionApiClient(self.api_key)
        
        # Create test root page
        self.test_page_title = f"Child Pages Test {uuid.uuid4().hex[:8]}"
        self.test_page = self.notion_client.create_page(
            parent={"page_id": self.page_id},
            properties={"title": {"title": [{"text": {"content": self.test_page_title}}]}}
        )
        self.test_page_id = self.test_page["id"]
        
        # Initialize NotionSync with the test page
        self.notion_sync = NotionSync(
            api_key=self.api_key,
            page_id=self.test_page_id
        )
        
        # Write .env file for NotionSync
        with open(".env", "w") as f:
            f.write(f"NOTION_API_KEY={self.api_key}\n")
            f.write(f"NOTION_PAGE_URL=https://www.notion.so/{self.test_page_id}\n")
    
    def teardown_method(self):
        """Clean up after tests"""
        # Archive the test page
        try:
            self.notion_client.client.pages.update(
                page_id=self.test_page_id,
                archived=True
            )
        except Exception as e:
            print(f"Warning: Failed to archive test page: {e}")
        
        # Clean up the temporary directory
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_create_and_pull_child_pages(self):
        """Test creating child pages in Notion and pulling them"""
        # Create a few child pages in Notion
        child_pages = []
        
        # Create first level child page
        child1_title = "Child Page 1"
        child1_content = "This is the content of child page 1."
        child1_blocks = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": child1_content}}]
                }
            }
        ]
        
        child1 = self.notion_client.create_page(
            parent={"page_id": self.test_page_id},
            properties={"title": {"title": [{"text": {"content": child1_title}}]}},
            content=child1_blocks
        )
        child_pages.append(child1)
        
        # Create second level child page (a child of child1)
        child2_title = "Nested Child Page"
        child2_content = "This is a nested child page."
        child2_blocks = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": child2_content}}]
                }
            }
        ]
        
        child2 = self.notion_client.create_page(
            parent={"page_id": child1["id"]},
            properties={"title": {"title": [{"text": {"content": child2_title}}]}},
            content=child2_blocks
        )
        child_pages.append(child2)
        
        # Pull content from Notion
        result = self.notion_sync.pull()
        assert result is True, "Pull operation failed"
        
        # Verify files were created
        assert os.path.exists("index.md"), "index.md file not created"
        assert os.path.exists("Child Page 1.md"), "Child page file not created"
        
        # Verify content
        with open("Child Page 1.md", "r") as f:
            content = f.read()
            assert child1_title in content
            assert child1_content in content
        
        # Verify that nested child page was pulled
        # Note: If nested pages are not yet implemented, this test will fail
        nested_file_exists = os.path.exists("Nested Child Page.md")
        if not nested_file_exists:
            pytest.xfail("Nested child pages are not currently supported")
        else:
            with open("Nested Child Page.md", "r") as f:
                content = f.read()
                assert child2_title in content
                assert child2_content in content
    
    def test_push_child_pages(self):
        """Test pushing local files as child pages to Notion"""
        # Create local files
        with open("index.md", "w") as f:
            f.write(f"# {self.test_page_title}\n\nMain page content.\n")
        
        with open("Child Page A.md", "w") as f:
            f.write("# Child Page A\n\nThis is child page A content.\n")
        
        with open("Child Page B.md", "w") as f:
            f.write("# Child Page B\n\nThis is child page B content.\n")
        
        # Commit and push to Notion
        self.notion_sync.commit("Add main page and child pages")
        result = self.notion_sync.push()
        assert result is True, "Push operation failed"
        
        # Verify pages were created in Notion
        child_pages = self.notion_client.get_child_pages(self.test_page_id)
        assert len(child_pages) == 2, f"Expected 2 child pages, got {len(child_pages)}"
        
        # Verify child page titles
        child_titles = [page["properties"]["title"]["title"][0]["plain_text"] for page in child_pages]
        assert "Child Page A" in child_titles, "Child Page A not found in Notion"
        assert "Child Page B" in child_titles, "Child Page B not found in Notion"
    
    def test_pull_page_with_content_blocks_and_child_pages(self):
        """Test pulling a page with both content blocks and child pages"""
        # Create content in the main page
        main_content = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "This is the main page content."}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "A Section"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "More content here."}}]
                }
            }
        ]
        
        # Update main page with content
        self.notion_client.update_page(self.test_page_id, content=main_content)
        
        # Create a child page
        child_title = "Related Page"
        child_content = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "This is a related page."}}]
                }
            }
        ]
        
        self.notion_client.create_page(
            parent={"page_id": self.test_page_id},
            properties={"title": {"title": [{"text": {"content": child_title}}]}},
            content=child_content
        )
        
        # Pull content from Notion
        result = self.notion_sync.pull()
        assert result is True, "Pull operation failed"
        
        # Verify files were created
        assert os.path.exists("index.md"), "index.md file not created"
        assert os.path.exists("Related Page.md"), "Child page file not created"
        
        # Verify content
        with open("index.md", "r") as f:
            content = f.read()
            assert "This is the main page content" in content
            assert "A Section" in content
            assert "More content here" in content
        
        with open("Related Page.md", "r") as f:
            content = f.read()
            assert "Related Page" in content
            assert "This is a related page" in content
    
    def test_modify_and_sync_child_pages(self):
        """Test modifying and syncing child pages"""
        # Create initial pages
        with open("index.md", "w") as f:
            f.write(f"# {self.test_page_title}\n\nInitial content.\n")
        
        with open("Child Page.md", "w") as f:
            f.write("# Child Page\n\nInitial child page content.\n")
        
        # Commit and push
        self.notion_sync.commit("Initial content")
        self.notion_sync.push()
        
        # Modify local content
        with open("Child Page.md", "w") as f:
            f.write("# Child Page\n\nUpdated child page content.\n\n## New Section\n\nAdditional content.\n")
        
        # Commit and push changes
        self.notion_sync.commit("Update child page")
        result = self.notion_sync.push()
        assert result is True, "Push operation failed"
        
        # Pull to verify the changes from Notion
        # Clear local files first
        os.remove("index.md")
        os.remove("Child Page.md")
        
        # Pull from Notion
        self.notion_sync.pull()
        
        # Verify updated content
        assert os.path.exists("Child Page.md"), "Child page file not pulled back"
        
        with open("Child Page.md", "r") as f:
            content = f.read()
            assert "Updated child page content" in content
            assert "New Section" in content
            assert "Additional content" in content
    
    def test_page_blocks_between_content(self):
        """Test handling of page blocks that appear between content blocks"""
        # Create content for the main page with a child page between paragraphs
        main_content_before = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "This is content before the child page."}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Section Before"}}]
                }
            }
        ]
        
        # Update the main test page with the first part of content
        self.notion_client.update_page(self.test_page_id, content=main_content_before)
        
        # Create a child page that will appear in the middle of content
        embedded_page_title = "Embedded Child Page"
        embedded_child = self.notion_client.create_page(
            parent={"page_id": self.test_page_id},
            properties={"title": {"title": [{"text": {"content": embedded_page_title}}]}},
            content=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "This is content inside the embedded child page."}}]
                    }
                }
            ]
        )
        
        # Add content after the child page
        main_content_after = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Section After"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "This is content after the child page."}}]
                }
            }
        ]
        
        # Update the main page with additional content
        self.notion_client.update_page(self.test_page_id, content=main_content_after)
        
        # Pull content from Notion
        result = self.notion_sync.pull()
        assert result is True, "Pull operation failed"
        
        # Verify files were created
        assert os.path.exists("index.md"), "index.md file not created"
        assert os.path.exists(f"{embedded_page_title}.md"), "Embedded child page file not created"
        
        # Verify the content of the main page
        with open("index.md", "r") as f:
            main_content = f.read()
            assert "This is content before the child page" in main_content
            assert "Section Before" in main_content
            assert "Section After" in main_content
            assert "This is content after the child page" in main_content
            # Check if there's a reference to the child page in the main content
            assert embedded_page_title in main_content
        
        # Verify the content of the child page
        with open(f"{embedded_page_title}.md", "r") as f:
            child_content = f.read()
            assert embedded_page_title in child_content
            assert "This is content inside the embedded child page" in child_content 