"""
NotionSync - Pull Command Tests

This module contains tests for the pull command functionality.
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from notionsync.cli.commands import pull
from notionsync.core.sync import NotionSync
from click.testing import CliRunner

class TestPullCommand:
    """Test the pull command functionality"""
    
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
    def test_pull_from_page(self, mock_sync, mock_load_env):
        """Test pull from a Notion page"""
        # Setup mocks
        mock_load_env.return_value = {
            "api_key": "test_api_key",
            "page_id": "test_page_id",
            "database_id": None
        }
        
        mock_sync_instance = MagicMock()
        mock_sync.return_value = mock_sync_instance
        
        # Mock pull method
        mock_sync_instance.pull.return_value = True
        
        # Run the command
        result = self.runner.invoke(pull)
        
        # Verify output
        assert result.exit_code == 0
        mock_sync_instance.pull.assert_called_once()
    
    @patch('notionsync.cli.commands.load_env_variables')
    @patch('notionsync.cli.commands.NotionSync')
    def test_pull_from_database(self, mock_sync, mock_load_env):
        """Test pull from a Notion database"""
        # Setup mocks
        mock_load_env.return_value = {
            "api_key": "test_api_key",
            "page_id": None,
            "database_id": "test_db_id"
        }
        
        mock_sync_instance = MagicMock()
        mock_sync.return_value = mock_sync_instance
        
        # Mock pull method
        mock_sync_instance.pull.return_value = True
        
        # Run the command
        result = self.runner.invoke(pull)
        
        # Verify output
        assert result.exit_code == 0
        mock_sync_instance.pull.assert_called_once()
    
    @patch('notionsync.cli.commands.load_env_variables')
    @patch('notionsync.cli.commands.NotionSync')
    def test_pull_with_error(self, mock_sync, mock_load_env):
        """Test pull with an error"""
        # Setup mocks
        mock_load_env.return_value = {
            "api_key": "test_api_key",
            "page_id": "test_page_id", 
            "database_id": None
        }
        
        mock_sync_instance = MagicMock()
        mock_sync.return_value = mock_sync_instance
        
        # Mock pull method with error
        mock_sync_instance.pull.return_value = False
        
        # Run the command
        result = self.runner.invoke(pull)
        
        # Verify output
        assert result.exit_code == 0  # Click still returns 0 by default
        mock_sync_instance.pull.assert_called_once() 