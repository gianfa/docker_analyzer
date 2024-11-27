import click

from docker_analyzer import config
from docker_analyzer.analysis import (
    compare_duplicated,
    compare_non_shared_layers,
    compare_number_of_layers,
    compare_shared_layers,
    compare_total_sizes,
)
from docker_analyzer.cli import utils
from docker_analyzer.logger import get_logger

logger = get_logger(__name__)

CLI_USE_RICH = config.CLI_USE_RICH
RICH_STYLE = config.CLI_RICH_STYLE


@click.group()
def compare():
    """Group of commands for comparing Docker image layers."""
    pass


@compare.command(help=compare_shared_layers.__doc__)
@click.argument("img_name_1")
@click.argument("img_name_2")
@click.option("--to-json", is_flag=True, help="Output the result as JSON.")
def shared_layers(img_name_1, img_name_2, to_json):
    """Compare shared layers between two images and display the result as a table or JSON."""
    result = compare_shared_layers(img_name_1, img_name_2, "Size_MB")
    utils.render_dataframe(result, "Compare Shared Layers", to_json)


@compare.command(help=compare_duplicated.__doc__)
@click.argument("img_name_1")
@click.argument("img_name_2")
@click.option("--to-json", is_flag=True, help="Output the result as JSON.")
def duplicated_layers(img_name_1, img_name_2, to_json):
    """Compare duplicated layers between two images and display the result as a table or JSON."""
    result = compare_duplicated(img_name_1, img_name_2)
    utils.render_dataframe(result, "Compare Duplicated Layers", to_json)


@compare.command(help=compare_number_of_layers.__doc__)
@click.argument("img_name_1")
@click.argument("img_name_2")
@click.option("--to-json", is_flag=True, help="Output the result as JSON.")
def number_of_layers(img_name_1, img_name_2, to_json):
    """Compare number of layers between two images and display the result as a table or JSON."""
    result = compare_number_of_layers(img_name_1, img_name_2)
    utils.render_dataframe(result, "Compare Number of Layers", to_json)


@compare.command(help=compare_total_sizes.__doc__)
@click.argument("img_name_1")
@click.argument("img_name_2")
@click.option("--to-json", is_flag=True, help="Output the result as JSON.")
def total_sizes(img_name_1, img_name_2, to_json):
    """Compares the total sizes of two Docker images."""
    result = compare_total_sizes(img_name_1, img_name_2)
    utils.render_dataframe(result, title=f"Compare Total Sizes [MB]", to_json=to_json)


@compare.command(help=compare_non_shared_layers.__doc__)
@click.argument("img_name_1")
@click.argument("img_name_2")
@click.option("--to-json", is_flag=True, help="Output the result as JSON.")
def non_shared_layers(img_name_1, img_name_2, to_json):
    """Compares the non-shared layers between two Docker images."""
    result = compare_non_shared_layers(img_name_1, img_name_2, "Size_MB")
    utils.render_dataframe(result, title=f"Compare Non-Shared Layers", to_json=to_json)
