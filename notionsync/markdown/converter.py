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
        blocks = self.basic_markdown_to_blocks(markdown_content)
        
        # Ensure all blocks have the correct structure
        for block in blocks:
            # Ensure object type is set
            if "object" not in block:
                block["object"] = "block"
                
            # Ensure type field exists and is valid
            if "type" not in block:
                raise ValueError(f"Block is missing required 'type' field: {block}")
                
            # Ensure the block type content exists
            block_type = block["type"]
            if block_type not in block:
                raise ValueError(f"Block is missing content for type '{block_type}': {block}")
        
        return blocks
    
    def basic_markdown_to_blocks(self, markdown_content):
        """Convert Markdown content to basic Notion blocks"""
        blocks = []
        lines = markdown_content.split('\n')
        
        i = 0
        in_code_block = False
        code_block_content = ""
        code_language = ""
        
        # Notionが受け入れる言語リスト
        valid_notion_languages = [
            "abap", "agda", "arduino", "ascii art", "assembly", "bash", "basic", "bnf", 
            "c", "c#", "c++", "clojure", "coffeescript", "coq", "css", "dart", "dhall", 
            "diff", "docker", "ebnf", "elixir", "elm", "erlang", "f#", "flow", "fortran", 
            "gherkin", "glsl", "go", "graphql", "groovy", "haskell", "hcl", "html", "idris", 
            "java", "javascript", "json", "julia", "kotlin", "latex", "less", "lisp", 
            "livescript", "llvm ir", "lua", "makefile", "markdown", "markup", "matlab", 
            "mathematica", "mermaid", "nix", "notion formula", "objective-c", "ocaml", 
            "pascal", "perl", "php", "plain text", "powershell", "prolog", "protobuf", 
            "purescript", "python", "r", "racket", "reason", "ruby", "rust", "sass", 
            "scala", "scheme", "scss", "shell", "smalltalk", "solidity", "sql", "swift", 
            "toml", "typescript", "vb.net", "verilog", "vhdl", "visual basic", 
            "webassembly", "xml", "yaml", "java/c/c++/c#", "notionscript"
        ]
        
        # 共通のプログラミング言語マッピング
        language_mapping = {
            "js": "javascript",
            "py": "python",
            "ts": "typescript",
            "cs": "c#",
            "sh": "shell",
            "rb": "ruby",
            "yml": "yaml",
            "": "plain text"
        }
        
        in_blockquote = False
        blockquote_content = ""
        
        while i < len(lines):
            line = lines[i]
            
            # Handle code blocks
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Start of code block
                    in_code_block = True
                    code_block_content = ""
                    # Extract language if specified
                    if len(line.strip()) > 3:
                        code_language = line.strip()[3:].strip()
                        # Map common language abbreviations
                        if code_language in language_mapping:
                            code_language = language_mapping[code_language]
                        # Ensure language is valid for Notion
                        if code_language not in valid_notion_languages:
                            # Default to plain text if language is not supported
                            code_language = "plain text"
                else:
                    # End of code block
                    in_code_block = False
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": code_block_content.rstrip()}}],
                            "language": code_language if code_language else "plain text"
                        }
                    })
                i += 1
                continue
                
            if in_code_block:
                code_block_content += line + "\n"
                i += 1
                continue
            
            # Handle blockquotes
            if line.strip().startswith('> '):
                if not in_blockquote:
                    # Start of blockquote
                    in_blockquote = True
                    blockquote_content = line.strip()[2:] + "\n"
                else:
                    # Continue blockquote
                    if line.strip() == '>':
                        blockquote_content += "\n"
                    else:
                        blockquote_content += line.strip()[2:] + "\n"
                i += 1
                continue
            elif in_blockquote and line.strip() == '':
                # Empty line might continue a blockquote, check next line
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('> '):
                    blockquote_content += "\n"
                    i += 1
                    continue
                else:
                    # End of blockquote
                    in_blockquote = False
                    blocks.append({
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": [{"type": "text", "text": {"content": blockquote_content.strip()}}]
                        }
                    })
            elif in_blockquote:
                # End of blockquote reached
                in_blockquote = False
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [{"type": "text", "text": {"content": blockquote_content.strip()}}]
                    }
                })
            
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
                
            # Horizontal rule
            elif line.strip() == '---' or line.strip() == '***' or line.strip() == '___':
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
                
            # Task list items
            elif re.match(r'^- \[([ x])\] ', line.strip()):
                match = re.match(r'^- \[([ x])\] (.*)', line.strip())
                checked = match.group(1) == 'x'
                content = match.group(2)
                blocks.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": content}}],
                        "checked": checked
                    }
                })
            
            # Bullet list items
            elif line.strip().startswith('- ') and not re.match(r'^- \[([ x])\] ', line.strip()):
                content = line.strip()[2:]
                rich_text = self.process_inline_formatting(content)
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": rich_text if rich_text else [{"type": "text", "text": {"content": content}}]
                    }
                })
                
            # Numbered list items
            elif re.match(r'^\d+\.\s', line.strip()):
                content = re.sub(r'^\d+\.\s', '', line.strip())
                rich_text = self.process_inline_formatting(content)
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": rich_text if rich_text else [{"type": "text", "text": {"content": content}}]
                    }
                })
                
            # Paragraph
            elif line.strip():
                rich_text = self.process_inline_formatting(line.strip())
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": rich_text if rich_text else [{"type": "text", "text": {"content": line.strip()}}]
                    }
                })
            
            i += 1
        
        # Handle any remaining blockquote or code block
        if in_blockquote:
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": blockquote_content.strip()}}]
                }
            })
        
        if in_code_block:
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": code_block_content.rstrip()}}],
                    "language": code_language if code_language else "plain text"
                }
            })
            
        return blocks
    
    def process_inline_formatting(self, text):
        """Process inline formatting in text"""
        # Regex patterns for inline formatting
        bold_pattern = r'\*\*(.*?)\*\*'
        italic_pattern = r'\*(.*?)\*'
        code_pattern = r'`(.*?)`'
        link_pattern = r'\[(.*?)\]\((.*?)\)'
        strikethrough_pattern = r'~~(.*?)~~'
        
        # Find all formatting patterns in the text
        rich_text = []
        remaining_text = text
        
        # Process bold text
        bold_matches = list(re.finditer(bold_pattern, text))
        # Process italic text
        italic_matches = list(re.finditer(italic_pattern, text))
        # Process code
        code_matches = list(re.finditer(code_pattern, text))
        # Process links
        link_matches = list(re.finditer(link_pattern, text))
        # Process strikethrough
        strikethrough_matches = list(re.finditer(strikethrough_pattern, text))
        
        # Combine all matches and sort by position
        all_matches = []
        
        for match in bold_matches:
            all_matches.append({
                'start': match.start(),
                'end': match.end(),
                'content': match.group(1),
                'type': 'bold'
            })
        
        for match in italic_matches:
            # Skip matches that are part of bold formatting (** has * inside it)
            is_inside_bold = False
            for bold_match in bold_matches:
                if bold_match.start() <= match.start() and bold_match.end() >= match.end():
                    is_inside_bold = True
                    break
            if not is_inside_bold:
                all_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'content': match.group(1),
                    'type': 'italic'
                })
        
        for match in code_matches:
            all_matches.append({
                'start': match.start(),
                'end': match.end(),
                'content': match.group(1),
                'type': 'code'
            })
        
        for match in link_matches:
            all_matches.append({
                'start': match.start(),
                'end': match.end(),
                'content': match.group(1),
                'url': match.group(2),
                'type': 'link'
            })
        
        for match in strikethrough_matches:
            all_matches.append({
                'start': match.start(),
                'end': match.end(),
                'content': match.group(1),
                'type': 'strikethrough'
            })
        
        # Sort matches by start position
        all_matches.sort(key=lambda x: x['start'])
        
        # If no formatting, return simple text
        if not all_matches:
            return [{"type": "text", "text": {"content": text}}]
        
        # Build rich text array
        rich_text = []
        last_end = 0
        
        for match in all_matches:
            # Add any text before this match
            if match['start'] > last_end:
                rich_text.append({
                    "type": "text",
                    "text": {"content": text[last_end:match['start']]}
                })
            
            # Add the formatted text
            if match['type'] == 'bold':
                rich_text.append({
                    "type": "text",
                    "text": {"content": match['content']},
                    "annotations": {"bold": True}
                })
            elif match['type'] == 'italic':
                rich_text.append({
                    "type": "text",
                    "text": {"content": match['content']},
                    "annotations": {"italic": True}
                })
            elif match['type'] == 'code':
                rich_text.append({
                    "type": "text",
                    "text": {"content": match['content']},
                    "annotations": {"code": True}
                })
            elif match['type'] == 'strikethrough':
                rich_text.append({
                    "type": "text",
                    "text": {"content": match['content']},
                    "annotations": {"strikethrough": True}
                })
            elif match['type'] == 'link':
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": match['content'],
                        "link": {"url": match['url']}
                    }
                })
            
            last_end = match['end']
        
        # Add any remaining text
        if last_end < len(text):
            rich_text.append({
                "type": "text",
                "text": {"content": text[last_end:]}
            })
        
        return rich_text
    
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
            link = text_item.get("text", {}).get("link", None)
            
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
                
            # Handle links
            if link and link.get("url"):
                content = f"[{content}]({link['url']})"
            
            result.append(content)
        
        return "".join(result) 