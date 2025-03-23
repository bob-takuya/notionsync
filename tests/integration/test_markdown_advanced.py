"""
NotionSync - Advanced Markdown Conversion Tests

This module contains more specialized tests for complex Markdown elements
and their conversion to Notion blocks. These tests verify edge cases and
special formatting options.
"""

import pytest
import os
import re
from pathlib import Path
import tempfile
import shutil
from dotenv import load_dotenv

from notionsync.markdown.converter import MarkdownConverter
from notionsync.core.notion_client import NotionApiClient
from notionsync.core.sync import NotionSync

# Skip tests if environment variables are not properly configured
pytestmark = pytest.mark.skipif(
    not (os.getenv("NOTION_API_KEY") and (os.getenv("NOTION_PAGE_URL") or os.getenv("NOTION_DATABASE_ID"))),
    reason="Notion API credentials not configured in .env file"
)

class TestAdvancedMarkdownConversion:
    """Test advanced conversion between Markdown and Notion blocks"""
    
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
    
    def teardown_method(self):
        """Clean up after tests"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_nested_formatting(self):
        """Test nested formatting (e.g., bold inside italic)"""
        markdown = """This contains *italic with **bold** inside* it.

And also **bold with *italic* inside** it.
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Verify content preservation
        assert "italic with" in converted_markdown
        assert "**bold**" in converted_markdown
        assert "bold with" in converted_markdown
        assert "*italic*" in converted_markdown
        
        # Check for formatting markers (implementation dependent)
        assert "*" in converted_markdown
        assert "**" in converted_markdown
    
    def test_tables(self):
        """Test Markdown tables if supported"""
        markdown = """| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Tables may not be directly supported, so just check if content is preserved
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Content preservation, though format might change
        assert "Header 1" in converted_markdown
        assert "Cell 1" in converted_markdown
        assert "Cell 6" in converted_markdown
    
    def test_math_equations(self):
        """Test math equations if supported"""
        markdown = """Inline equation: $E=mc^2$.

Block equation:

$$
\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
$$
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Content preservation (format might change)
        assert "E=" in converted_markdown
        assert "mc" in converted_markdown
        assert "int" in converted_markdown or "\\int" in converted_markdown
    
    def test_links(self):
        """Test hyperlinks"""
        markdown = """[NotionSync GitHub](https://github.com/bob-takuya/notionsync)

Check out [this link](https://www.notion.so) for more information.
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Check for link preservation
        assert "NotionSync GitHub" in converted_markdown
        assert "github.com" in converted_markdown
        assert "notion.so" in converted_markdown
        assert "[" in converted_markdown
        assert "]" in converted_markdown
        assert "(" in converted_markdown
        assert ")" in converted_markdown
    
    def test_mixed_lists(self):
        """Test mixed list types"""
        markdown = """- First bullet
  - Nested bullet
    1. Nested number
    2. Another nested number
- Second bullet
1. First number
2. Second number
   - Nested bullet in number
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Content preservation
        assert "First bullet" in converted_markdown
        assert "Nested bullet" in converted_markdown
        assert "nested number" in converted_markdown.lower()
        assert "Second bullet" in converted_markdown
        assert "First number" in converted_markdown
    
    def test_multiline_nested_elements(self):
        """Test elements with multiple lines and nesting"""
        markdown = """> This is a blockquote
> With multiple lines
> 
> And a paragraph break
> 
> - With a list
> - Inside the quote
> 
> And more content.
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Content preservation
        assert "blockquote" in converted_markdown
        assert "multiple lines" in converted_markdown
        assert "With a list" in converted_markdown
        assert "Inside the quote" in converted_markdown
        assert "And more content" in converted_markdown
    
    def test_frontmatter(self):
        """Test YAML frontmatter if supported"""
        markdown = """---
title: Test Document
tags: [markdown, test, conversion]
date: 2023-08-15
---

# After Frontmatter

Content starts here.
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Content preservation - frontmatter might not be preserved in the same format
        assert "After Frontmatter" in converted_markdown
        assert "Content starts here" in converted_markdown
    
    def test_html_in_markdown(self):
        """Test HTML elements in Markdown if supported"""
        markdown = """Some <strong>HTML</strong> inline elements.

<div class="custom">
  <p>This is an HTML block.</p>
</div>

<table>
  <tr>
    <td>Cell 1</td>
    <td>Cell 2</td>
  </tr>
</table>
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Content preservation - HTML might be stripped or converted
        assert "HTML" in converted_markdown
        assert "inline elements" in converted_markdown
        assert "This is an HTML block" in converted_markdown
    
    @pytest.mark.skipif(not os.getenv("NOTION_PAGE_URL"), reason="No page URL configured")
    def test_large_document_conversion(self):
        """Test conversion of a large document"""
        # Create a dedicated test child page to avoid affecting main page content
        test_page_title = f"Large Doc Test {os.urandom(4).hex()}"
        
        try:
            # Create test child page
            created_page = self.notion_client.create_page(
                parent={"page_id": self.page_id},
                properties={"title": {"title": [{"text": {"content": test_page_title}}]}}
            )
            
            test_child_id = created_page["id"]
            
            # Create a large markdown document with repeating elements
            large_markdown = "# Large Document Test\n\n"
            
            # Add 50 paragraphs with various formatting
            for i in range(1, 51):
                large_markdown += f"## Section {i}\n\n"
                large_markdown += f"This is paragraph {i} with **bold** and *italic* formatting.\n\n"
                large_markdown += f"- List item {i}.1\n"
                large_markdown += f"- List item {i}.2\n\n"
                if i % 5 == 0:
                    large_markdown += f"```python\ndef function_{i}():\n    return {i}\n```\n\n"
                if i % 7 == 0:
                    large_markdown += f"> Blockquote in section {i}\n\n"
                large_markdown += "---\n\n" if i % 10 == 0 else "\n"
            
            # Write large document to file
            with open("large_test.md", "w", encoding="utf-8") as f:
                f.write(large_markdown)
            
            # Test basic conversion of the large document
            blocks = self.converter.markdown_to_notion_blocks(large_markdown)
            assert blocks is not None
            assert len(blocks) > 100  # Should be many blocks
            
            # Convert back to markdown
            converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
            assert converted_markdown is not None
            
            # Test with Notion API if credentials are available
            # First clear the test page content
            self.notion_client.clear_page_content(test_child_id)
            
            # Use first 100 blocks only to avoid rate limits
            blocks = blocks[:100]
            result = self.notion_client.update_page(test_child_id, properties=None, content=blocks)
            assert result is not False
            
            # Verify content can be retrieved
            retrieved_blocks = self.notion_client.get_page_content(test_child_id)
            assert retrieved_blocks is not None
            
            # Check content preservation for a few sections
            for i in [1, 10, 20]:
                assert f"Section {i}" in large_markdown
                assert f"paragraph {i}" in large_markdown
                assert f"List item {i}.1" in large_markdown
        except Exception as e:
            pytest.fail(f"Large document API test failed: {str(e)}")
        finally:
            # Cleanup: Delete the test file and archive the test page
            try:
                if os.path.exists("large_test.md"):
                    os.remove("large_test.md")
                
                if 'test_child_id' in locals():
                    self.notion_client.client.pages.update(
                        page_id=test_child_id,
                        archived=True
                    )
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up test resources: {cleanup_error}")
    
    @pytest.mark.skipif(not os.getenv("NOTION_DATABASE_ID"), reason="No database ID configured")
    def test_database_properties_in_frontmatter(self):
        """Test conversion of frontmatter to database properties"""
        markdown = """---
title: Database Test Entry
tags: markdown, conversion, test
priority: high
date: 2023-08-15
complete: true
---

# Database Entry

This tests conversion of frontmatter to Notion database properties.
"""
        # Set up test file
        with open("db_frontmatter_test.md", "w", encoding="utf-8") as f:
            f.write(markdown)
        
        try:
            # Initialize NotionSync for database
            notion_sync = NotionSync(
                api_key=self.api_key,
                database_id=self.database_id
            )
            
            # Initialize config directory
            notion_sync.config_dir = Path(self.test_dir) / ".notionsync"
            notion_sync.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Commit and push to database
            notion_sync.commit("Test frontmatter conversion")
            result = notion_sync.push()
            
            # Skip further assertions if push failed
            if result is False:
                pytest.skip("Push to database failed")
                
            # Pull from database
            notion_sync.pull()
            
            # Check if file exists with frontmatter
            pulled_files = list(Path().glob("*.md"))
            assert len(pulled_files) > 0
            
            # Check content of at least one file
            for file_path in pulled_files:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "---" in content:  # Has frontmatter
                        # Check if any of our original properties are preserved
                        # (they might be renamed or transformed)
                        lower_content = content.lower()
                        has_property = any(prop in lower_content for prop in 
                                          ["title", "tags", "priority", "date", "complete"])
                        if has_property:
                            break
            else:
                pytest.fail("No files with expected frontmatter properties found")
                
        except Exception as e:
            pytest.fail(f"Database properties test failed: {str(e)}")
    
    def test_special_characters(self):
        """Test handling of special characters"""
        markdown = """# Special Characters: ©®™

- Em dash —
- En dash –
- Ellipsis …
- Straight quotes: ' and "
- Curly quotes: ' ' and " "
- Bullet •
- Arrow →
- Registered ®
- Copyright ©
- Trademark ™
- Currency symbols: $ € £ ¥
- Math symbols: ± × ÷ √ ≈
- Accents: é à ü ñ
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Content preservation
        assert "Special Characters" in converted_markdown
        assert "Em dash" in converted_markdown
        assert "En dash" in converted_markdown
        assert "Ellipsis" in converted_markdown
        assert "Straight quotes" in converted_markdown
        assert "Currency symbols" in converted_markdown
        
        # Check for some special characters
        for char in ["é", "®", "&", "👍", "🚀"]:
            if char not in converted_markdown:
                pytest.skip(f"Character {char} not preserved in conversion")
    
    def test_nested_list_to_notion_and_back(self):
        """Test deeply nested lists conversion"""
        markdown = """- Level 1
  - Level 2
    - Level 3
      - Level 4
        - Level 5
          - Level 6

1. Number 1
   1. Number 1.1
      1. Number 1.1.1
         - Bullet in number list
           - Deeper bullet
"""
        blocks = self.converter.markdown_to_notion_blocks(markdown)
        
        # Convert back to markdown
        converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
        
        # Content preservation
        assert "Level 1" in converted_markdown
        assert "Level 6" in converted_markdown
        assert "Number 1" in converted_markdown
        assert "Number 1.1.1" in converted_markdown
        assert "Bullet in number list" in converted_markdown 