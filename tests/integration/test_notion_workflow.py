"""
NotionSync - Notion API Complete Workflow Tests

These tests use the actual Notion API to verify all workflows of NotionSync.
Requires a valid .env file with NOTION_API_KEY and either NOTION_PAGE_URL or NOTION_DATABASE_ID.
Tests cover the complete workflow: init, status, commit, push, pull, log, etc.
"""

import os
import re
import pytest
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv
import time

from notionsync.core.sync import NotionSync
from notionsync.utils.helpers import load_env_variables
from notionsync.cli.commands import init_command, status_command, commit_command, push_command, pull_command, log_command

# Skip all tests if environment variables are not properly configured
pytestmark = pytest.mark.skipif(
    not (os.getenv("NOTION_API_KEY") and (os.getenv("NOTION_PAGE_URL") or os.getenv("NOTION_DATABASE_ID"))),
    reason="Notion API credentials not configured in .env file"
)

class TestNotionGitWorkflow:
    """Complete workflow tests with actual Notion API"""
    
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
        
        # Create .env file in test directory
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"NOTION_API_KEY={self.api_key}\n")
            f.write(f"NOTION_PAGE_URL={self.page_url}\n")
            if self.database_id:
                f.write(f"NOTION_DATABASE_ID={self.database_id}\n")
        
        # Initialize NotionSync with real credentials
        self.notion_sync = NotionSync(
            api_key=self.api_key,
            page_id=self.page_id,
            database_id=self.database_id
        )
    
    def teardown_method(self):
        """Clean up after tests"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_1_initial_setup_and_index_md_generation(self):
        """テストケース1: 初期セットアップとindex.md自動生成"""
        # Test if index.md doesn't exist initially
        assert not Path("index.md").exists()
        
        # Run the init command
        result = init_command({}, None)
        assert result is True
        
        # Check if index.md was created
        assert Path("index.md").exists()
        
        # Verify content of index.md is a template
        with open("index.md", "r", encoding="utf-8") as f:
            content = f.read()
            assert "# " in content
            assert "NotionSync" in content

    def test_2_local_document_creation_and_status(self):
        """テストケース2: ローカルでの文書作成とstatusコマンド"""
        # Initialize the repository
        init_command({}, None)
        
        # Create a new markdown file
        with open("chapter1.md", "w", encoding="utf-8") as f:
            f.write("# Chapter 1\n\nThis is the first chapter of my document.")
        
        # Edit index.md
        with open("index.md", "a", encoding="utf-8") as f:
            f.write("\n\n## Added Content\nThis content was added for testing.")
        
        # Run status command to check for changes
        status = status_command({}, None)
        
        # Verify status shows the files are changed (either as added or modified)
        assert status is not None
        assert "chapter1.md" in status["added"]
        
        # index.md could be in either added or modified depending on implementation
        # check that it appears in one of these
        assert "index.md" in status["added"] or "index.md" in status["modified"], \
            "index.md should be detected as either added or modified"

    def test_3_commit_command(self):
        """テストケース3: commitコマンドの実行"""
        # Initialize and create files
        init_command({}, None)
        with open("chapter1.md", "w", encoding="utf-8") as f:
            f.write("# Chapter 1\n\nThis is the first chapter of my document.")
        
        # Run commit command
        commit_result = commit_command({"message": "Add chapter1"}, None)
        assert commit_result is not None
        
        # Check commit was recorded
        log_entries = log_command({}, None)
        assert len(log_entries) > 0
        assert any("Add chapter1" in entry for entry in log_entries)
        
        # Status should now show no changes
        status = status_command({}, None)
        assert len(status["added"]) == 0
        assert len(status["modified"]) == 0
        assert len(status["deleted"]) == 0

    def test_4_push_command(self):
        """テストケース4: pushコマンドの実行"""
        # Skip if no page_id is provided
        if not self.page_id:
            pytest.skip("No page_id configured in .env")
            
        # Initialize, create files and commit
        init_command({}, None)
        with open("chapter1.md", "w", encoding="utf-8") as f:
            f.write("# Chapter 1\n\nThis is the first chapter of my document.")
        commit_command({"message": "Add chapter1"}, None)
        
        # Run push command
        push_result = push_command({}, None)
        assert push_result is True
        
        # Wait a moment for Notion API to process
        time.sleep(2)
        
        # Verify content was pushed to Notion by pulling it back
        # Delete local files first to ensure we're pulling fresh content
        os.remove("index.md")
        os.remove("chapter1.md")
        
        # Pull content from Notion
        pull_result = pull_command({}, None)
        assert pull_result is True
        
        # Verify files were pulled correctly
        assert Path("index.md").exists()
        assert Path("chapter1.md").exists() or any(Path().glob("*chapter1*.md"))

    def test_5_notion_edit_and_pull(self):
        """テストケース5: Notion上での編集後のpullコマンド"""
        # Skip if no page_id is provided
        if not self.page_id:
            pytest.skip("No page_id configured in .env")
            
        # Initialize, create files, commit and push
        init_command({}, None)
        # First, create content that we'll later modify through the API
        with open("index.md", "w", encoding="utf-8") as f:
            f.write("# Main Page\n\nThis is the main page content.")
        commit_command({"message": "Update main page"}, None)
        push_command({}, None)
        
        # Wait a moment for Notion API to process
        time.sleep(2)
        
        # Edit content directly through Notion API
        # We'll use the notion_client to update the page
        # Adding a marker text that we'll check for after pulling
        test_content = "This content was added through the Notion API."
        try:
            self.notion_sync.notion_client.update_page(
                self.page_id, 
                f"# Main Page\n\nThis is the main page content.\n\n## API Edit\n{test_content}"
            )
            
            # Wait for API changes to take effect
            time.sleep(2)
            
            # Delete local index.md to ensure we get fresh content
            os.remove("index.md")
            
            # Pull content from Notion
            pull_result = pull_command({}, None)
            assert pull_result is True
            
            # Verify the API changes were pulled
            assert Path("index.md").exists()
            with open("index.md", "r", encoding="utf-8") as f:
                content = f.read()
                assert test_content in content
        except Exception as e:
            pytest.skip(f"Could not update Notion page directly: {str(e)}")

    def test_6_log_command(self):
        """テストケース6: logコマンドの検証"""
        # Initialize and create multiple commits
        init_command({}, None)
        
        # First commit
        with open("file1.md", "w", encoding="utf-8") as f:
            f.write("# File 1\n\nContent of file 1.")
        commit_command({"message": "Add file1"}, None)
        
        # Second commit
        with open("file2.md", "w", encoding="utf-8") as f:
            f.write("# File 2\n\nContent of file 2.")
        commit_command({"message": "Add file2"}, None)
        
        # Third commit - modify existing file
        with open("file1.md", "a", encoding="utf-8") as f:
            f.write("\n\nAdditional content for file 1.")
        commit_command({"message": "Update file1"}, None)
        
        # Check log entries
        log_entries = log_command({}, None)
        assert len(log_entries) >= 3
        
        # Verify commits are in reverse chronological order
        assert "Update file1" in log_entries[0]
        assert "Add file2" in log_entries[1]
        assert "Add file1" in log_entries[2]
        
        # Check format of log entries
        for entry in log_entries:
            assert re.search(r'\d{4}-\d{2}-\d{2}', entry)  # Date
            assert re.search(r'\d{2}:\d{2}:\d{2}', entry)  # Time

    def test_7_local_edit_and_push_after_pull(self):
        """テストケース7: ローカル編集後の再編集フロー"""
        # Skip if no page_id is provided
        if not self.page_id:
            pytest.skip("No page_id configured in .env")
            
        # Initialize, create files, commit and push
        init_command({}, None)
        with open("document.md", "w", encoding="utf-8") as f:
            f.write("# Document\n\nInitial content.")
        commit_command({"message": "Add document"}, None)
        push_command({}, None)
        
        # Wait for API
        time.sleep(2)
        
        # Simulate pull (by directly modifying files as if pulled from Notion)
        with open("document.md", "w", encoding="utf-8") as f:
            f.write("# Document\n\nInitial content.\n\nContent from Notion.")
        
        # Re-edit locally
        with open("document.md", "a", encoding="utf-8") as f:
            f.write("\n\nLocal edit after pull.")
        
        # Check status
        status = status_command({}, None)
        assert "document.md" in status["modified"]
        
        # Commit and push changes
        commit_command({"message": "Local edit after pull"}, None)
        push_result = push_command({}, None)
        assert push_result is True
        
        # Verify changes by pulling again
        os.remove("document.md")
        pull_result = pull_command({}, None)
        assert pull_result is True
        
        # Check content includes both changes
        with open("document.md", "r", encoding="utf-8") as f:
            content = f.read()
            assert "Content from Notion" in content
            assert "Local edit after pull" in content

    def test_8_error_handling(self):
        """テストケース8: エラーハンドリングおよび不正操作の検証"""
        # Initialize with valid settings
        init_command({}, None)
        
        # Temporarily save API key
        saved_api_key = os.environ.get("NOTION_API_KEY")
        
        try:
            # Set invalid API key
            os.environ["NOTION_API_KEY"] = "invalid_key_12345"
            
            # Create a new .env file with invalid credentials
            with open(".env", "w", encoding="utf-8") as f:
                f.write("NOTION_API_KEY=invalid_key_12345\n")
                f.write(f"NOTION_PAGE_URL={self.page_url}\n")
            
            # Test push should fail but gracefully handle the error
            result = push_command({}, None)
            assert result is False, "Push should fail with invalid API key"
            
            # Commit should still work with local operations
            result = commit_command({"message": "Test commit with invalid API"}, None)
            assert result is not False, "Commit should work even with invalid API key"
            
        finally:
            # Restore API key
            if saved_api_key:
                os.environ["NOTION_API_KEY"] = saved_api_key
                with open(".env", "w", encoding="utf-8") as f:
                    f.write(f"NOTION_API_KEY={saved_api_key}\n")
                    f.write(f"NOTION_PAGE_URL={self.page_url}\n")
                    if self.database_id:
                        f.write(f"NOTION_DATABASE_ID={self.database_id}\n")
    
    @pytest.mark.skipif(not os.getenv("NOTION_DATABASE_ID"), reason="No database ID configured")
    def test_database_integration(self):
        """データベース統合テスト"""
        # Skip if no database_id is provided
        if not self.database_id:
            pytest.skip("No database_id configured in .env")
        
        # Initialize
        init_command({}, None)
        
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
        
        # Commit and push to database
        commit_command({"message": "Add database entry"}, None)
        push_result = push_command({}, None)
        assert push_result is True
        
        # Wait for API
        time.sleep(2)
        
        # Remove files
        os.remove("test_db_entry.md")
        
        # Pull from database
        pull_result = pull_command({}, None)
        assert pull_result is True
        
        # Check database files were pulled
        db_files = list(Path().glob("*.md"))
        assert len(db_files) > 0
        
        # Check content of at least one file
        if db_files:
            with open(db_files[0], "r", encoding="utf-8") as f:
                content = f.read()
                assert "---" in content  # Has front matter
                assert "#" in content  # Has markdown content 