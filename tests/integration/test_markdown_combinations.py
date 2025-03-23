"""
NotionSync - Markdown Conversion Combinations Tests

This module tests combinations of different Markdown elements
to ensure they work together correctly when converting to Notion blocks
and back to Markdown.
"""

import pytest
import os
import re
import itertools
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

# Define the basic markdown elements to test
markdown_elements = {
    "heading1": "# Heading 1\n\n",
    "heading2": "## Heading 2\n\n",
    "heading3": "### Heading 3\n\n",
    "paragraph": "This is a simple paragraph with plain text.\n\n",
    "bold": "**Bold text** in a paragraph.\n\n",
    "italic": "*Italic text* in a paragraph.\n\n",
    "combined_format": "**Bold and *nested italic* text** in a paragraph.\n\n",
    "code": "`Inline code` in a paragraph.\n\n",
    "link": "[Link text](https://example.com) in a paragraph.\n\n",
    "bullet_list": "- Item 1\n- Item 2\n- Item 3\n\n",
    "numbered_list": "1. First item\n2. Second item\n3. Third item\n\n",
    "nested_list": "- Item A\n  - Nested item A.1\n  - Nested item A.2\n- Item B\n\n",
    "mixed_list": "1. First\n   - Sub bullet\n   - Another sub bullet\n2. Second\n\n",
    "blockquote": "> This is a blockquote\n> It spans multiple lines\n\n",
    "code_block": "```python\ndef hello():\n    print('Hello, world!')\n```\n\n",
    "checkbox": "- [x] Completed task\n- [ ] Pending task\n\n",
    "horizontal_rule": "---\n\n",
    "table": "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |\n\n",
    "image": "![Image description](https://example.com/image.jpg)\n\n",
    "html": "<strong>HTML content</strong> in a paragraph.\n\n",
    "math": "$E = mc^2$ inline equation.\n\n",
    "special_chars": "Special characters: © ® ™ 🎉 👍\n\n"
}

class TestMarkdownCombinations:
    """Test combinations of Markdown elements"""
    
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
    
    def test_basic_element_combinations(self):
        """Test basic combinations of different markdown elements"""
        # Define combination groups to test
        test_groups = [
            # Headers and formatting
            ["heading1", "paragraph", "bold", "italic"],
            # Lists and formatting
            ["heading2", "bullet_list", "numbered_list", "combined_format"],
            # Quotes and code
            ["heading2", "blockquote", "code_block", "code"],
            # Links and images
            ["heading3", "link", "image", "horizontal_rule"],
            # Special elements
            ["heading2", "table", "special_chars", "math"],
            # Mixed elements
            ["heading1", "nested_list", "code_block", "blockquote"]
        ]
        
        # Test each group
        for group_idx, group in enumerate(test_groups):
            # Combine elements from the group
            markdown = f"# Test Group {group_idx + 1}\n\n"
            for element in group:
                markdown += markdown_elements[element]
            
            # Convert to notion blocks and back
            blocks = self.converter.markdown_to_notion_blocks(markdown)
            converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
            
            # Verify basic content preservation for each element
            for element in group:
                # Special case for links - check for the link text separately
                if element == "link":
                    assert "Link text" in converted_markdown, f"Link text not found in converted markdown"
                    assert "https://example.com" in converted_markdown, f"URL not found in converted markdown"
                    continue
                
                # Special case for images - check for image components separately
                if element == "image":
                    assert "Image description" in converted_markdown, f"Image description not found in converted markdown"
                    assert "https://example.com/image.jpg" in converted_markdown, f"Image URL not found in converted markdown"
                    continue
                
                # Extract the first few words of the element to check for
                element_content = markdown_elements[element].split()
                if element_content:
                    # Take the first few significant words 
                    # (skip formatting symbols and just get text content)
                    words_to_check = []
                    for word in element_content:
                        clean_word = re.sub(r'[*_`#\-\[\]()>!|]', '', word).strip()
                        if clean_word and len(clean_word) > 1:  # Skip short symbols or empty strings
                            words_to_check.append(clean_word)
                            if len(words_to_check) >= 2:  # Get at most 2 words
                                break
                    
                    # Check for presence of these words in the converted markdown
                    for word in words_to_check:
                        assert word in converted_markdown, f"Word '{word}' from element '{element}' not found in converted markdown"
    
    def test_progressive_document_building(self):
        """Test progressively building a document with different elements"""
        # Start with an empty document
        markdown = ""
        
        # Progressive test steps with different elements to add
        test_steps = [
            ("heading1", "# Main Title\n\n"),
            ("paragraph", "This is an introduction paragraph.\n\n"),
            ("bullet_list", "- First important point\n- Second important point\n\n"),
            ("heading2", "## Section 1\n\n"),
            ("bold_paragraph", "This paragraph has **bold text** in it.\n\n"),
            ("code_block", "```\nprint('Hello')\n```\n\n"),
            ("heading2", "## Section 2\n\n"),
            ("numbered_list", "1. Step one\n2. Step two\n\n"),
            ("blockquote", "> Important quote to remember\n\n"),
            ("horizontal_rule", "---\n\n"),
            ("conclusion", "In conclusion, this test verifies progressive document building.\n\n")
        ]
        
        # Add each element progressively and test conversion
        for step_idx, (element_name, element_content) in enumerate(test_steps):
            # Add new element to document
            markdown += element_content
            
            # Convert to notion blocks and back
            blocks = self.converter.markdown_to_notion_blocks(markdown)
            converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
            
            # For each step, verify all previous elements are still present
            for i in range(step_idx + 1):
                prev_name, prev_content = test_steps[i]
                
                # Special case for formatted text
                if prev_name == "bold_paragraph":
                    assert "bold text" in converted_markdown, f"Step {step_idx+1}: Bold text from step {i+1} not found"
                    continue
                
                # Extract key phrase from the content to check for
                key_phrase = prev_content.strip().split('\n')[0]
                key_phrase = re.sub(r'[*_`#\-\[\]()>]', '', key_phrase).strip()
                
                if key_phrase:
                    assert key_phrase in converted_markdown, f"Step {step_idx+1}: Content from step {i+1} ({prev_name}) not found in converted markdown"
    
    def test_common_document_patterns(self):
        """Test common document patterns and structures"""
        # Define common document patterns
        document_patterns = [
            # Basic article structure
            """# Article Title

Introduction paragraph goes here with some context.

## First Section

This section introduces the first main point.

- Point 1 with **bold emphasis**
- Point 2 with *italic text*
- Point 3 with `code snippet`

## Second Section

> This is an important quote or key takeaway.

Here's a code example:

```python
def example():
    return "Hello, world!"
```

## Conclusion

Summary paragraph with final thoughts.
""",
            # Tutorial/guide structure
            """# How-To Guide

This guide will show you how to achieve a specific task.

## Prerequisites

Before starting, you'll need:

1. Requirement one
2. Requirement two
3. Requirement three

## Step 1: First Action

Do this first. Here's what you should see:

```
Example output
```

## Step 2: Second Action

Now do this next step.

> Note: Pay attention to this important detail.

## Troubleshooting

If you encounter issues:

- [ ] Check prerequisite 1
- [ ] Verify step 1 completed
- [x] Contact support if needed

## Additional Resources

[Link to more information](https://example.com)
""",
            # Note-taking structure
            """# Meeting Notes

**Date:** Today
**Participants:** Alice, Bob, Charlie

## Agenda

1. Project updates
2. Timeline discussion
3. Action items

## Discussion Points

### Project Updates

- Team A: Working on feature X
  - Subtask 1 completed
  - Subtask 2 in progress
- Team B: Resolved issue Y

### Timeline

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Alpha     | June 15     | On track |
| Beta      | July 30     | At risk |

## Action Items

- [ ] Alice: Follow up on issue Y
- [ ] Bob: Schedule next meeting
- [x] Charlie: Share documentation

---

*Next meeting scheduled for next week*
"""
        ]
        
        # Test each pattern
        for idx, pattern in enumerate(document_patterns):
            # Convert to notion blocks and back
            blocks = self.converter.markdown_to_notion_blocks(pattern)
            converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
            
            # Verify major sections are preserved
            # Extract headings from the original
            headings = re.findall(r'#+\s+(.+)$', pattern, re.MULTILINE)
            
            for heading in headings:
                assert heading in converted_markdown, f"Pattern {idx+1}: Heading '{heading}' not found in converted markdown"
            
            # Check for key formatting elements
            if "**bold" in pattern:
                assert "bold" in converted_markdown
            if "*italic" in pattern:
                assert "italic" in converted_markdown
            if "`code" in pattern:
                assert "code" in converted_markdown
            if "- [ ]" in pattern:
                assert "[ ]" in converted_markdown or "unchecked" in converted_markdown.lower()
    
    @pytest.mark.skipif(not os.getenv("NOTION_PAGE_URL"), reason="No page URL configured")
    def test_combination_workflows(self):
        """Test combination workflows with the Notion API"""
        # Test both local conversion and API-based conversion for a document
        test_documents = [
            # Document 1: Basic elements
            """# Test Document 1

This is a simple document with **bold** and *italic* text.

## Lists

- Item 1
- Item 2
  - Nested item
  
## Code

```python
print("Hello")
```

> Important note
""",
            # Document 2: More complex elements
            """# Test Document 2

This document tests more elements together.

## Table and List

| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |

1. Step one
2. Step two
   - Substep A
   - Substep B

## Tasks and Quotes

- [ ] Todo item
- [x] Completed item

> Quote with **bold** and *italic* formatting
> And a second line
"""
        ]
        
        # Create a dedicated test child page
        test_page_title = f"Combo Workflow Test {os.urandom(4).hex()}"
        test_page_id = None
        test_files = []
        
        try:
            # Create test parent page
            created_page = self.notion_client.create_page(
                parent={"page_id": self.page_id},
                properties={"title": {"title": [{"text": {"content": test_page_title}}]}}
            )
            test_page_id = created_page["id"]
            
            notion_sync = NotionSync(
                api_key=self.api_key,
                page_id=test_page_id
            )
            
            # Initialize config directory
            notion_sync.config_dir = Path(self.test_dir) / ".notionsync"
            notion_sync.config_dir.mkdir(parents=True, exist_ok=True)
            
            for idx, doc_content in enumerate(test_documents):
                # Test filename
                filename = f"test_doc_{idx+1}.md"
                test_files.append(filename)
                
                # Local conversion test
                blocks = self.converter.markdown_to_notion_blocks(doc_content)
                converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
                
                # API-based test: Write to file, commit, push, pull
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(doc_content)
                
                # Commit and push
                notion_sync.commit(f"Test document {idx+1}")
                result = notion_sync.push()
                
                if result is False:
                    pytest.skip("Push to Notion failed")
                
                # Delete local file and pull
                os.remove(filename)
                notion_sync.pull()
                
                # Verify file was recreated
                assert Path(filename).exists()
                
                with open(filename, "r", encoding="utf-8") as f:
                    pulled_content = f.read()
                
                # Extract headings from original and pulled content
                original_headings = re.findall(r'#+\s+(.+)$', doc_content, re.MULTILINE)
                pulled_headings = re.findall(r'#+\s+(.+)$', pulled_content, re.MULTILINE)
                
                # Verify all headings from original are in pulled content
                for heading in original_headings:
                    assert any(heading in ph for ph in pulled_headings), f"Document {idx+1}: Heading '{heading}' not found in pulled content"
                
                # Verify key structural elements are preserved
                if "##" in doc_content:
                    assert "##" in pulled_content
                if "- " in doc_content:
                    assert "- " in pulled_content or "•" in pulled_content  # Some converters use bullets
                if "```" in doc_content:
                    assert "```" in pulled_content or "code" in pulled_content.lower()
                
        except Exception as e:
            pytest.fail(f"Workflow test failed: {str(e)}")
            
        finally:
            # Cleanup
            try:
                # Remove test files
                for filename in test_files:
                    if os.path.exists(filename):
                        os.remove(filename)
                
                # Archive the test page
                if test_page_id:
                    self.notion_client.client.pages.update(
                        page_id=test_page_id,
                        archived=True
                    )
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up test resources: {cleanup_error}")
    
    def test_generated_combinations(self):
        """Test generated combinations of markdown elements"""
        # Select key elements to combine
        key_elements = ["heading1", "bold", "italic", "bullet_list", 
                        "numbered_list", "blockquote", "code_block"]
        
        # Generate all combinations of 3 elements
        combinations = list(itertools.combinations(key_elements, 3))
        
        # Test a subset of combinations to avoid too many tests
        for combo_idx, combo in enumerate(combinations[:5]):  # Test first 5 combinations
            # Combine elements from the combo
            markdown = f"# Combination Test {combo_idx + 1}\n\n"
            for element in combo:
                markdown += markdown_elements[element]
            
            # Convert to notion blocks and back
            blocks = self.converter.markdown_to_notion_blocks(markdown)
            converted_markdown = self.converter.notion_blocks_to_markdown(blocks)
            
            # Verify content preservation for each element
            for element in combo:
                if element == "heading1":
                    assert "# " in converted_markdown
                elif element == "bold":
                    assert "Bold text" in converted_markdown
                elif element == "italic":
                    assert "Italic text" in converted_markdown
                elif element == "bullet_list":
                    assert "Item 1" in converted_markdown
                    assert "Item 2" in converted_markdown
                elif element == "numbered_list":
                    assert "First item" in converted_markdown
                elif element == "blockquote":
                    assert "blockquote" in converted_markdown
                elif element == "code_block":
                    assert "hello()" in converted_markdown 