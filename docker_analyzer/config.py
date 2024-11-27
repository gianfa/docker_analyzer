""" Configuration settings for docker_analyzer

This module centralizes all configuration options, such as logging settings and file paths.
"""

import difflib
import logging
import os
from pathlib import Path

from docker_analyzer.defaults_utils import get_default_temp_dir, get_version_from_init

PROJECT_ROOT = Path(__file__).parent.resolve()

# --- Project Settings ---

AUTHOR_NAME = "Name"
AUTHOR_SURNAME = "Surname"
GITHUB_URL = "https://github.com/gianfa"
PROJECT_TITLE = "🔍docker_analyzer Dashboard"  # notused
VERSION = get_version_from_init()

# --- Image Selector Page ---

IMAGE_SELECTOR_TITLE = "Select Docker Images"
IMAGE_SELECTOR_SUBTITLE = "Select Docker Images to Compare"
IMAGE_SELECTOR_DESC = "Choose two Docker images from the dropdowns below"


# --- Logging Settings ---

LOG_FORMAT = {
    "-COMPLETE": "%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
    "|COMPLETE": "%(asctime)s|%(levelname)s|%(filename)s|%(funcName)s| %(message)s",
    "|EASY": "%(asctime)s | %(levelname)s | %(filename)s | %(message)s",
    "|LESS": "%(levelname)s | %(message)s",
}
"""LOG_FORMAT (dict)
Preconfigurated options for logger formatting
"""

RICH_STYLES = {
    "DOCKER_1": {
        "header": "bold yellow on blue",
        "columns": ["", "on grey15"],
    }
}
"""RICH_STYLES (dict)

"""

DEFAULT_LOG_FORMAT = LOG_FORMAT["|COMPLETE"]
LOG_LEVEL = logging.debug
LOG_FILE_PATH = ""  # "docker_analyzer.log"
LOG_MAX_SIZE = 1024 * 1024 * 5  # 5 MB
LOG_BACKUP_COUNT = 3

TEMP_DIR = get_default_temp_dir()
"""TEMP_DIR (str)
Temporary files directory
"""

LAYERS_SIMILARITY_FUNCTION = lambda layer_1, layer_2: int(
    difflib.SequenceMatcher(None, layer_1, layer_2).ratio() * 100
)
"""LAYERS_SIMILARITY_FUNCTION (function)
The similarity function to compare two layers commands, or 'CreatedBy' field.

Parameters
----------
x : str
    The first string to compare.
y : str
    The second string to compare.

Returns
-------
int
    The similarity ratio between `x` and `y`, expressed as an integer percentage (0-100).

Examples
--------
>>> LAYERS_SIMILARITY_FUNCTION("RUN| 5 echo 'first command'", "RUN| 5 echo 'second command'")
85
"""

LAYOUT_SIMILARITY_THRESHOLD = 50
"""LAYOUT_SIMILARITY_THRESHOLD (int)
Layout similarity threshold to show similar layers
"""

# --- WEB GUI ---

# WEB_APP_HOST = "http://127.0.0.1"
WEB_APP_HOST = "0.0.0.0"
WEB_APP_PORT = "5002"
WEB_APP_ADDRESS = f"{WEB_APP_HOST}:{WEB_APP_PORT}"

# --- CLI ---
CLI_USE_RICH = True
CLI_RICH_STYLE = RICH_STYLES["DOCKER_1"]

# --- Checks ---

temp_dir = Path(TEMP_DIR)
if not temp_dir.exists():
    temp_dir.mkdir(parents=True, exist_ok=True)
