"""
NotionSync - Markdown Converter Module

This module handles the conversion of Markdown content to Notion blocks and vice versa.
"""

import re
import mistune
from mistletoe import Document

class MarkdownConverter:
    """Converts between Markdown content and Notion blocks"""
    
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
    
    def notion_blocks_to_markdown(self, blocks):
        """Convert Notion blocks to Markdown content"""
        markdown_lines = []
        
        for block in blocks:
            block_type = block.get("type", "")
            
            if block_type == "paragraph":
                text = self.extract_text_from_rich_text(block["paragraph"]["rich_text"])
                markdown_lines.append(text)
                markdown_lines.append("")  # Add empty line after paragraph
                
            elif block_type == "heading_1":
                text = self.extract_text_from_rich_text(block["heading_1"]["rich_text"])
                markdown_lines.append(f"# {text}")
                markdown_lines.append("")  # Add empty line after heading
                
            elif block_type == "heading_2":
                text = self.extract_text_from_rich_text(block["heading_2"]["rich_text"])
                markdown_lines.append(f"## {text}")
                markdown_lines.append("")  # Add empty line after heading
                
            elif block_type == "heading_3":
                text = self.extract_text_from_rich_text(block["heading_3"]["rich_text"])
                markdown_lines.append(f"### {text}")
                markdown_lines.append("")  # Add empty line after heading
                
            elif block_type == "bulleted_list_item":
                text = self.extract_text_from_rich_text(block["bulleted_list_item"]["rich_text"])
                markdown_lines.append(f"- {text}")
                
            elif block_type == "numbered_list_item":
                text = self.extract_text_from_rich_text(block["numbered_list_item"]["rich_text"])
                markdown_lines.append(f"1. {text}")  # We always use 1. as the number
                
            elif block_type == "code":
                text = self.extract_text_from_rich_text(block["code"]["rich_text"])
                language = block["code"].get("language", "")
                markdown_lines.append(f"```{language}")
                markdown_lines.append(text)
                markdown_lines.append("```")
                markdown_lines.append("")  # Add empty line after code block
                
            elif block_type == "to_do":
                text = self.extract_text_from_rich_text(block["to_do"]["rich_text"])
                checked = block["to_do"].get("checked", False)
                checkbox = "[x]" if checked else "[ ]"
                markdown_lines.append(f"- {checkbox} {text}")
                
            elif block_type == "quote":
                text = self.extract_text_from_rich_text(block["quote"]["rich_text"])
                markdown_lines.append(f"> {text}")
                markdown_lines.append("")  # Add empty line after quote
                
            elif block_type == "divider":
                markdown_lines.append("---")
                markdown_lines.append("")  # Add empty line after divider
                
            # Handle child blocks recursively if available
            if "children" in block and block["children"]:
                child_markdown = self.notion_blocks_to_markdown(block["children"])
                # Indent child content
                indented_markdown = "\n".join(["    " + line for line in child_markdown.split("\n")])
                markdown_lines.append(indented_markdown)
        
        return "\n".join(markdown_lines)
    
    def extract_text_from_rich_text(self, rich_text):
        """Extract plain text from Notion rich text array"""
        result = []
        
        for text_item in rich_text:
            content = text_item.get("text", {}).get("content", "")
            annotations = text_item.get("annotations", {})
            
            # Apply formatting based on annotations
            if annotations.get("bold"):
                content = f"**{content}**"
            if annotations.get("italic"):
                content = f"*{content}*"
            if annotations.get("strikethrough"):
                content = f"~~{content}~~"
            if annotations.get("code"):
                content = f"`{content}`"
            if annotations.get("underline"):
                # Markdown doesn't have underline, approximate with emphasis
                content = f"_{content}_"
            
            result.append(content)
        
        return "".join(result) 