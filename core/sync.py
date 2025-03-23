import json
import os
from pathlib import Path
from datetime import datetime
import hashlib
from slugify import slugify

from ..utils.console import print_info, print_success, print_error, print_warning
from ..utils.helpers import extract_front_matter
from .notion_client import NotionClient


class NotionSync:
    """Main class for syncing between Notion and local markdown files"""

    def __init__(self, api_key=None, page_id=None, database_id=None):
        """Initialize NotionSync

        Args:
            api_key (str, optional): Notion API key. If None, will try to get from environment.
            page_id (str, optional): Notion page ID. If None, will try to get from environment.
            database_id (str, optional): Notion database ID. If None, will try to get from environment.
        """
        self.notion_client = NotionClient(api_key)
        self.page_id = page_id
        self.database_id = database_id
        
        # Create config directory if it doesn't exist
        self.config_dir = Path(".notionsync")
        self.config_dir.mkdir(exist_ok=True)
        
        # Create commits directory if it doesn't exist
        self.commits_dir = self.config_dir / "commits"
        self.commits_dir.mkdir(exist_ok=True)

    def push(self):
        """Push local changes to Notion
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if we're pushing to a page or database
        if self.page_id:
            return self.push_to_page(self.page_id)
        elif self.database_id:
            return self.push_to_database(self.database_id)
        else:
            print_error("No page_id or database_id provided")
            return False

    def pull(self):
        """Pull changes from Notion
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if we're pulling from a page or database
        if self.page_id:
            return self.pull_from_page(self.page_id)
        elif self.database_id:
            return self.pull_from_database(self.database_id)
        else:
            print_error("No page_id or database_id provided")
            return False

    def status(self):
        """Check status of local changes compared to last commit
        
        Returns:
            dict: Status information with counts of added, modified, and deleted files
        """
        # Get last commit
        last_commit = self._get_last_commit()
        
        # Get current files
        current_files = self._get_current_files()
        
        # Compare
        if not last_commit:
            print_info("No commits found. All files will be added in the next commit.")
            status = {
                "added": list(current_files.keys()),
                "modified": [],
                "deleted": []
            }
            return status
        
        # Find added, modified, and deleted files
        added = []
        modified = []
        deleted = []
        
        for file_path, file_hash in current_files.items():
            if file_path not in last_commit:
                added.append(file_path)
            elif last_commit[file_path] != file_hash:
                modified.append(file_path)
        
        for file_path in last_commit:
            if file_path not in current_files:
                deleted.append(file_path)
        
        status = {
            "added": added,
            "modified": modified,
            "deleted": deleted
        }
        
        return status

    def commit(self):
        """Commit current state of local files
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self._save_commit()

    def push_to_page(self, page_id):
        """Push local changes to a Notion page
        
        Args:
            page_id (str): The ID of the Notion page to push to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate page ID
            if not page_id:
                print_error("Page ID is required for pushing to a page")
                return False
                
            print_info(f"Pushing to Notion page with ID: {page_id}")
            
            # Get the current status
            status = self.status()
            
            # Check if we have an index.md file for the main page content
            index_path = Path("index.md")
            if index_path.exists():
                with open(index_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Extract front matter if present
                front_matter, markdown_content = extract_front_matter(content)
                
                # Update the page with markdown content
                success = self.notion_client.update_page(page_id, markdown_content)
                if success:
                    print_success(f"Updated main page content from {index_path}")
                else:
                    print_error(f"Failed to update page with content from {index_path}")
                    return False
            
            # Process other markdown files as child pages
            for file_path in status["added"] + status["modified"]:
                path = Path(file_path)
                
                # Skip index.md as it's handled separately
                if path.name == "index.md":
                    continue
                    
                # Only process markdown files
                if path.suffix.lower() != ".md":
                    continue
                    
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Extract front matter
                front_matter, markdown_content = extract_front_matter(content)
                
                # Check if this is a new or existing child page
                if front_matter and "notion_id" in front_matter:
                    # Update existing page
                    child_id = front_matter["notion_id"]
                    success = self.notion_client.update_page(child_id, markdown_content)
                    if success:
                        print_success(f"Updated child page for {path}")
                    else:
                        print_error(f"Failed to update child page for {path}")
                else:
                    # Create new child page
                    child_title = front_matter.get("title", path.stem) if front_matter else path.stem
                    child_id = self.notion_client.create_page(page_id, child_title, markdown_content)
                    if child_id:
                        print_success(f"Created new child page for {path}")
                        
                        # Update the file with the new notion_id in front matter
                        if front_matter:
                            front_matter["notion_id"] = child_id
                        else:
                            front_matter = {"notion_id": child_id, "title": child_title}
                            
                        with open(path, "w", encoding="utf-8") as f:
                            f.write("---\n")
                            f.write(json.dumps(front_matter, indent=2))
                            f.write("\n---\n\n")
                            f.write(markdown_content)
                    else:
                        print_error(f"Failed to create child page for {path}")
            
            # Handle deleted files if they have a notion_id in front matter
            for file_path in status["deleted"]:
                path = Path(file_path)
                
                # Only process markdown files
                if path.suffix.lower() != ".md":
                    continue
                    
                # Try to get the last committed version
                last_commit = self._get_last_commit_data()
                if not last_commit:
                    continue
                    
                file_content = last_commit.get(str(path))
                if not file_content:
                    continue
                    
                # Extract front matter
                front_matter, _ = extract_front_matter(file_content)
                
                # Check if this file had a notion_id
                if front_matter and "notion_id" in front_matter:
                    # Archive the page in Notion
                    child_id = front_matter["notion_id"]
                    success = self.notion_client.archive_page(child_id)
                    if success:
                        print_success(f"Archived Notion page for deleted file {path}")
                    else:
                        print_warning(f"Failed to archive Notion page for deleted file {path}")
            
            # Save a new commit
            return self._save_commit()
            
        except Exception as e:
            print_error(f"Error pushing to page: {str(e)}")
            return False

    def push_to_database(self, database_id):
        """Push local changes to a Notion database
        
        Args:
            database_id (str): The ID of the Notion database to push to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate database ID
            if not database_id:
                print_error("Database ID is required for pushing to a database")
                return False
                
            print_info(f"Pushing to Notion database with ID: {database_id}")
            
            # Get the current status
            status = self.status()
            
            # Process markdown files for database entries
            for file_path in status["added"] + status["modified"]:
                path = Path(file_path)
                
                # Only process markdown files
                if path.suffix.lower() != ".md":
                    continue
                    
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Extract front matter
                front_matter, markdown_content = extract_front_matter(content)
                
                # Skip files without front matter
                if not front_matter:
                    print_warning(f"Skipping {path} - no front matter found")
                    continue
                    
                # Check if this is a new or existing database entry
                if "notion_id" in front_matter:
                    # Update existing entry
                    entry_id = front_matter["notion_id"]
                    properties = front_matter.get("properties", {})
                    success = self.notion_client.update_database_item(entry_id, properties, markdown_content)
                    if success:
                        print_success(f"Updated database entry for {path}")
                    else:
                        print_error(f"Failed to update database entry for {path}")
                else:
                    # Create new entry
                    title = front_matter.get("title", path.stem)
                    properties = front_matter.get("properties", {})
                    if not properties:
                        properties = {"Name": {"title": [{"text": {"content": title}}]}}
                        
                    entry_id = self.notion_client.create_database_item(database_id, properties, markdown_content)
                    if entry_id:
                        print_success(f"Created new database entry for {path}")
                        
                        # Update the file with the new notion_id in front matter
                        front_matter["notion_id"] = entry_id
                        
                        with open(path, "w", encoding="utf-8") as f:
                            f.write("---\n")
                            f.write(json.dumps(front_matter, indent=2))
                            f.write("\n---\n\n")
                            f.write(markdown_content)
                    else:
                        print_error(f"Failed to create database entry for {path}")
            
            # Handle deleted files if they have a notion_id in front matter
            for file_path in status["deleted"]:
                path = Path(file_path)
                
                # Only process markdown files
                if path.suffix.lower() != ".md":
                    continue
                    
                # Try to get the last committed version
                last_commit = self._get_last_commit_data()
                if not last_commit:
                    continue
                    
                file_content = last_commit.get(str(path))
                if not file_content:
                    continue
                    
                # Extract front matter
                front_matter, _ = extract_front_matter(file_content)
                
                # Check if this file had a notion_id
                if front_matter and "notion_id" in front_matter:
                    # Archive the database item in Notion
                    entry_id = front_matter["notion_id"]
                    success = self.notion_client.archive_database_item(entry_id)
                    if success:
                        print_success(f"Archived database entry for deleted file {path}")
                    else:
                        print_warning(f"Failed to archive database entry for deleted file {path}")
            
            # Save a new commit
            return self._save_commit()
            
        except Exception as e:
            print_error(f"Error pushing to database: {str(e)}")
            return False

    def pull_from_page(self, page_id):
        """Pull content from a Notion page to local markdown files

        Args:
            page_id (str): The ID of the Notion page to pull from

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate page ID
            if not page_id:
                print_error("Page ID is required for pulling from a page")
                return False
                
            print_info(f"Pulling content from Notion page with ID: {page_id}")
            
            # Get the page content
            page = self.notion_client.get_page(page_id)
            if not page:
                print_error(f"Failed to retrieve page with ID: {page_id}")
                return False
                
            # Get the page markdown content
            markdown_content = self.notion_client.get_page_content(page_id)
            
            # Save main page content to index.md
            index_path = Path("index.md")
            with open(index_path, "w", encoding="utf-8") as f:
                # Add front matter if page has properties
                if page.get("properties"):
                    front_matter = {
                        "notion_id": page_id,
                        "title": page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled"),
                        "last_edited_time": page.get("last_edited_time", "")
                    }
                    f.write("---\n")
                    f.write(json.dumps(front_matter, indent=2))
                    f.write("\n---\n\n")
                
                f.write(markdown_content)
                
            print_success(f"Saved page content to {index_path}")
            
            # Get child pages
            child_pages = self.notion_client.get_child_pages(page_id)
            for child in child_pages:
                child_id = child.get("id")
                child_title = child.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
                child_filename = f"{slugify(child_title)}.md"
                
                # Get child page content
                child_content = self.notion_client.get_page_content(child_id)
                
                # Save child page
                with open(child_filename, "w", encoding="utf-8") as f:
                    # Add front matter
                    front_matter = {
                        "notion_id": child_id,
                        "title": child_title,
                        "last_edited_time": child.get("last_edited_time", "")
                    }
                    f.write("---\n")
                    f.write(json.dumps(front_matter, indent=2))
                    f.write("\n---\n\n")
                    
                    f.write(child_content)
                    
                print_success(f"Saved child page to {child_filename}")
            
            # Save this version as a commit
            return self._save_commit()
            
        except Exception as e:
            print_error(f"Error pulling from page: {str(e)}")
            return False

    def pull_from_database(self, database_id):
        """Pull content from a Notion database to local markdown files

        Args:
            database_id (str): The ID of the Notion database to pull from

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate database ID
            if not database_id:
                print_error("Database ID is required for pulling from a database")
                return False
                
            print_info(f"Pulling content from Notion database with ID: {database_id}")
            
            # Get the database
            database = self.notion_client.get_database(database_id)
            if not database:
                print_error(f"Failed to retrieve database with ID: {database_id}")
                return False
                
            # Get database entries
            entries = self.notion_client.query_database(database_id)
            
            # Create folder for database if doesn't exist
            db_folder = Path("database")
            db_folder.mkdir(exist_ok=True)
            
            # Save database info
            db_info = {
                "notion_id": database_id,
                "title": database.get("title", [{}])[0].get("plain_text", "Untitled Database"),
                "properties": database.get("properties", {})
            }
            with open(db_folder / "database.json", "w", encoding="utf-8") as f:
                json.dump(db_info, f, indent=2)
                
            # Process each database entry
            for entry in entries:
                entry_id = entry.get("id")
                properties = entry.get("properties", {})
                
                # Extract title from properties (using the first title property found)
                title = "Untitled"
                for prop_name, prop_value in properties.items():
                    if prop_value.get("type") == "title" and prop_value.get("title"):
                        title = prop_value["title"][0]["plain_text"] if prop_value["title"] else "Untitled"
                        break
                
                # Create a filename from the title
                filename = f"{slugify(title)}.md"
                
                # Get page content
                content = self.notion_client.get_page_content(entry_id)
                
                # Save to file with front matter
                file_path = db_folder / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    # Add front matter with all properties
                    front_matter = {
                        "notion_id": entry_id,
                        "title": title,
                        "properties": properties,
                        "last_edited_time": entry.get("last_edited_time", "")
                    }
                    f.write("---\n")
                    f.write(json.dumps(front_matter, indent=2))
                    f.write("\n---\n\n")
                    
                    f.write(content)
                    
                print_success(f"Saved database entry to {file_path}")
            
            # Save this version as a commit
            return self._save_commit()
            
        except Exception as e:
            print_error(f"Error pulling from database: {str(e)}")
            return False

    def _get_current_files(self):
        """Get current markdown files with their hash
        
        Returns:
            dict: Dictionary of file paths to their hash
        """
        files = {}
        
        # Walk through all files in the current directory
        for root, _, filenames in os.walk("."):
            # Skip the .notionsync directory
            if ".notionsync" in root:
                continue
                
            for filename in filenames:
                # Only include markdown files
                if not filename.endswith(".md"):
                    continue
                    
                file_path = os.path.join(root, filename)
                # Remove ./ from the start if present
                if file_path.startswith("./"):
                    file_path = file_path[2:]
                    
                with open(file_path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    
                files[file_path] = file_hash
                
        return files

    def _get_last_commit(self):
        """Get the last commit information
        
        Returns:
            dict: Dictionary of file paths to their hash, or None if no commits
        """
        # Get all commit files
        commit_files = list(self.commits_dir.glob("*.json"))
        if not commit_files:
            return None
            
        # Sort by timestamp in filename
        commit_files.sort(key=lambda x: x.stem)
        
        # Get the latest commit
        latest_commit = commit_files[-1]
        
        # Load the commit data
        with open(latest_commit, "r", encoding="utf-8") as f:
            commit_data = json.load(f)
            
        return commit_data.get("files", {})

    def _get_last_commit_data(self):
        """Get the last commit data with file contents
        
        Returns:
            dict: Dictionary of file paths to their content, or None if no commits
        """
        # Get all commit files
        commit_files = list(self.commits_dir.glob("*.json"))
        if not commit_files:
            return None
            
        # Sort by timestamp in filename
        commit_files.sort(key=lambda x: x.stem)
        
        # Get the latest commit
        latest_commit = commit_files[-1]
        
        # Load the commit data
        with open(latest_commit, "r", encoding="utf-8") as f:
            commit_data = json.load(f)
            
        return commit_data.get("file_contents", {})

    def _save_commit(self):
        """Save current state as a commit
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get current files
            files = self._get_current_files()
            
            # Get file contents for reference
            file_contents = {}
            for file_path in files:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_contents[file_path] = f.read()
            
            # Create commit data
            commit_data = {
                "timestamp": datetime.now().isoformat(),
                "files": files,
                "file_contents": file_contents
            }
            
            # Create commit filename with timestamp
            commit_filename = f"{int(datetime.now().timestamp())}.json"
            commit_path = self.commits_dir / commit_filename
            
            # Save commit data
            with open(commit_path, "w", encoding="utf-8") as f:
                json.dump(commit_data, f, indent=2)
                
            print_success(f"Saved commit to {commit_path}")
            return True
            
        except Exception as e:
            print_error(f"Error saving commit: {str(e)}")
            return False 