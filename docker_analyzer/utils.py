from pathlib import Path
from typing import List

import click
from anytree import Node, RenderTree
from anytree.exporter import DotExporter
from rich.console import Console
from rich.tree import Tree

from docker_analyzer.logger import get_logger

logger = get_logger(__name__)


def create_interactive_tree(file_paths: List[str]) -> Tree:
    """
    Create an interactive tree structure using Rich from a list of file paths.

    Parameters
    ----------
    file_paths : List[str]
        List of file paths as strings.

    Returns
    -------
    Tree
        The tree object built from the file paths.
    """
    root = Tree("Root")
    nodes = {"root": root}

    for file_path in file_paths:
        path_parts = Path(file_path).parts
        parent_node = root

        for part in path_parts:
            if part not in nodes:
                new_node = parent_node.add(part)
                nodes[part] = new_node
            parent_node = nodes[part]

    return root


def create_file_tree(file_paths: List[str]):
    """
    Create and display a tree structure from a list of file paths.

    Parameters
    ----------
    file_paths : List[str]
        List of file paths as strings.

    Returns
    -------
    None
    """
    root = Node("root")
    nodes = {"root": root}

    for file_path in file_paths:
        path_parts = Path(file_path).parts
        parent = root
        for part in path_parts:
            if part not in nodes:
                nodes[part] = Node(part, parent=parent)
            parent = nodes[part]

    # Print the tree
    for pre, fill, node in RenderTree(root):
        print(f"{pre}{node.name}")
