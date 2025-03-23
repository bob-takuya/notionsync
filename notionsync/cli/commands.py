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

def init_command(options, ctx=None):
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
    return True

def status_command(options, ctx=None):
    """Show status of local files compared to last commit"""
    # Load environment variables
    env = load_env_variables()
    
    # Initialize NotionSync
    sync = NotionSync(
        api_key=env["api_key"],
        page_id=env["page_id"],
        database_id=env["database_id"]
    )
    
    # Get status
    status = sync.status()
    
    # Display results in a table
    if not any(status.values()):
        console.print("[green]Working directory clean, nothing to commit.[/green]")
        return status
    
    console.print(f"[yellow]Changes since last commit:[/yellow]")
    
    # Added files
    if status["added"]:
        table = Table(title="New Files")
        table.add_column("File", style="green")
        
        for file_path in status["added"]:
            table.add_row(str(file_path))
        
        console.print(table)
    
    # Modified files
    if status["modified"]:
        table = Table(title="Modified Files")
        table.add_column("File", style="yellow")
        
        for file_path in status["modified"]:
            table.add_row(str(file_path))
        
        console.print(table)
    
    # Deleted files
    if status["deleted"]:
        table = Table(title="Deleted Files")
        table.add_column("File", style="red")
        
        for file_path in status["deleted"]:
            table.add_row(str(file_path))
        
        console.print(table)
    
    return status

def commit_command(options, ctx=None):
    """Commit changes to local storage"""
    message = options.get("message")
    if not message:
        console.print("[red]Error: Commit message is required[/red]")
        return None
        
    # Load environment variables
    env = load_env_variables()
    
    # Initialize NotionSync
    sync = NotionSync(
        api_key=env["api_key"],
        page_id=env["page_id"],
        database_id=env["database_id"]
    )
    
    # Commit changes
    return sync.commit(message)

def push_command(options, ctx=None):
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
    return sync.push()

def pull_command(options, ctx=None):
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
    return sync.pull()

def log_command(options, ctx=None):
    """Show commit history"""
    # Load environment variables
    env = load_env_variables()
    
    # Initialize NotionSync
    sync = NotionSync(
        api_key=env["api_key"],
        page_id=env["page_id"],
        database_id=env["database_id"]
    )
    
    # List commits
    commits_dir = sync.config_dir / "commits"
    if not commits_dir.exists():
        console.print("[yellow]No commits found.[/yellow]")
        return []
    
    commit_files = sorted(commits_dir.glob("*.json"), reverse=True)
    
    table = Table(title="Commit History")
    table.add_column("Date", style="cyan")
    table.add_column("Message", style="green")
    table.add_column("Files", style="yellow")
    
    log_entries = []
    
    for commit_file in commit_files:
        # Load commit data
        with open(commit_file, "r", encoding="utf-8") as f:
            commit_data = json.load(f)
        
        timestamp = commit_data["timestamp"]
        message = commit_data["message"]
        file_count = len(commit_data["files"])
        
        log_entry = f"{timestamp}: {message} ({file_count} files)"
        log_entries.append(log_entry)
        
        table.add_row(timestamp, message, str(file_count))
    
    console.print(table)
    return log_entries

@cli.command()
def init():
    """Initialize a new NotionSync project"""
    return init_command({})

@cli.command()
def status():
    """Show status of local files compared to last commit"""
    return status_command({})

@cli.command()
@click.option("-m", "--message", required=True, help="Commit message")
def commit(message):
    """Commit changes to local storage"""
    return commit_command({"message": message})

@cli.command()
def push():
    """Push committed changes to Notion"""
    return push_command({})

@cli.command()
def pull():
    """Pull content from Notion to local files"""
    return pull_command({})

@cli.command()
def log():
    """Show commit history"""
    return log_command({})

def main():
    """Main entry point for the CLI"""
    cli() 