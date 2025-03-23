"""
NotionSync - Notion Block Type Tests

This module tests all the Notion block types that should be supported by the converter.
These tests ensure we can properly convert between Markdown and all supported Notion block types.
"""

import pytest
import os
import re
import json
from pathlib import Path
import tempfile
import shutil
from dotenv import load_dotenv
import uuid
import time

from notionsync.markdown.converter import MarkdownConverter
from notionsync.core.notion_client import NotionApiClient

# Skip tests if environment variables are not properly configured
pytestmark = pytest.mark.skipif(
    not (os.getenv("NOTION_API_KEY") and os.getenv("NOTION_PAGE_URL")),
    reason="Notion API credentials not configured in .env file"
)

class TestNotionBlocks:
    """Test all supported Notion block types"""
    
    def setup_method(self):
        """Set up test environment"""
        # Load environment variables
        load_dotenv()
        
        # Get environment variables
        self.api_key = os.getenv("NOTION_API_KEY")
        self.page_url = os.getenv("NOTION_PAGE_URL")
        self.page_id = None
        
        if self.page_url:
            # Extract page ID from the URL
            if "?p=" in self.page_url:
                self.page_id = self.page_url.split("?p=")[1].split("&")[0]
            else:
                # Extract ID from traditional format URL
                pattern = r"notion\.so/(?:[^/]+/)?([a-zA-Z0-9-]+)(?:\?|$)"
                match = re.search(pattern, self.page_url)
                if match:
                    self.page_id = match.group(1)
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Initialize converter
        self.converter = MarkdownConverter()
        
        # Initialize Notion client
        self.notion_client = NotionApiClient(self.api_key)
        
        # Create a test page for these tests
        self.test_page_title = f"Block Test {uuid.uuid4().hex[:8]}"
        test_page = self.notion_client.create_page(
            parent={"page_id": self.page_id},
            properties={"title": {"title": [{"text": {"content": self.test_page_title}}]}}
        )
        self.test_page_id = test_page["id"]
    
    def teardown_method(self):
        """Clean up after tests"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
        
        # Archive (delete) the test page
        try:
            if hasattr(self, 'test_page_id'):
                self.notion_client.client.pages.update(
                    page_id=self.test_page_id,
                    archived=True
                )
        except Exception as e:
            print(f"Warning: Failed to clean up test page: {e}")
    
    def test_paragraph_block(self):
        """Test paragraph block conversion"""
        # Create paragraph block using the API
        paragraph_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "This is a paragraph block."}}]
            }
        }
        
        # Add block to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=[paragraph_block]
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content
        assert "This is a paragraph block." in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify block type and content
        found_paragraph = False
        for block in converted_blocks:
            if block.get("type") == "paragraph":
                text = block["paragraph"]["rich_text"][0]["text"]["content"]
                if "This is a paragraph block." in text:
                    found_paragraph = True
                    break
        
        assert found_paragraph, "Paragraph block not properly converted"
    
    def test_heading_blocks(self):
        """Test heading blocks (h1, h2, h3) conversion"""
        # Create heading blocks
        heading_blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "Heading 1"}}],
                    "color": "default"
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Heading 2"}}],
                    "color": "default"
                }
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "Heading 3"}}],
                    "color": "default"
                }
            }
        ]
        
        # Add blocks to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=heading_blocks
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content
        assert "# Heading 1" in markdown
        assert "## Heading 2" in markdown
        assert "### Heading 3" in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify block types and content
        heading_types = {"heading_1": False, "heading_2": False, "heading_3": False}
        for block in converted_blocks:
            block_type = block.get("type", "")
            if block_type in heading_types:
                text = block[block_type]["rich_text"][0]["text"]["content"]
                if f"Heading {block_type[-1]}" in text:
                    heading_types[block_type] = True
        
        assert all(heading_types.values()), "Not all heading blocks properly converted"
    
    def test_list_blocks(self):
        """Test list blocks (bulleted and numbered) conversion"""
        # Create list blocks
        list_blocks = [
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Bullet item 1"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Bullet item 2"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Number item 1"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Number item 2"}}]
                }
            }
        ]
        
        # Add blocks to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=list_blocks
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content
        assert "- Bullet item 1" in markdown
        assert "- Bullet item 2" in markdown
        assert "Number item 1" in markdown
        assert "Number item 2" in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify block types and content
        bullet_count = 0
        number_count = 0
        for block in converted_blocks:
            if block.get("type") == "bulleted_list_item":
                text = block["bulleted_list_item"]["rich_text"][0]["text"]["content"]
                if "Bullet item" in text:
                    bullet_count += 1
            elif block.get("type") == "numbered_list_item":
                text = block["numbered_list_item"]["rich_text"][0]["text"]["content"]
                if "Number item" in text:
                    number_count += 1
        
        assert bullet_count == 2, "Not all bulleted items properly converted"
        assert number_count == 2, "Not all numbered items properly converted"
    
    def test_to_do_blocks(self):
        """Test to-do blocks (checkboxes) conversion"""
        # Create to-do blocks
        todo_blocks = [
            {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": "Unchecked item"}}],
                    "checked": False
                }
            },
            {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": "Checked item"}}],
                    "checked": True
                }
            }
        ]
        
        # Add blocks to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=todo_blocks
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content
        assert "[ ] Unchecked item" in markdown
        assert "[x] Checked item" in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify block types and content
        unchecked_found = False
        checked_found = False
        for block in converted_blocks:
            if block.get("type") == "to_do":
                text = block["to_do"]["rich_text"][0]["text"]["content"]
                checked = block["to_do"]["checked"]
                if "Unchecked item" in text and not checked:
                    unchecked_found = True
                elif "Checked item" in text and checked:
                    checked_found = True
        
        assert unchecked_found, "Unchecked to-do item not properly converted"
        assert checked_found, "Checked to-do item not properly converted"
    
    def test_code_block(self):
        """Test code block conversion"""
        # Create code block
        code_block = {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": "def hello():\n    print('Hello, world!')"}}],
                "language": "python"
            }
        }
        
        # Add block to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=[code_block]
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content
        assert "```python" in markdown
        assert "def hello():" in markdown
        assert "print('Hello, world!')" in markdown
        assert "```" in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify block type and content
        found_code_block = False
        for block in converted_blocks:
            if block.get("type") == "code":
                text = block["code"]["rich_text"][0]["text"]["content"]
                language = block["code"]["language"]
                if "def hello():" in text and language == "python":
                    found_code_block = True
                    break
        
        assert found_code_block, "Code block not properly converted"
    
    def test_quote_block(self):
        """Test quote block conversion"""
        # Create quote block
        quote_block = {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [{"type": "text", "text": {"content": "This is a quote block."}}]
            }
        }
        
        # Add block to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=[quote_block]
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content
        assert "> This is a quote block." in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify block type and content
        found_quote_block = False
        for block in converted_blocks:
            if block.get("type") == "quote":
                text = block["quote"]["rich_text"][0]["text"]["content"]
                if "This is a quote block." in text:
                    found_quote_block = True
                    break
        
        assert found_quote_block, "Quote block not properly converted"
    
    def test_divider_block(self):
        """Test divider (horizontal rule) block conversion"""
        # Create divider block
        divider_block = {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
        
        # Add block to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=[divider_block]
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content
        assert "---" in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify block type
        found_divider_block = False
        for block in converted_blocks:
            if block.get("type") == "divider":
                found_divider_block = True
                break
        
        assert found_divider_block, "Divider block not properly converted"
    
    def test_callout_block(self):
        """Test callout block conversion"""
        # Create callout block
        callout_block = {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": "This is a callout block"}}],
                "icon": {
                    "type": "emoji",
                    "emoji": "💡"
                },
                "color": "gray_background"
            }
        }
        
        # Add block to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=[callout_block]
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content - we'll use a special syntax for callouts
        assert "::: callout 💡" in markdown or "!!! note" in markdown
        assert "This is a callout block" in markdown
        assert ":::" in markdown or "!!!" in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify we created some kind of block that contains the text
        found_callout_content = False
        for block in converted_blocks:
            # Either we handle it as a callout or some other block type
            if block.get("type") == "callout":
                text = block["callout"]["rich_text"][0]["text"]["content"]
                if "This is a callout block" in text:
                    found_callout_content = True
                    break
            elif block.get("type") in ["paragraph", "quote"]:
                # If we don't support callout yet, it might be handled as a paragraph or quote
                rich_text_key = f"{block.get('type')}".strip()
                if rich_text_key in block:
                    rich_text = block[rich_text_key]["rich_text"]
                    for rt in rich_text:
                        if "text" in rt and "content" in rt["text"]:
                            if "This is a callout block" in rt["text"]["content"]:
                                found_callout_content = True
                                break
        
        assert found_callout_content, "Callout block content not preserved"
    
    def test_rich_text_formatting(self):
        """Test rich text formatting (bold, italic, etc.) conversion"""
        # Create paragraph with formatted text
        formatted_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Normal "},
                        "annotations": {"bold": False, "italic": False, "strikethrough": False, "code": False}
                    },
                    {
                        "type": "text",
                        "text": {"content": "Bold"},
                        "annotations": {"bold": True, "italic": False, "strikethrough": False, "code": False}
                    },
                    {
                        "type": "text",
                        "text": {"content": " "},
                        "annotations": {"bold": False, "italic": False, "strikethrough": False, "code": False}
                    },
                    {
                        "type": "text",
                        "text": {"content": "Italic"},
                        "annotations": {"bold": False, "italic": True, "strikethrough": False, "code": False}
                    },
                    {
                        "type": "text",
                        "text": {"content": " "},
                        "annotations": {"bold": False, "italic": False, "strikethrough": False, "code": False}
                    },
                    {
                        "type": "text",
                        "text": {"content": "Strike"},
                        "annotations": {"bold": False, "italic": False, "strikethrough": True, "code": False}
                    },
                    {
                        "type": "text",
                        "text": {"content": " "},
                        "annotations": {"bold": False, "italic": False, "strikethrough": False, "code": False}
                    },
                    {
                        "type": "text",
                        "text": {"content": "Code"},
                        "annotations": {"bold": False, "italic": False, "strikethrough": False, "code": True}
                    }
                ]
            }
        }
        
        # Add block to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=[formatted_block]
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content
        assert "Normal" in markdown
        assert "**Bold**" in markdown
        assert "*Italic*" in markdown
        assert "~~Strike~~" in markdown
        assert "`Code`" in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Check if the paragraph with formatted text exists
        formatted_content_found = False
        for block in converted_blocks:
            if block.get("type") == "paragraph":
                # Get the combined text from all rich_text segments
                combined_text = "".join(rt.get("text", {}).get("content", "") 
                                    for rt in block["paragraph"]["rich_text"])
                if ("Normal" in combined_text and "Bold" in combined_text and 
                    "Italic" in combined_text and "Strike" in combined_text and 
                    "Code" in combined_text):
                    formatted_content_found = True
                    break
        
        assert formatted_content_found, "Formatted text not properly converted"
    
    def test_link_in_text(self):
        """Test links in text conversion"""
        # Create paragraph with link
        link_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Check out this "},
                        "annotations": {"bold": False, "italic": False}
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": "link",
                            "link": {"url": "https://example.com"}
                        },
                        "annotations": {"bold": False, "italic": False}
                    },
                    {
                        "type": "text",
                        "text": {"content": " here."},
                        "annotations": {"bold": False, "italic": False}
                    }
                ]
            }
        }
        
        # Add block to test page
        self.notion_client.client.blocks.children.append(
            block_id=self.test_page_id,
            children=[link_block]
        )
        
        # Retrieve page content
        blocks = self.notion_client.get_page_content(self.test_page_id)
        
        # Convert to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content
        assert "Check out this" in markdown
        assert "[link](https://example.com)" in markdown
        assert "here." in markdown
        
        # Convert back to blocks
        converted_blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify we created a paragraph block with link
        found_link = False
        for block in converted_blocks:
            if block.get("type") == "paragraph":
                for rt in block["paragraph"]["rich_text"]:
                    if "text" in rt and rt["text"].get("content") == "link" and "link" in rt["text"]:
                        found_link = True
                        break
        
        assert found_link, "Link not preserved"
    
    def test_table_block(self):
        """Test table block conversion - simplified to test our converter only"""
        # Create a markdown table
        markdown_table = (
            "| Name  | Age | Location  |\n"
            "| ----- | --- | --------- |\n"
            "| John  | 30  | New York  |\n"
            "| Alice | 25  | London    |\n"
        )
        
        # Convert markdown to blocks
        blocks = self.converter.markdown_to_notion_blocks(markdown_table)
        
        # Debug output
        print("\nGenerated Table Blocks:")
        for block in blocks:
            if block.get("type") == "table":
                print(json.dumps(block, indent=2))
        
        # Verify the correct table block structure was created
        found_table = False
        for block in blocks:
            if block.get("type") == "table":
                found_table = True
                
                # Verify table properties
                assert block["table"]["table_width"] == 3
                # Debug
                print(f"Has header: {block['table'].get('has_column_header', 'NOT SET')}")
                assert block["table"].get("has_column_header", False) == True  # Header row detected
                
                # Verify rows
                assert "children" in block, "Table should have children (rows)"
                rows = block["children"]
                assert len(rows) == 3  # Header + 2 data rows
                
                # Check header row
                header = rows[0]
                assert header["type"] == "table_row"
                assert len(header["table_row"]["cells"]) == 3
                header_texts = []
                for cell in header["table_row"]["cells"]:
                    for text in cell:
                        header_texts.append(text["text"]["content"])
                assert "Name" in header_texts
                assert "Age" in header_texts
                assert "Location" in header_texts
                
                # Check data rows
                data_row = rows[1]
                assert data_row["type"] == "table_row"
                cell_texts = []
                for cell in data_row["table_row"]["cells"]:
                    for text in cell:
                        cell_texts.append(text["text"]["content"])
                assert "John" in cell_texts
                assert "30" in cell_texts
                assert "New York" in cell_texts
                
                break
        
        assert found_table, "Table block was not created"
        
        # Now convert back to markdown
        markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify the markdown contains our table content
        assert "| Name" in markdown
        assert "| ---" in markdown
        assert "| John" in markdown
        assert "| 30" in markdown
        assert "New York" in markdown
        assert "Alice" in markdown
        assert "25" in markdown
        assert "London" in markdown
    
    # Add more tests for other block types as needed... 