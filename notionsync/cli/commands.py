"""
NotionSync - CLI Commands

This module provides CLI commands for NotionSync.
"""

import os
import json
import click
from rich.console import Console
from rich.table import Table
from pathlib import Path

from ..core.sync import NotionSync
from ..utils.helpers import load_env_variables, get_file_changes

# Initialize rich console for better output formatting
console = Console()

@click.group()
def cli():
    """NotionSync - A Git-like CLI tool for syncing Markdown files with Notion pages"""
    pass

@cli.command()
@click.option("-m", "--message", required=True, help="Commit message")
def commit(message):
    """Commit changes to local storage"""
    # Load environment variables
    env = load_env_variables()
    
    # Initialize NotionSync
    sync = NotionSync(
        api_key=env["api_key"],
        page_id=env["page_id"],
        database_id=env["database_id"]
    )
    
    # Commit changes
    sync.commit(message)

@cli.command()
def status():
    """Show status of local files compared to last commit"""
    # Load environment variables
    env = load_env_variables()
    
    # Initialize NotionSync
    sync = NotionSync(
        api_key=env["api_key"],
        page_id=env["page_id"],
        database_id=env["database_id"]
    )
    
    # Get config to find last commit
    config = sync.load_config()
    
    if "last_commit" not in config:
        console.print("[yellow]No commits found. This is a new project.[/yellow]")
        console.print("\nAll files will be added in the next commit.")
        
        # Show all markdown files as new
        files = sync.get_markdown_files()
        
        if not files:
            console.print("[yellow]No markdown files found in the current directory.[/yellow]")
            return
        
        table = Table(title="New Files")
        table.add_column("File", style="green")
        
        for file_path in files:
            table.add_row(str(file_path))
        
        console.print(table)
        return
    
    # Get current files
    current_files = sync.get_markdown_files()
    
    # Load the last commit to compare
    last_commit = config["last_commit"]
    commit_file = sync.config_dir / "commits" / f"{last_commit.replace(':', '-')}.json"
    
    if not commit_file.exists():
        console.print(f"[bold red]Commit file not found: {commit_file}[/bold red]")
        return
    
    try:
        with open(commit_file, "r", encoding="utf-8") as f:
            commit_data = json.load(f)
        
        # Create a dictionary of last committed files
        last_commit_files = {}
        for file_data in commit_data["files"]:
            last_commit_files[file_data["path"]] = file_data["content"]
        
        # Compare files
        changes = get_file_changes(last_commit_files, current_files)
        
        # Display results in a table
        if not any(changes.values()):
            console.print("[green]Working directory clean, nothing to commit.[/green]")
            return
        
        console.print(f"[yellow]Changes since last commit ({commit_data['message']}):[/yellow]")
        
        # Added files
        if changes["added"]:
            table = Table(title="New Files")
            table.add_column("File", style="green")
            
            for file_path in changes["added"]:
                table.add_row(file_path)
            
            console.print(table)
        
        # Modified files
        if changes["modified"]:
            table = Table(title="Modified Files")
            table.add_column("File", style="yellow")
            
            for file_path in changes["modified"]:
                table.add_row(file_path)
            
            console.print(table)
        
        # Deleted files
        if changes["deleted"]:
            table = Table(title="Deleted Files")
            table.add_column("File", style="red")
            
            for file_path in changes["deleted"]:
                table.add_row(file_path)
            
            console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error checking status: {e}[/bold red]")

@cli.command()
def push():
    """Push committed changes to Notion"""
    # Load environment variables
    env = load_env_variables()
    
    # Initialize NotionSync
    sync = NotionSync(
        api_key=env["api_key"],
        page_id=env["page_id"],
        database_id=env["database_id"]
    )
    
    # Push changes
    sync.push()

@cli.command()
def pull():
    """Pull content from Notion to local files"""
    # Load environment variables
    env = load_env_variables()
    
    # Initialize NotionSync
    sync = NotionSync(
        api_key=env["api_key"],
        page_id=env["page_id"],
        database_id=env["database_id"]
    )
    
    # Pull changes
    sync.pull()

@cli.command()
def log():
    """Show commit history"""
    # Load environment variables
    env = load_env_variables()
    
    # Initialize NotionSync
    sync = NotionSync(
        api_key=env["api_key"],
        page_id=env["page_id"],
        database_id=env["database_id"]
    )
    
    # Get config to find last commit
    config = sync.load_config()
    
    if "last_commit" not in config:
        console.print("[yellow]No commits found.[/yellow]")
        return
    
    # List commits
    commits_dir = sync.config_dir / "commits"
    if not commits_dir.exists():
        console.print("[yellow]No commits found.[/yellow]")
        return
    
    commit_files = sorted(commits_dir.glob("*.json"), reverse=True)
    
    table = Table(title="Commit History")
    table.add_column("Date", style="cyan")
    table.add_column("Message", style="green")
    table.add_column("Files", style="yellow")
    
    for commit_file in commit_files:
        # Load commit data
        with open(commit_file, "r", encoding="utf-8") as f:
            commit_data = json.load(f)
        
        timestamp = commit_data["timestamp"]
        message = commit_data["message"]
        file_count = len(commit_data["files"])
        
        table.add_row(timestamp, message, str(file_count))
    
    console.print(table)

@cli.command()
def init():
    """Initialize a new NotionSync project"""
    # Create .env file if it doesn't exist
    env_path = Path(".env")
    if not env_path.exists():
        console.print("[yellow]Creating .env file...[/yellow]")
        with open(env_path, "w") as f:
            f.write("NOTION_API_KEY=your_notion_api_key_here\n")
            f.write("NOTION_PAGE_URL=https://www.notion.so/your_page_url\n")
            f.write("# NOTION_DATABASE_ID=your_database_id_here\n")
        console.print("[green]Created .env file. Please edit it with your Notion API credentials.[/green]")
    
    # Load environment variables
    env = load_env_variables()
    
    # Initialize NotionSync
    sync = NotionSync(
        api_key=env["api_key"],
        page_id=env["page_id"],
        database_id=env["database_id"]
    )
    
    # Create index.md if it doesn't exist
    sync.create_index_md_if_missing()
    
    console.print("[green]NotionSync project initialized successfully.[/green]")
    console.print("[yellow]Don't forget to edit .env with your Notion API key and page URL.[/yellow]")

def main():
    """Main entry point for the CLI"""
    cli() 