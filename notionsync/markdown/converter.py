"""
NotionSync - Markdown Converter Module

This module handles the conversion of Markdown content to Notion blocks.
"""

import re
import mistune
from mistletoe import Document

class MarkdownConverter:
    """Converts Markdown content to Notion blocks"""
    
    def __init__(self):
        """Initialize the Markdown converter"""
        pass
    
    def markdown_to_notion_blocks(self, markdown_content):
        """Convert Markdown content to Notion blocks"""
        # This is a simplified version of the conversion function
        # In a real implementation, this would be more complex
        blocks = self.basic_markdown_to_blocks(markdown_content)
        return blocks
    
    def basic_markdown_to_blocks(self, markdown_content):
        """Convert Markdown content to basic Notion blocks"""
        blocks = []
        lines = markdown_content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Headings
            if line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]
                    }
                })
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]
                    }
                })
            elif line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:].strip()}}]
                    }
                })
            
            # Paragraph
            elif line.strip() and not line.startswith('```'):
                # Check for bulleted list item
                if line.strip().startswith('- '):
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": line.strip()[2:].strip()}}]
                        }
                    })
                # Check for numbered list item
                elif re.match(r'^\d+\.\s', line.strip()):
                    content = re.sub(r'^\d+\.\s', '', line.strip())
                    blocks.append({
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": content.strip()}}]
                        }
                    })
                # Regular paragraph
                else:
                    # Process inline formatting
                    rich_text = self.process_inline_formatting(line.strip())
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": rich_text if rich_text else [{"type": "text", "text": {"content": line.strip()}}]
                        }
                    })
            
            i += 1
        
        return blocks
    
    def process_inline_formatting(self, text):
        """Process inline formatting in text"""
        # This is a simplified version of the inline formatting processing
        # In a real implementation, this would handle bold, italic, etc.
        return [{"type": "text", "text": {"content": text}}] 