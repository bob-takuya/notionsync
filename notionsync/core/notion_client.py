"""
NotionSync - Notion API Client Module

This module handles all interactions with the Notion API.
"""

import os
import json
from notion_client import Client
from rich.console import Console

# Initialize rich console for better output formatting
console = Console()

class NotionApiClient:
    """Notion API client for interacting with Notion"""
    
    def __init__(self, api_key=None, page_id=None, database_id=None):
        """Initialize the Notion API client"""
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.page_id = page_id
        self.database_id = database_id
        
        if not self.api_key:
            console.print("[bold red]Error: NOTION_API_KEY not found in environment variables.[/bold red]")
            raise ValueError("NOTION_API_KEY is required")
        
        self.client = Client(auth=self.api_key)
    
    def get_page(self, page_id):
        """Get a Notion page by ID"""
        try:
            return self.client.pages.retrieve(page_id=page_id)
        except Exception as e:
            console.print(f"[bold red]Error retrieving page: {e}[/bold red]")
            raise
    
    def update_page(self, page_id, properties=None, content=None):
        """Update a Notion page"""
        try:
            # Update page properties if provided
            if properties:
                self.client.pages.update(page_id=page_id, properties=properties)
            
            # Update page content if provided
            if content:
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=content
                )
            
            return True
        except Exception as e:
            console.print(f"[bold red]Error updating page: {e}[/bold red]")
            raise
    
    def get_database(self, database_id):
        """Get a Notion database by ID"""
        try:
            return self.client.databases.retrieve(database_id=database_id)
        except Exception as e:
            console.print(f"[bold red]Error retrieving database: {e}[/bold red]")
            raise
    
    def query_database(self, database_id, filter=None, sorts=None):
        """Query a Notion database"""
        try:
            return self.client.databases.query(
                database_id=database_id,
                filter=filter,
                sorts=sorts
            )
        except Exception as e:
            console.print(f"[bold red]Error querying database: {e}[/bold red]")
            raise
    
    def create_page(self, parent, properties, content=None):
        """Create a new Notion page"""
        try:
            page = self.client.pages.create(
                parent=parent,
                properties=properties
            )
            
            # Add content if provided
            if content and page:
                self.client.blocks.children.append(
                    block_id=page["id"],
                    children=content
                )
            
            return page
        except Exception as e:
            console.print(f"[bold red]Error creating page: {e}[/bold red]")
            raise
    
    def get_page_content(self, page_id):
        """Get the content blocks of a Notion page"""
        try:
            return self.client.blocks.children.list(block_id=page_id)["results"]
        except Exception as e:
            console.print(f"[bold red]Error retrieving page content: {e}[/bold red]")
            raise
    
    def delete_block(self, block_id):
        """Delete a Notion block"""
        try:
            return self.client.blocks.delete(block_id=block_id)
        except Exception as e:
            console.print(f"[bold red]Error deleting block: {e}[/bold red]")
            raise
    
    def get_child_pages(self, parent_page_id):
        """Get all child pages of a Notion page"""
        try:
            # Query for all child blocks
            blocks = self.client.blocks.children.list(block_id=parent_page_id)["results"]
            
            # Filter for child page blocks
            child_pages = []
            for block in blocks:
                if block["type"] == "child_page":
                    # Get the full page details
                    page_details = self.get_page(block["id"])
                    child_pages.append(page_details)
                elif block["type"] == "child_database":
                    # Future enhancement: handle child databases
                    console.print(f"[yellow]Found child database: {block['id']} (databases not fully supported yet)[/yellow]")
            
            return child_pages
        except Exception as e:
            console.print(f"[bold red]Error retrieving child pages: {e}[/bold red]")
            raise
    
    def clear_page_content(self, page_id):
        """Clear all content from a Notion page"""
        try:
            # Get all blocks
            blocks = self.get_page_content(page_id)
            
            # Delete each block
            for block in blocks:
                self.delete_block(block["id"])
            
            return True
        except Exception as e:
            console.print(f"[bold red]Error clearing page content: {e}[/bold red]")
            raise
    
    def create_database(self, parent, title, properties):
        """Create a new Notion database"""
        try:
            return self.client.databases.create(
                parent=parent,
                title=[{"text": {"content": title}}],
                properties=properties
            )
        except Exception as e:
            console.print(f"[bold red]Error creating database: {e}[/bold red]")
            raise 