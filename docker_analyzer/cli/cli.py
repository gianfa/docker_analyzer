"""CLI

Examples
--------

"""

import time
import webbrowser

import click
import docker
from rich.console import Console
from rich.table import Table

from docker_analyzer import config
from docker_analyzer.cli.compare import (
    compare,
    duplicated_layers,
    non_shared_layers,
    number_of_layers,
    shared_layers,
    total_sizes,
)
from docker_analyzer.cli.inspect_image import inspect_cmd
from docker_analyzer.gui import create_app
from docker_analyzer.logger import get_logger

console = Console()

logger = get_logger(__name__)


@click.group()
def cli():
    pass


@cli.command()
def web_gui():
    """Launch the web GUI to select images and perform analysis."""

    def open_browser():
        print("Attempting to open the browser...")
        time.sleep(2)
        webbrowser.open(config.WEB_APP_ADDRESS)

    app = create_app()
    logger.info("Flask app created.")

    try:
        logger.info(
            f"Running Flask app on {config.WEB_APP_HOST}:{config.WEB_APP_PORT}..."
        )
        app.run(
            host=config.WEB_APP_HOST,
            port=config.WEB_APP_PORT,
            use_reloader=False,
            debug=True,
        )
    except Exception as e:
        logger.error(f"Error running Flask: {e}")

    logger.info("Flask app has stopped.")


@cli.command(name="get-temp-dir", help="Print the temp directory used to inspect")
def get_temp_dir():
    return config.TEMP_DIR


@click.command(name="version", help="Show the version and exit.")
@click.option("--only-version", is_flag=True, help="Print only the version number.")
def version(only_version):
    """Command to show the version. Optionally, print only the version number."""
    version = config.VERSION

    if only_version:
        # Print only the version number
        console.print(version)
    else:
        # Print the full version message
        console.print(f"[bold cyan]docker_analyzer[/bold cyan] version {version}")


@click.command(
    name="list-images", help="List all Docker images with full name (tag or ID)."
)
def list_images():
    """Command to list all Docker images with their full name (tag or ID)."""
    client = docker.from_env()

    try:
        images = client.images.list()

        if not images:
            console.print(
                "[bold yellow]No Docker images found on the system.[/bold yellow]"
            )
            return

        # Create a table using rich to display images
        table = Table(title="Docker Images", show_lines=True)
        table.add_column("Image ID", justify="center", style="cyan")
        table.add_column("Full Name (Tag or ID)", justify="left", style="magenta")

        for image in images:
            # If the image has no tag, show the image ID
            full_name = image.tags[0] if image.tags else image.id
            table.add_row(image.id[:12], full_name)

        console.print(table)

    except docker.errors.DockerException as e:
        console.print(f"[bold red]Error:[/bold red] Failed to connect to Docker. {e}")


cli.add_command(list_images)
cli.add_command(version)

cli.add_command(inspect_cmd)  # group
cli.add_command(compare)  # group

if __name__ == "__main__":
    cli()
