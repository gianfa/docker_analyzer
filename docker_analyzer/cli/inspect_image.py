"""Single Docker image Inspection
"""

from pathlib import Path

import click
from rich.console import Console

from docker_analyzer import config
from docker_analyzer.cli import utils
from docker_analyzer.inspection import (
    compare_layers_files,
    extract_image_tar,
    get_layer_hashes_from_extracted_tar,
    inspect_all_image_layers_and_get_files_from_extracted_tar,
    inspect_files_in_layer,
    save_docker_image,
)
from docker_analyzer.logger import get_logger

logger = get_logger(__name__)

CLI_USE_RICH = config.CLI_USE_RICH
RICH_STYLE = config.CLI_RICH_STYLE

console = Console()


def get_image_tar(image_name, overwrite: bool = False) -> str:
    tar_path = save_docker_image(image_name, overwrite=overwrite)
    return extract_image_tar(tar_path, overwrite=overwrite)


@click.group(cls=utils.ColoredGroup)
def inspect_cmd():
    """Group of commands for inspecting single Docker image."""
    pass


@inspect_cmd.command(
    name="inspect-files", help="Inspect files from a Docker image tarball."
)
@click.argument("image_name")
def inspect_files(image_name):
    """Inspect the layers of a Docker image and list the files in each layer."""

    extracted_folder = get_image_tar(image_name)
    if extracted_folder:
        files_df = inspect_all_image_layers_and_get_files_from_extracted_tar(
            extracted_folder
        )
        utils.render_dataframe(files_df, title="Files in Docker Image Layers")
    else:
        console.print(
            f"[bold red]Failed to extract and inspect files from {image_name}[/bold red]"
        )


@inspect_cmd.command(
    name="layers-hash", help="Retrieve the layer hashes from a Docker image."
)
@click.argument("image_name")
def layers_hash(image_name):
    """Retrieve the list of layer hashes in build order from a Docker image."""
    extracted_folder = get_image_tar(image_name)
    if extracted_folder:
        layers_df = get_layer_hashes_from_extracted_tar(extracted_folder)
        utils.render_dataframe(layers_df, title="Layer Hashes in Docker Image")
    else:
        console.print(
            f"[bold red]Failed to extract and retrieve layer hashes from {image_name}[/bold red]"
        )


@inspect_cmd.command(
    name="compare-layers", help="Compare files between two Docker image layers."
)
@click.argument("image_name")
@click.argument("layer_hash_1")
@click.argument("layer_hash_2")
def compare_layers(image_name, layer_hash_1, layer_hash_2):
    """Compare the files added, removed, and modified between two Docker image layers."""
    extracted_folder = extract_image_tar(image_name)
    if extracted_folder:
        files_df = inspect_all_image_layers_and_get_files_from_extracted_tar(
            extracted_folder
        )
        added, removed, modified = compare_layers_files(
            files_df, layer_hash_1, layer_hash_2
        )
        console.print(f"[bold cyan]Files added in {layer_hash_2}[/bold cyan]:")
        utils.render_dataframe(added, "Added Files")
        console.print(f"[bold cyan]Files removed in {layer_hash_2}[/bold cyan]:")
        utils.render_dataframe(removed, "Removed Files")
        console.print(
            f"[bold cyan]Files modified between {layer_hash_1} and {layer_hash_2}[/bold cyan]:"
        )
        utils.render_dataframe(modified, "Modified Files")
    else:
        console.print(
            f"[bold red]Failed to compare layers {layer_hash_1} and {layer_hash_2}[/bold red]"
        )


@inspect_cmd.command(
    name="list-files-in-layer", help="List all files in a specific Docker image layer."
)
@click.argument("image_name")
@click.argument("layer_hash")
def list_files_in_layer(image_name, layer_hash):
    """List all files in a specific Docker image layer."""
    extracted_folder = extract_image_tar(image_name)
    if extracted_folder:
        layer_tar_path = Path(extracted_folder) / f"blobs/sha256/{layer_hash}/layer.tar"
        files_df = inspect_files_in_layer(layer_tar_path)
        utils.render_dataframe(files_df, title=f"Files in Layer {layer_hash}")
    else:
        console.print(
            f"[bold red]Failed to list files in layer {layer_hash}[/bold red]"
        )
