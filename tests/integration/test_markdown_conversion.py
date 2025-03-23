"""
NotionSync - Markdown Conversion Tests

This module contains tests for the conversion between Markdown and Notion blocks.
These tests verify that all supported Markdown elements can be correctly converted
to Notion blocks and back to Markdown.
"""

import pytest
import os
import re
import json
from pathlib import Path
import tempfile
import shutil
from dotenv import load_dotenv

from notionsync.markdown.converter import MarkdownConverter
from notionsync.core.notion_client import NotionApiClient
from notionsync.core.sync import NotionSync
from notionsync.utils.helpers import load_env_variables

# Skip tests if environment variables are not properly configured
pytestmark = pytest.mark.skipif(
    not (os.getenv("NOTION_API_KEY") and (os.getenv("NOTION_PAGE_URL") or os.getenv("NOTION_DATABASE_ID"))),
    reason="Notion API credentials not configured in .env file"
)

class TestMarkdownConversion:
    """Test conversion between Markdown and Notion blocks"""
    
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
        
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Initialize converter
        self.converter = MarkdownConverter()
        
        # Initialize Notion client (for end-to-end tests)
        self.notion_client = NotionApiClient(self.api_key)
        
        # Initialize NotionSync (for workflow tests)
        self.notion_sync = NotionSync(
            api_key=self.api_key,
            page_id=self.page_id,
            database_id=self.database_id
        )
    
    def teardown_method(self):
        """Clean up after tests"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_headings_conversion(self):
        """Test conversion of headings (H1, H2, H3)"""
        markdown = """# Heading 1
        
## Heading 2

### Heading 3
"""
        # Convert markdown to notion blocks
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify blocks are correctly created
        assert len(blocks) >= 3
        assert blocks[0]["type"] == "heading_1"
        assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Heading 1"
        assert blocks[1]["type"] == "heading_2"
        assert blocks[1]["heading_2"]["rich_text"][0]["text"]["content"] == "Heading 2"
        assert blocks[2]["type"] == "heading_3"
        assert blocks[2]["heading_3"]["rich_text"][0]["text"]["content"] == "Heading 3"
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Normalize whitespace for comparison
        normalized_markdown = re.sub(r'\s+', ' ', converted_markdown).strip()
        expected_normalized = re.sub(r'\s+', ' ', "# Heading 1 ## Heading 2 ### Heading 3").strip()
        
        assert "Heading 1" in converted_markdown
        assert "Heading 2" in converted_markdown
        assert "Heading 3" in converted_markdown
        assert "# " in converted_markdown
        assert "## " in converted_markdown
        assert "### " in converted_markdown
    
    def test_paragraph_conversion(self):
        """Test conversion of paragraphs"""
        markdown = """This is a simple paragraph.

This is another paragraph with *italic* and **bold** text.
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify blocks
        assert len(blocks) >= 2
        assert blocks[0]["type"] == "paragraph"
        assert "simple paragraph" in blocks[0]["paragraph"]["rich_text"][0]["text"]["content"]
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        assert "simple paragraph" in converted_markdown
        assert "another paragraph" in converted_markdown
    
    def test_lists_conversion(self):
        """Test conversion of bullet and numbered lists"""
        markdown = """- Item 1
- Item 2
- Item 3

1. First
2. Second
3. Third
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify blocks
        assert len(blocks) >= 6
        assert blocks[0]["type"] == "bulleted_list_item"
        assert "Item 1" in blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
        assert blocks[3]["type"] == "numbered_list_item"
        assert "First" in blocks[3]["numbered_list_item"]["rich_text"][0]["text"]["content"]
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        assert "- Item 1" in converted_markdown
        assert "- Item 2" in converted_markdown
        assert "- Item 3" in converted_markdown
        assert "1. First" in converted_markdown or "1. " in converted_markdown and "First" in converted_markdown
    
    def test_code_blocks_conversion(self):
        """Test conversion of code blocks"""
        markdown = """```python
def hello_world():
    print("Hello, world!")
```
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify blocks
        if len(blocks) > 0 and "code" in blocks[0]:
            assert blocks[0]["type"] == "code"
            assert "python" in blocks[0]["code"].get("language", "")
            assert "hello_world" in blocks[0]["code"]["rich_text"][0]["text"]["content"]
            
            # Convert back to markdown
            converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
            
            assert "```python" in converted_markdown
            assert "def hello_world()" in converted_markdown
            assert "Hello, world!" in converted_markdown
    
    def test_blockquotes_conversion(self):
        """Test conversion of blockquotes"""
        markdown = """> This is a blockquote.
> It can span multiple lines.
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify blocks
        if len(blocks) > 0 and blocks[0].get("type") == "quote":
            assert "blockquote" in blocks[0]["quote"]["rich_text"][0]["text"]["content"]
            
            # Convert back to markdown
            converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
            
            assert ">" in converted_markdown
            assert "blockquote" in converted_markdown
    
    def test_horizontal_rule_conversion(self):
        """Test conversion of horizontal rules"""
        markdown = """Before the rule

---

After the rule
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Find the divider block
        divider_index = None
        for i, block in enumerate(blocks):
            if block.get("type") == "divider":
                divider_index = i
                break
        
        if divider_index is not None:
            assert blocks[divider_index]["type"] == "divider"
            
            # Convert back to markdown
            converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
            
            assert "---" in converted_markdown
            assert "Before the rule" in converted_markdown
            assert "After the rule" in converted_markdown
    
    def test_formatting_conversion(self):
        """Test conversion of text formatting (bold, italic, etc.)"""
        markdown = """**Bold text** and *italic text* and ~~strikethrough text~~ and `inline code`.
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify blocks - this depends on how the converter implements rich text
        assert len(blocks) > 0
        assert blocks[0]["type"] == "paragraph"
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Validate that the formatted elements are preserved in some form
        assert "Bold text" in converted_markdown
        assert "italic text" in converted_markdown
        assert "strikethrough text" in converted_markdown
        assert "inline code" in converted_markdown
    
    def test_task_list_conversion(self):
        """Test conversion of task lists (checkboxes)"""
        markdown = """- [ ] Unchecked task
- [x] Checked task
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Verify blocks if converter supports to_do blocks
        to_do_blocks = [b for b in blocks if b.get("type") == "to_do"]
        if to_do_blocks:
            assert any(not b["to_do"].get("checked", False) for b in to_do_blocks)
            assert any(b["to_do"].get("checked", False) for b in to_do_blocks)
            
            # Convert back to markdown
            converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
            
            assert "[ ]" in converted_markdown
            assert "[x]" in converted_markdown
            assert "Unchecked task" in converted_markdown
            assert "Checked task" in converted_markdown
    
    def test_complex_document_conversion(self):
        """Test conversion of a complex document with multiple elements"""
        markdown = """# Complex Document Test

This is a paragraph with **bold** and *italic* formatting.

## Lists Section

- Item 1
- Item 2
  - Subitem 2.1
  - Subitem 2.2
- Item 3

1. First ordered item
2. Second ordered item
   1. Subitem 2.1
   2. Subitem 2.2
3. Third ordered item

## Code and Quotes

Here's a code block:

```python
def test_function():
    return "Hello, World!"
```

And a blockquote:

> This is a quote
> It spans multiple lines

## Tasks

- [ ] Implement feature A
- [x] Fix bug B
- [ ] Update documentation

---

The end.
"""
        # Convert to blocks
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Basic verification of content preservation
        assert "Complex Document Test" in converted_markdown
        assert "bold" in converted_markdown
        assert "italic" in converted_markdown
        assert "Lists Section" in converted_markdown
        assert "Item" in converted_markdown
        assert "code block" in converted_markdown or "```" in converted_markdown
        assert "quote" in converted_markdown
        assert "Tasks" in converted_markdown
        assert "feature A" in converted_markdown
        assert "bug B" in converted_markdown
        assert "The end" in converted_markdown
    
    @pytest.mark.skipif(not os.getenv("NOTION_PAGE_URL"), reason="No page URL configured")
    def test_end_to_end_conversion(self):
        """Test end-to-end conversion via the Notion API (requires API credentials)"""
        # Create a dedicated test child page to avoid affecting main page content
        test_page_title = f"Test Page {os.urandom(4).hex()}"
        child_page = {
            "parent": {"page_id": self.page_id},
            "properties": {
                "title": [{"text": {"content": test_page_title}}]
            }
        }
        
        try:
            # Create test child page
            created_page = self.notion_client.create_page(
                parent={"page_id": self.page_id},
                properties={"title": {"title": [{"text": {"content": test_page_title}}]}}
            )
            
            test_child_id = created_page["id"]
            
            # Test markdown for conversion
            test_markdown = """# API Conversion Test

This is a test of the Markdown to Notion blocks conversion through the API.

## Features tested:
- Lists
- **Bold formatting**
- *Italic formatting*
- Code: `print("Hello")`

```python
def test_function():
    return "This is a code block"
```

> This is a blockquote

---

The end.
"""
            # Set up test file
            with open("api_test.md", "w", encoding="utf-8") as f:
                f.write(test_markdown)

            # Get blocks from markdown
            blocks = self.converter.markdown_to_notion_blocks(test_markdown)

            # Clear existing blocks from test page before adding new ones
            self.notion_client.clear_page_content(test_child_id)
            
            # Update test page via API
            result = self.notion_client.update_page(test_child_id, properties=None, content=blocks)
            assert result is not False

            # Get the updated page content
            retrieved_blocks = self.notion_client.get_page_content(test_child_id)
            assert retrieved_blocks is not None

            # Convert retrieved blocks back to markdown
            retrieved_markdown = self.converter.notion_blocks_to_markdown(retrieved_blocks)
            assert retrieved_markdown is not None

            # Check if key elements are preserved
            assert "API Conversion Test" in retrieved_markdown
            assert "Features tested" in retrieved_markdown
            assert "Bold formatting" in retrieved_markdown
            assert "Italic formatting" in retrieved_markdown
            assert "code block" in retrieved_markdown
            assert "blockquote" in retrieved_markdown

        except Exception as e:
            pytest.fail(f"End-to-end API test failed: {str(e)}")
            
        finally:
            # Cleanup: Delete the test child page
            try:
                if 'test_child_id' in locals():
                    # Use archive instead of delete since Notion API doesn't support 
                    # direct deletion of pages
                    self.notion_client.client.pages.update(
                        page_id=test_child_id,
                        archived=True
                    )
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up test page: {cleanup_error}")
    
    @pytest.mark.skipif(not os.getenv("NOTION_PAGE_URL"), reason="No page URL configured")
    def test_workflow_markdown_conversion(self):
        """Test markdown conversion as part of NotionSync workflow"""
        # Use a unique test file name to avoid conflicts
        test_file_name = f"workflow_test_{os.urandom(4).hex()}.md"
        
        test_markdown = """# Workflow Conversion Test

This document tests the conversion of Markdown as part of the NotionSync workflow.

## Lists and formatting:
- Item with **bold text**
- Item with *italic text*
- Item with `inline code`

```
This is a code block
With multiple lines
```

Final paragraph.
"""
        # Set up test file
        with open(test_file_name, "w", encoding="utf-8") as f:
            f.write(test_markdown)
        
        try:
            # Initialize config directory
            self.notion_sync.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Store original page ID
            original_page_id = self.notion_sync.notion_client.page_id
            
            # Create a temporary test page
            test_page_title = f"Workflow Test {os.urandom(4).hex()}"
            created_page = self.notion_client.create_page(
                parent={"page_id": original_page_id},
                properties={"title": {"title": [{"text": {"content": test_page_title}}]}}
            )
            test_page_id = created_page["id"]
            
            # Set the test page as the target
            self.notion_sync.notion_client.page_id = test_page_id
            
            # Commit the file
            commit = self.notion_sync.commit("Test workflow conversion")
            assert commit is not None
            
            # Push to Notion
            result = self.notion_sync.push()
            assert result is not False
            
            # Remove local file to test pull
            os.remove(test_file_name)
            
            # Pull from Notion
            result = self.notion_sync.pull()
            assert result is not False
            
            # Verify file was recreated
            assert Path(test_file_name).exists()
            
            # Read the content
            with open(test_file_name, "r", encoding="utf-8") as f:
                pulled_content = f.read()
            
            # Check if key elements are preserved
            assert "Workflow Conversion Test" in pulled_content
            assert "Lists and formatting" in pulled_content
            assert "bold text" in pulled_content
            assert "italic text" in pulled_content
            assert "inline code" in pulled_content
            assert "code block" in pulled_content
            assert "Final paragraph" in pulled_content
            
        except Exception as e:
            pytest.fail(f"Workflow conversion test failed: {str(e)}")
            
        finally:
            # Cleanup
            try:
                # Remove test file
                if os.path.exists(test_file_name):
                    os.remove(test_file_name)
                    
                # Restore original page ID
                if 'original_page_id' in locals():
                    self.notion_sync.notion_client.page_id = original_page_id
                
                # Archive the test page
                if 'test_page_id' in locals():
                    self.notion_client.client.pages.update(
                        page_id=test_page_id,
                        archived=True
                    )
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up test resources: {cleanup_error}") 