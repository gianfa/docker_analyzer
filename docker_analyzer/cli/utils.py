""" Utilities for CLI

"""

import click
import pandas as pd
from rich.box import HEAVY_EDGE
from rich.console import Console
from rich.table import Table

from docker_analyzer import config
from docker_analyzer.logger import get_logger

logger = get_logger(__name__)

console = Console()

CLI_USE_RICH = config.CLI_USE_RICH
RICH_STYLE = config.CLI_RICH_STYLE


def render_df_with_rich(df: pd.DataFrame, title: str):
    table = Table(title=title, box=HEAVY_EDGE, show_lines=True)

    header_style = RICH_STYLE["header"]
    for column in df.columns:
        if column == "CreatedBy":
            align = "left"
        else:
            align = "center"

        table.add_column(column, justify=align, style="cyan", header_style=header_style)

    row_styles = RICH_STYLE["columns"]
    for i, row in enumerate(df.itertuples(index=False)):
        style = row_styles[i % len(row_styles)]
        table.add_row(
            *[
                f"[bold green]{value}" if isinstance(value, int) else str(value)
                for value in row
            ],
            style=style,
        )

    console.print(table)


def render_dataframe(df: pd.DataFrame, title: str, to_json: bool = False):
    """Render a DataFrame as a table using Rich, or print it as JSON if --to-json is specified."""

    if to_json:
        print(df.to_json(orient="records", indent=4))
    elif CLI_USE_RICH:
        render_df_with_rich(df, title)
    else:
        print(f"\n--- {title} ---\n")
        print(df)


def ansi_color(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"


class ColoredGroup(click.Group):
    def format_help(self, ctx, formatter):
        # Colorize the group name in help text
        original_help = super().get_help(ctx)
        colored_group_name = ansi_color(self.name, "32")  # Apply green color
        return original_help.replace(self.name, colored_group_name)
