"""
NotionSync - Status Command Tests

This module contains tests for the status command functionality.
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from notionsync.cli.commands import status
from notionsync.core.sync import NotionSync
from click.testing import CliRunner

class TestStatusCommand:
    """Test the status command functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a mock config directory
        self.config_dir = Path(self.test_dir) / ".notionsync"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a commits directory
        self.commits_dir = self.config_dir / "commits"
        self.commits_dir.mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
    
    @patch('notionsync.cli.commands.load_env_variables')
    @patch('notionsync.cli.commands.NotionSync')
    def test_status_no_commits(self, mock_sync, mock_load_env):
        """Test status command with no commits"""
        # Setup mocks
        mock_load_env.return_value = {
            "api_key": "test_api_key",
            "page_id": "test_page_id",
            "database_id": None
        }
        
        mock_sync_instance = MagicMock()
        mock_sync.return_value = mock_sync_instance
        
        # Mock config with no last_commit
        mock_sync_instance.load_config.return_value = {}
        
        # Mock markdown files
        mock_sync_instance.get_markdown_files.return_value = [
            Path("test1.md"),
            Path("test2.md")
        ]
        
        # Run the command
        result = self.runner.invoke(status)
        
        # Verify output
        assert result.exit_code == 0
        assert "No commits found" in result.output
        assert "All files will be added" in result.output
    
    @patch('notionsync.cli.commands.load_env_variables')
    @patch('notionsync.cli.commands.NotionSync')
    def test_status_with_changes(self, mock_sync, mock_load_env):
        """Test status command with changes"""
        # Setup mocks
        mock_load_env.return_value = {
            "api_key": "test_api_key",
            "page_id": "test_page_id",
            "database_id": None
        }
        
        mock_sync_instance = MagicMock()
        mock_sync.return_value = mock_sync_instance
        
        # Mock config with last_commit
        mock_sync_instance.load_config.return_value = {
            "last_commit": "2023-03-24T12:00:00"
        }
        
        # Create a dummy commit file
        commit_file_path = self.commits_dir / "2023-03-24T12-00-00.json"
        commit_data = {
            "timestamp": "2023-03-24T12:00:00",
            "message": "Test commit",
            "files": [
                {"path": "index.md", "content": "# Test\n\nOld content"},
                {"path": "unchanged.md", "content": "# Unchanged\n\nThis file is unchanged"}
            ]
        }
        
        with open(commit_file_path, "w") as f:
            json.dump(commit_data, f)
        
        # Set the config_dir
        mock_sync_instance.config_dir = self.config_dir
        
        # Mock markdown files
        # Add a new file, modify one, and keep one unchanged
        # Create real files for testing
        with open("index.md", "w") as f:
            f.write("# Test\n\nNew content")
        
        with open("unchanged.md", "w") as f:
            f.write("# Unchanged\n\nThis file is unchanged")
        
        with open("new_file.md", "w") as f:
            f.write("# New File\n\nThis is a new file")
        
        mock_sync_instance.get_markdown_files.return_value = [
            Path("index.md"),
            Path("unchanged.md"),
            Path("new_file.md")
        ]
        
        # Run the command
        result = self.runner.invoke(status)
        
        # Verify output
        assert result.exit_code == 0
        assert "Changes since last commit" in result.output
        assert "Modified Files" in result.output
        assert "New Files" in result.output 