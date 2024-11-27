import os
import platform
from pathlib import Path

import toml


def get_default_temp_dir():
    """
    Return the default temporary directory based on the platform.

    Returns
    -------
    str
        Path to the temporary directory.
    """
    system = platform.system()

    if system in ["Linux", "Darwin"]:
        return Path.home() / "docker_analyzer_temp"
    elif system == "Windows":
        return Path.home() / "docker_analyzer_temp"
    else:
        # Fallback for other systems
        return Path.home() / "docker_analyzer_temp"


def get_version_from_pyproject():
    """Retrieve the version from pyproject.toml using toml library."""
    with open("pyproject.toml", "r") as file:
        pyproject_data = toml.load(file)
        return pyproject_data["tool"]["poetry"]["version"]
    return "Unknown"


def get_version_from_init():
    """Retrieve the version from __init__.py."""
    from docker_analyzer import __version__  # Importa dal pacchetto completo

    return __version__
