"""
NotionSync - Sync Module

This module handles the synchronization between local markdown files and Notion pages.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from rich.console import Console

from ..markdown.converter import MarkdownConverter
from .notion_client import NotionApiClient
from ..utils.helpers import extract_front_matter

# Initialize rich console for better output formatting
console = Console()

class NotionSync:
    """Sync between local markdown files and Notion pages"""
    
    def __init__(self, api_key=None, page_id=None, database_id=None, config_dir=None):
        """Initialize the NotionSync"""
        self.notion_client = NotionApiClient(api_key, page_id, database_id)
        self.markdown_converter = MarkdownConverter()
        self.config_dir = config_dir or Path.home() / ".notionsync"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure the required directories exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self):
        """Load config from config file"""
        config_file = self.config_dir / "config.json"
        if config_file.exists():
            with open(config_file, "r") as f:
                return json.load(f)
        return {}
    
    def save_config(self, config):
        """Save config to config file"""
        config_file = self.config_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
    
    def get_markdown_files(self):
        """Get all markdown files in the current directory"""
        return list(Path(".").glob("**/*.md"))
    
    def create_index_md_if_missing(self):
        """Create an index.md file if it doesn't exist"""
        index_path = Path("index.md")
        if not index_path.exists():
            console.print("[yellow]Creating index.md file...[/yellow]")
            with open(index_path, "w") as f:
                f.write("# NotionSync Project\n\nThis is the main page of your NotionSync project.\n")
            console.print("[green]Created index.md file[/green]")
    
    def commit(self, message):
        """Commit changes to local storage"""
        # Get current state of markdown files
        files = self.get_markdown_files()
        
        # Prepare commit data
        commit_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "files": []
        }
        
        # Record file contents
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                commit_data["files"].append({
                    "path": str(file_path),
                    "content": content
                })
        
        # Save commit to file
        commits_dir = self.config_dir / "commits"
        commits_dir.mkdir(exist_ok=True)
        commit_file = commits_dir / f"{commit_data['timestamp'].replace(':', '-')}.json"
        
        with open(commit_file, "w", encoding="utf-8") as f:
            json.dump(commit_data, f, indent=2)
        
        # Update last commit pointer
        config = self.load_config()
        config["last_commit"] = commit_data["timestamp"]
        self.save_config(config)
        
        console.print(f"[green]Committed {len(files)} files with message: {message}[/green]")
        return commit_data
    
    def push(self):
        """Push committed changes to Notion"""
        # Load config to get last commit
        config = self.load_config()
        if "last_commit" not in config:
            console.print("[bold red]No commits found. Please commit first.[/bold red]")
            return False
        
        # Load the last commit
        last_commit = config["last_commit"]
        commit_file = self.config_dir / "commits" / f"{last_commit.replace(':', '-')}.json"
        
        if not commit_file.exists():
            console.print(f"[bold red]Commit file not found: {commit_file}[/bold red]")
            return False
        
        with open(commit_file, "r", encoding="utf-8") as f:
            commit_data = json.load(f)
        
        # Determine if we're pushing to a database or a page
        if self.notion_client.database_id:
            return self.push_to_database(commit_data)
        else:
            index_path = Path("index.md")
            return self.push_to_page(commit_data, index_path)
    
    def push_to_database(self, commit_data):
        """Push committed changes to a Notion database"""
        console.print("[yellow]Pushing to Notion database...[/yellow]")
        
        # Validate database ID
        if not self.notion_client.database_id:
            console.print("[bold red]Database ID not set. Please set NOTION_DATABASE_ID in your .env file.[/bold red]")
            return False
        
        # Process each file in the commit
        success_count = 0
        for file_data in commit_data["files"]:
            file_path = file_data["path"]
            content = file_data["content"]
            
            # Skip index.md for database pushes
            if file_path == "index.md":
                continue
            
            try:
                # Extract front matter and content
                front_matter, markdown_content = extract_front_matter(content)
                
                # Skip files without front matter in database mode
                if not front_matter:
                    console.print(f"[yellow]Skipping {file_path} - No front matter found (required for database entries)[/yellow]")
                    continue
                
                # Get page title from filename (without extension)
                page_title = Path(file_path).stem
                
                # Create properties for database
                properties = {
                    "Name": {"title": [{"text": {"content": page_title}}]}
                }
                
                # Add front matter as properties
                for key, value in front_matter.items():
                    # Handle tags specially (as multi-select)
                    if key.lower() == "tags":
                        tags = [tag.strip() for tag in value.split(",")]
                        properties["Tags"] = {
                            "multi_select": [{"name": tag} for tag in tags]
                        }
                    else:
                        # For other properties, add as rich text
                        properties[key] = {
                            "rich_text": [{"text": {"content": value}}]
                        }
                
                # Convert markdown to Notion blocks
                blocks = self.markdown_converter.markdown_to_notion_blocks(markdown_content)
                
                # Check if entry already exists in database by name
                query_filter = {
                    "property": "Name",
                    "title": {
                        "equals": page_title
                    }
                }
                
                # Query the database
                query_result = self.notion_client.query_database(
                    self.notion_client.database_id,
                    filter=query_filter
                )
                
                if query_result["results"]:
                    # Update existing entry
                    page_id = query_result["results"][0]["id"]
                    console.print(f"[yellow]Updating existing page in database: {page_title}[/yellow]")
                    
                    # First, clear existing content
                    # (In a real implementation, we would handle this more gracefully)
                    
                    # Update properties and content
                    self.notion_client.update_page(page_id, properties, blocks)
                else:
                    # Create new entry
                    console.print(f"[yellow]Creating new page in database: {page_title}[/yellow]")
                    
                    # Set parent to database
                    parent = {"database_id": self.notion_client.database_id}
                    
                    # Create page
                    self.notion_client.create_page(parent, properties, blocks)
                
                success_count += 1
                
            except Exception as e:
                console.print(f"[bold red]Error pushing {file_path} to database: {e}[/bold red]")
        
        if success_count > 0:
            console.print(f"[green]Successfully pushed {success_count} files to Notion database[/green]")
            return True
        else:
            console.print("[bold red]No files were pushed to the database.[/bold red]")
            return False
    
    def push_to_page(self, commit_data, index_path):
        """Push committed changes to a Notion page"""
        console.print("[yellow]Pushing to Notion page...[/yellow]")
        
        # Validate page ID
        if not self.notion_client.page_id:
            console.print("[bold red]Page ID not set. Please set NOTION_PAGE_URL in your .env file.[/bold red]")
            return False
        
        try:
            # Check if the page exists
            page = self.notion_client.get_page(self.notion_client.page_id)
            
            # Clear existing content
            # In a real implementation, we would handle this more gracefully (e.g., diff and update)
            
            # First, push the index.md file to the main content
            index_file = None
            child_pages = []
            
            # Find index.md and other files in commit data
            for file_data in commit_data["files"]:
                if file_data["path"] == "index.md":
                    index_file = file_data
                else:
                    child_pages.append(file_data)
            
            # Push index.md content to the main page
            if index_file:
                console.print("[yellow]Updating main page content from index.md...[/yellow]")
                
                # Convert markdown to Notion blocks
                blocks = self.markdown_converter.markdown_to_notion_blocks(index_file["content"])
                
                # Update page content
                self.notion_client.update_page(self.notion_client.page_id, None, blocks)
            
            # Create child pages for other markdown files
            for child_page_data in child_pages:
                file_path = child_page_data["path"]
                content = child_page_data["content"]
                
                # Get page title from filename (without extension)
                page_title = Path(file_path).stem
                
                console.print(f"[yellow]Creating child page: {page_title}[/yellow]")
                
                # Extract front matter if exists
                front_matter, markdown_content = extract_front_matter(content)
                
                # Create properties for child page
                properties = {
                    "title": {"title": [{"text": {"content": page_title}}]}
                }
                
                # Convert markdown to Notion blocks
                blocks = self.markdown_converter.markdown_to_notion_blocks(markdown_content)
                
                # Set parent to page
                parent = {"page_id": self.notion_client.page_id}
                
                # Create child page
                self.notion_client.create_page(parent, properties, blocks)
            
            console.print(f"[green]Successfully pushed {len(commit_data['files'])} files to Notion[/green]")
            return True
            
        except Exception as e:
            console.print(f"[bold red]Error pushing to Notion: {e}[/bold red]")
            return False
    
    def pull(self):
        """Pull content from Notion to local files"""
        # Determine if we're pulling from a database or a page
        if self.notion_client.database_id:
            return self.pull_from_database()
        else:
            return self.pull_from_page()
    
    def pull_from_database(self):
        """Pull content from a Notion database to local files"""
        console.print("[yellow]Pulling from Notion database...[/yellow]")
        
        # Validate database ID
        if not self.notion_client.database_id:
            console.print("[bold red]Database ID not set. Please set NOTION_DATABASE_ID in your .env file.[/bold red]")
            return False
        
        try:
            # Query database to get all entries
            query_result = self.notion_client.query_database(self.notion_client.database_id)
            
            if not query_result["results"]:
                console.print("[yellow]No entries found in database.[/yellow]")
                return True
            
            # Create a directory for the database if it doesn't exist
            db_dir = Path("notion_db")
            db_dir.mkdir(exist_ok=True)
            
            # Process each database entry
            for entry in query_result["results"]:
                # Get page ID and title
                page_id = entry["id"]
                
                # Get page title from Name property
                page_title = "untitled"
                if "properties" in entry and "Name" in entry["properties"]:
                    title_data = entry["properties"]["Name"]["title"]
                    if title_data:
                        page_title = title_data[0]["plain_text"]
                
                # Sanitize title for filename
                safe_title = "".join(c if c.isalnum() or c in [' ', '.', '-', '_'] else '_' for c in page_title)
                
                # Get page content
                page_content = self.notion_client.get_page_content(page_id)
                
                # Convert blocks to markdown
                markdown_content = self.markdown_converter.notion_blocks_to_markdown(page_content)
                
                # Extract properties to front matter
                front_matter = {}
                
                for prop_name, prop_data in entry["properties"].items():
                    # Skip the Name property as it's used for the title
                    if prop_name == "Name":
                        continue
                    
                    # Handle different property types
                    prop_type = prop_data["type"]
                    
                    if prop_type == "rich_text" and prop_data["rich_text"]:
                        front_matter[prop_name] = prop_data["rich_text"][0]["plain_text"]
                    elif prop_type == "select" and prop_data["select"]:
                        front_matter[prop_name] = prop_data["select"]["name"]
                    elif prop_type == "multi_select":
                        tags = [item["name"] for item in prop_data["multi_select"]]
                        if tags:
                            front_matter["tags"] = ", ".join(tags)
                    # Add more property types as needed
                
                # Create front matter string
                front_matter_str = "---\n"
                for key, value in front_matter.items():
                    front_matter_str += f"{key}: {value}\n"
                front_matter_str += "---\n\n"
                
                # Save to file
                file_path = db_dir / f"{safe_title}.md"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(front_matter_str + markdown_content)
                
                console.print(f"[green]Saved {file_path}[/green]")
            
            console.print(f"[green]Successfully pulled {len(query_result['results'])} entries from database[/green]")
            return True
            
        except Exception as e:
            console.print(f"[bold red]Error pulling from database: {e}[/bold red]")
            return False
    
    def pull_from_page(self):
        """Pull content from a Notion page to local files"""
        console.print("[yellow]Pulling from Notion page...[/yellow]")
        
        # Validate page ID
        if not self.notion_client.page_id:
            console.print("[bold red]Page ID not set. Please set NOTION_PAGE_URL in your .env file.[/bold red]")
            return False
        
        try:
            # Get page content
            page_content = self.notion_client.get_page_content(self.notion_client.page_id)
            
            # Get page metadata
            page = self.notion_client.get_page(self.notion_client.page_id)
            
            # Get page title
            page_title = "Notion Page"
            if "properties" in page and "title" in page["properties"]:
                title_data = page["properties"]["title"]["title"]
                if title_data:
                    page_title = title_data[0]["plain_text"]
            
            # Convert blocks to markdown
            markdown_content = self.markdown_converter.notion_blocks_to_markdown(page_content)
            
            # Save to index.md
            with open("index.md", "w", encoding="utf-8") as f:
                f.write(f"# {page_title}\n\n{markdown_content}")
            
            console.print(f"[green]Saved main page content to index.md[/green]")
            
            # Get child pages
            child_pages = self.notion_client.get_child_pages(self.notion_client.page_id)
            
            # Process each child page
            for child_page in child_pages:
                child_id = child_page["id"]
                child_title = child_page["properties"]["title"]["title"][0]["plain_text"]
                
                # Sanitize title for filename
                safe_title = "".join(c if c.isalnum() or c in [' ', '.', '-', '_'] else '_' for c in child_title)
                
                # Get child page content
                child_content = self.notion_client.get_page_content(child_id)
                
                # Convert blocks to markdown
                child_markdown = self.markdown_converter.notion_blocks_to_markdown(child_content)
                
                # Save to file
                with open(f"{safe_title}.md", "w", encoding="utf-8") as f:
                    f.write(f"# {child_title}\n\n{child_markdown}")
                
                console.print(f"[green]Saved child page {child_title} to {safe_title}.md[/green]")
            
            console.print(f"[green]Successfully pulled page and {len(child_pages)} child pages from Notion[/green]")
            return True
            
        except Exception as e:
            console.print(f"[bold red]Error pulling from Notion: {e}[/bold red]")
            return False
    
    def status(self):
        """Check status of local changes compared to the last commit"""
        # Get config to find last commit
        config = self.load_config()
        
        if "last_commit" not in config:
            # No commits yet
            files = self.get_markdown_files()
            return {
                "no_commits": True,
                "all_files": [str(f) for f in files]
            }
        
        # Load the last commit
        last_commit = config["last_commit"]
        commit_file = self.config_dir / "commits" / f"{last_commit.replace(':', '-')}.json"
        
        if not commit_file.exists():
            return {
                "error": f"Commit file not found: {commit_file}"
            }
        
        # Load commit data
        with open(commit_file, "r", encoding="utf-8") as f:
            commit_data = json.load(f)
        
        # Create a dictionary of last committed files
        last_commit_files = {}
        for file_data in commit_data["files"]:
            last_commit_files[file_data["path"]] = file_data["content"]
        
        # Get current files
        current_files = self.get_markdown_files()
        
        # Compare files
        from ..utils.helpers import get_file_changes
        changes = get_file_changes(last_commit_files, current_files)
        
        # Add in last commit info
        changes["changes_since_last_commit"] = any(changes.values())
        changes["last_commit"] = commit_data["timestamp"]
        
        return changes 