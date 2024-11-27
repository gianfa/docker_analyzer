"""Input/Output function
"""

import json
from pathlib import Path

import docker
import numpy as np
import pandas as pd

from docker_analyzer.logger import get_logger

logger = get_logger(__name__)


def bytes_to_mb(n):
    if pd.notnull(n) and np.isscalar(n):
        return n / (1024 * 1024)
    return n


def dump_image_history_to_json(image_name: str, output_json: str = None) -> str:
    """
    Retrieves the history of a Docker image and saves it to a JSON file if it doesn't already exist.

    Parameters:
        image_name (str): The name or ID of the Docker image.
        output_json (str): The path to the output JSON file. Defaults to 'image_name.json' if not provided.

    Returns:
        str: The path to the JSON file containing the image history.
    """
    client = docker.from_env()

    if type(image_name) != str:
        raise ValueError(f"Wrong image_name. It must be a str")

    if str(image_name).endswith(".json"):
        raise ValueError(
            f"Wrong image_name. It was actually a JSON file name: {image_name}"
        )

    if output_json is None:
        output_json = f"{image_name}.json"

    output_path = Path(output_json)

    if output_path.exists():
        logger.debug(f"File '{output_path}' already exists. Skipping creation.")
        return str(output_path)

    try:
        image = client.images.get(image_name)
        history = image.history()

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

        logger.info(f"History of image '{image_name}' saved to '{output_path}'.")

    except docker.errors.ImageNotFound:
        logger.error(f"Image '{image_name}' not found.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

    return str(output_path)


def read_history_json(fpath) -> pd.DataFrame:
    with open(fpath, "r", encoding="utf-8") as f1:
        history = json.load(f1)
    df = pd.DataFrame(history).iloc[::-1].reset_index(drop=True)

    # postprocess
    df["Size"] = pd.to_numeric(df["Size"], errors="coerce").astype(float)
    df.loc[:, "Size"] = df["Size"].apply(bytes_to_mb)
    df = df.rename(columns={"Size": "Size_MB"})

    df["Created_dt"] = pd.to_datetime(df["Created"], unit="s")
    return df


def get_image_history(image_name: str, json_path: str = None) -> pd.DataFrame:
    json_path = dump_image_history_to_json(image_name, json_path)
    return read_history_json(json_path)
