"""
Command-line interface for the Condeco team area booking system.
"""

import click
import logging
import datetime
import sys
from pathlib import Path
from typing import List
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler
from rich.progress import Progress
from rich import print as rprint

from .auth import CondecoAuth, get_auth_token
from .booking import TeamAreaBooker, TeamAreaConfig, get_tuesday_wednesday_dates, BookingResult

console = Console()

def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(name)s - %(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(rich_tracebacks=True, show_path=False),
            logging.FileHandler("team_booker.log")
        ]
    )

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose: bool):
    """Condeco Team Area Booking System
    
    Automatically book team areas for Tuesdays and Wednesdays with secure authentication.
    """
    setup_logging(verbose)

@cli.command()
@click.option('--unique-key', help='Condeco unique key (e.g., company.condecosoftware.com)')
def setup(unique_key: str):
    """Set up initial authentication with Condeco."""
    auth = CondecoAuth(unique_key)
    
    if auth.is_setup_complete():
        if not click.confirm("Authentication is already set up. Do you want to reconfigure?"):
            return
        auth.clear_credentials()
    
    success = auth.setup_initial_auth()
    
    if success:
        console.print("\n[green]✓ Setup completed successfully![/green]")
        console.print("You can now use 'team-booker book' to start booking team areas.")
    else:
        console.print("\n[red]✗ Setup failed. Please try again.[/red]")
        sys.exit(1)

@cli.command()
@click.option('--location-id', required=True, help='Condeco location ID')
@click.option('--group-id', required=True, help='Condeco group ID') 
@click.option('--user-id', required=True, help='Condeco user ID')
@click.option('--floor-id', help='Condeco floor ID (optional)')
@click.option('--keywords', default='team,collaboration,meeting,huddle', help='Comma-separated keywords to identify team areas')
@click.option('--preferred-rooms', help='Comma-separated list of preferred room names')
@click.option('--weeks', default=4, help='Number of weeks ahead to book (default: 4)')
@click.option('--dry-run', is_flag=True, help='Show what would be booked without actually booking')
@click.option('--mock', is_flag=True, help='Use mock Condeco API for testing (no real API calls)')
@click.option('--date', 'specific_dates', multiple=True, help='Specific date to book (YYYY-MM-DD format)')
def book(
    location_id: str,
    group_id: str, 
    user_id: str,
    floor_id: str,
    keywords: str,
    preferred_rooms: str,
    weeks: int,
    dry_run: bool,
    mock: bool,
    specific_dates: List[str]
):
    """Book team areas for upcoming Tuesdays and Wednesdays."""
    
    # Check authentication (skip for mock mode)
    if mock:
        access_token = "mock_token_12345"
        config = {"unique_key": "mock.condecosoftware.com"}
        console.print("[yellow]ℹ️  Skipping authentication check in mock mode[/yellow]")
    else:
        auth = CondecoAuth()
        if not auth.is_setup_complete():
            console.print("[red]Authentication not set up. Run 'team-booker setup' first.[/red]")
            sys.exit(1)
        
        if not auth.validate_token():
            console.print("[red]Authentication token is invalid or expired. Run 'team-booker setup' to re-authenticate.[/red]")
            sys.exit(1)
        
        access_token = auth.get_token()
        config = auth.get_config()
    
    # Set up booking configuration
    team_config = TeamAreaConfig(
        location_id=location_id,
        group_id=group_id,
        user_id=user_id,
        floor_id=floor_id,
        team_area_keywords=keywords.split(',') if keywords else [],
        preferred_rooms=preferred_rooms.split(',') if preferred_rooms else []
    )
    
    # Initialize Condeco and booker  
    if mock:
        from .mock_condeco import MockCondeco
        condeco = MockCondeco(unique_key=config.get('unique_key', 'mock.condecosoftware.com'))
        console.print("[yellow]🧪 Using Mock Condeco API for testing[/yellow]")
    else:
        try:
            from .booking import _import_condeco
            Condeco = _import_condeco()
        except ImportError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        
        condeco = Condeco(unique_key=config['unique_key'])
    booker = TeamAreaBooker(condeco, team_config)
    
    # Determine dates to book
    if specific_dates:
        try:
            dates = [datetime.datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in specific_dates]
        except ValueError as e:
            console.print(f"[red]Invalid date format: {e}[/red]")
            sys.exit(1)
    else:
        dates = get_tuesday_wednesday_dates(weeks)
    
    if not dates:
        console.print("[yellow]No dates to book.[/yellow]")
        return
    
    # Display booking plan
    if mock and dry_run:
        mode = "[yellow]🧪 MOCK + DRY RUN[/yellow]"
    elif mock:
        mode = "[yellow]🧪 MOCK MODE[/yellow]"
    elif dry_run:
        mode = "[yellow]DRY RUN[/yellow]"
    else:
        mode = "[blue]LIVE BOOKING[/blue]"
    
    console.print(f"\n{mode} - Planning to book team areas:")
    
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Date")
    table.add_column("Day")
    table.add_column("Status")
    
    for date in dates:
        day_name = date.strftime('%A')
        status = "Planned" if not dry_run else "Will simulate"
        table.add_row(str(date), day_name, status)
    
    console.print(table)
    
    if not dry_run and not click.confirm(f"\nProceed with booking {len(dates)} dates?"):
        console.print("Booking cancelled.")
        return
    
    # Perform bookings
    console.print(f"\n{'Simulating' if dry_run else 'Starting'} booking process...")
    
    with Progress() as progress:
        task = progress.add_task("Booking team areas...", total=len(dates))
        
        results = []
        for date in dates:
            progress.update(task, description=f"Processing {date}...")
            result = booker.book_date(access_token, date) if not dry_run else \
                     booker.book_multiple_dates(access_token, [date], dry_run=True)[0]
            results.append(result)
            progress.advance(task)
    
    # Display results
    console.print(f"\n{mode} Results:")
    
    results_table = Table(show_header=True, header_style="bold blue")
    results_table.add_column("Date")
    results_table.add_column("Status") 
    results_table.add_column("Room")
    results_table.add_column("Message")
    
    success_count = 0
    for result in results:
        if result.result == BookingResult.SUCCESS:
            status = "[green]✓ Success[/green]"
            success_count += 1
        elif result.result == BookingResult.NO_AVAILABILITY:
            status = "[yellow]⚠ No availability[/yellow]"
        else:
            status = "[red]✗ Failed[/red]"
        
        room_info = result.room_name or "N/A"
        if result.booking_id:
            room_info += f" (#{result.booking_id})"
        
        results_table.add_row(
            str(result.date),
            status,
            room_info,
            result.message
        )
    
    console.print(results_table)
    
    # Summary
    total = len(results)
    console.print(f"\nSummary: {success_count}/{total} bookings {'would succeed' if dry_run else 'successful'}")
    
    if not dry_run and success_count > 0:
        console.print("[green]Team areas booked successfully! Check your Condeco calendar.[/green]")

@cli.command()
def status():
    """Check authentication status and configuration."""
    auth = CondecoAuth()
    config = auth.get_config()
    
    console.print("[bold blue]Authentication Status[/bold blue]")
    
    if auth.is_setup_complete():
        console.print("[green]✓ Authentication configured[/green]")
        console.print(f"Email: {config.get('email', 'Unknown')}")
        console.print(f"Unique Key: {config.get('unique_key', 'Unknown')}")
        
        if auth.validate_token():
            console.print("[green]✓ Token valid[/green]")
        else:
            console.print("[yellow]⚠ Token invalid or expired[/yellow]")
    else:
        console.print("[red]✗ Authentication not configured[/red]")
        console.print("Run 'team-booker setup' to configure authentication.")

@cli.command()
def clear():
    """Clear all stored credentials and configuration."""
    if click.confirm("This will clear all stored credentials. Continue?"):
        auth = CondecoAuth()
        auth.clear_credentials()

if __name__ == '__main__':
    cli()