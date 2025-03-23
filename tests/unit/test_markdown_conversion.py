"""
NotionSync - Markdown Conversion Tests

This module contains tests for the markdown conversion functionality.
"""

import os
import sys
import pytest
from pathlib import Path

from notionsync.markdown.converter import MarkdownConverter

class TestMarkdownConversion:
    """Test the Markdown conversion functionality"""
    
    def setup_method(self):
        """Set up the test"""
        self.converter = MarkdownConverter()
        
    def test_basic_headings(self):
        """Test conversion of basic headings"""
        markdown = "# Heading 1\n## Heading 2\n### Heading 3"
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 3
        assert blocks[0]["type"] == "heading_1"
        assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Heading 1"
        assert blocks[1]["type"] == "heading_2"
        assert blocks[2]["type"] == "heading_3"
    
    def test_paragraphs(self):
        """Test conversion of paragraphs"""
        markdown = "This is a paragraph.\n\nThis is another paragraph."
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 2
        assert blocks[0]["type"] == "paragraph"
        assert blocks[1]["type"] == "paragraph"
    
    def test_bulleted_list(self):
        """Test conversion of bulleted lists"""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 3
        assert blocks[0]["type"] == "bulleted_list_item"
        assert blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Item 1"
    
    def test_numbered_list(self):
        """Test conversion of numbered lists"""
        markdown = "1. Item 1\n2. Item 2\n3. Item 3"
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 3
        assert blocks[0]["type"] == "numbered_list_item"
        assert blocks[0]["numbered_list_item"]["rich_text"][0]["text"]["content"] == "Item 1"
    
    # Additional tests can be added here for other markdown features 