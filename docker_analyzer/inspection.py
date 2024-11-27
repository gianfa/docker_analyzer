"""Inspection [WIP]
"""

import json
import os
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import docker
import pandas as pd

from docker_analyzer import config
from docker_analyzer.inspection_io import get_image_history
from docker_analyzer.logger import get_logger
from docker_analyzer.utils import create_interactive_tree

sys.path += [".."]


logger = get_logger(__name__)


def save_docker_image(
    image_name: str, output_file: str = None, overwrite: bool = False
) -> str:
    """
    Save a Docker image to a tarball using the docker-py client.

    Parameters
    ----------
    image_name : str
        Name or ID of the Docker image.
    output_file : str, optional
        Path to the output tar file. If None, a default path is used.
    overwrite : bool, optional
        If True, the file will be overwritten if it already exists.

    Returns
    -------
    str
        The path to the saved tar file.
    """
    client = docker.from_env()

    try:
        # Get the image object
        image = client.images.get(image_name)

        if output_file is None:
            output_file = Path(config.TEMP_DIR) / f"{image_name}.tar"
        output_file = Path(output_file)
        if not output_file.parent.is_dir():
            raise ValueError(
                f"{output_file.parent.resolve()} is not a valid directory "
                "to host tar files for Docker images"
            )

        if output_file.is_file() and not overwrite:
            return output_file

        # Save the image as a tarball
        with open(output_file, "wb") as f:
            for chunk in image.save(named=True):  # Save in OCI format
                f.write(chunk)

        logger.info(f"Docker image '{image_name}' saved to '{output_file}'.")

    except docker.errors.ImageNotFound:
        logger.error(f"Error: Docker image '{image_name}' not found.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    return str(output_file)


def extract_tar(tarball_path: str, output_dir: str) -> str:
    """
    Extracts files from a tarball to the specified directory.
    """
    try:
        with tarfile.open(tarball_path, "r") as tar:
            tar.extractall(output_dir)
            logger.debug(f"Extracted {tarball_path} to {output_dir}")
        return output_dir
    except Exception as e:
        logger.error(f"Error extracting {tarball_path}: {e}")
        return None


def extract_image_tar(
    tarball_path: str, output_dir: str = None, overwrite: bool = False
) -> str:
    """
    Extracts the files from a Docker image tarball.

    Parameters
    ----------
    tarball_path : str
        The path to the tarball of the Docker image.
    output_dir : str
        The directory where the tarball contents will be extracted.
    overwrite : bool
        If yes the directory will be overwritten if it already exists.
    """
    if output_dir is None:
        output_dir = Path(config.TEMP_DIR) / (Path(tarball_path).stem + "-tar")
    output_dir = Path(output_dir)
    if not output_dir.parent.is_dir():
        raise ValueError(
            f"{output_dir.parent.resolve()} is not a valid directory "
            "to host extracted tar files for Docker images"
        )

    if output_dir.is_dir() and not overwrite:
        return output_dir

    return extract_tar(tarball_path, output_dir)


def list_files_in_tar(tar: tarfile.TarFile) -> List[dict]:
    """
    Lists all files in a tarfile along with their sizes.

    Parameters
    ----------
    tar : tarfile.TarFile
        Opened tarfile object.

    Returns
    -------
    List[dict]
        List of dictionaries containing file paths and sizes.
    """
    file_info_list = []
    for member in tar.getmembers():
        file_info_list.append(
            {"FilePath": member.name, "FileSize_MB": round(member.size / (1024**2), 4)}
        )
    return file_info_list


def load_manifest_and_config_from_extracted_tar(
    extracted_folder: Path,
) -> Tuple[dict, dict]:
    """
    Loads the manifest and config files from the extracted folder.

    Returns
    -------
    Tuple[dict, dict] : manifest and config JSON objects.
    """
    manifest_file_path = extracted_folder / "manifest.json"
    if not manifest_file_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {extracted_folder}")

    with manifest_file_path.open("r") as manifest_file:
        manifest = json.load(manifest_file)

    config_file_path = extracted_folder / manifest[0]["Config"]
    if not config_file_path.exists():
        raise FileNotFoundError(f"Config file {config_file_path} not found.")

    with config_file_path.open("r") as config_file:
        config_json = json.load(config_file)

    return manifest, config_json


def inspect_files_in_layer(layer_tar_path: Path) -> pd.DataFrame:
    """
    Inspects the files in a Docker image layer tarball and returns a DataFrame
    with information about the files and their sizes.

    Parameters
    ----------
    layer_tar_path : Path
        The path to the Docker layer tarball.

    Returns
    -------
    pd.DataFrame
        DataFrame containing file information.
        Columns: FilePath, FileSize_MB.
    """
    files_info = []

    # Open the layer tarball to inspect the files inside
    with tarfile.open(layer_tar_path, "r") as layer_tarfile:
        for member in layer_tarfile.getmembers():
            # Get file size in MB
            file_size = member.size / (1024**2)  # Convert size to MB
            files_info.append(
                {"FilePath": member.name, "FileSize_MB": round(file_size, 4)}
            )

    return pd.DataFrame(files_info)


def inspect_all_image_layers_and_get_files_from_extracted_tar(
    extracted_folder_path: str,
) -> pd.DataFrame:
    """
    Inspects the layers of a Docker image from an extracted folder and returns a DataFrame
    with information about each layer's files, sizes, and creation commands.

    Parameters
    ----------
    extracted_folder_path : str
        The path to the extracted Docker image folder.

    Returns
    -------
    pd.DataFrame
        DataFrame containing layer and file information.
        Columns: LayerHash, FilePath, FileSize_MB, CreatedBy, Created_dt.
    """
    layers_info = []

    extracted_folder = Path(extracted_folder_path)

    # Path to the manifest.json file in the extracted folder
    manifest_file_path = extracted_folder / "manifest.json"

    if not manifest_file_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {extracted_folder}")

    # Load the manifest.json file
    with manifest_file_path.open("r") as manifest_file:
        manifest = json.load(manifest_file)

    # Path to the config file
    config_file_path = extracted_folder / manifest[0]["Config"]

    if not config_file_path.exists():
        raise FileNotFoundError(f"Config file {config_file_path} not found.")

    # Load the config.json file
    with config_file_path.open("r") as config_file:
        config_json = json.load(config_file)

    # Iterate through each layer in the manifest
    for layer_path in manifest[0]["Layers"]:
        layer_tar_path = extracted_folder / layer_path

        if not layer_tar_path.exists():
            logger.warning(f"Layer tarball {layer_tar_path} not found, skipping.")
            continue

        # Get the list of files and their sizes from the layer
        layer_files_df = inspect_files_in_layer(layer_tar_path)

        # Extract creation info from the config file
        created_by = config_json.get("container_config", {}).get("Cmd", "")
        created_dt = config_json.get("created", "")

        # Append the layer info to each file in the layer
        layer_files_df["LayerHash"] = layer_path.split("/")[
            2
        ]  # Extract hash from the layer path
        layer_files_df["CreatedBy"] = created_by
        layer_files_df["Created_dt"] = created_dt

        layers_info.append(layer_files_df)

    # Concatenate all layer info into a single DataFrame
    return pd.concat(layers_info, ignore_index=True)


def get_layer_hashes_from_extracted_tar(
    extracted_folder: Path,
) -> pd.DataFrame:
    """
    Retrieves the list of layer hashes from an extracted Docker image tarball in ascending build order,
    including empty layers.

    Parameters
    ----------
    extracted_folder : Path
        Path to the folder where the Docker image tarball was extracted.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the layer hashes, creation commands, and creation times in ascending order of build.
        Columns: LayerHash, CreatedBy, Created_dt
    """
    # Path to the manifest.json file in the extracted folder
    manifest_file_path = extracted_folder / "manifest.json"

    if not manifest_file_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {extracted_folder}")

    # Load the manifest.json file
    with manifest_file_path.open("r") as manifest_file:
        manifest = json.load(manifest_file)

    # Path to the config file
    config_file_path = extracted_folder / manifest[0]["Config"]

    if not config_file_path.exists():
        raise FileNotFoundError(f"Config file {config_file_path} not found.")

    # Load the config.json file
    with config_file_path.open("r") as config_file:
        config_json = json.load(config_file)

    history = config_json["history"]  # Contains history of all layers

    # Collect layer information: hash, createdBy, and created timestamp
    layers_info = []
    layer_count = 0  # Track which layer index we are on
    for history_entry in history:
        created_by = history_entry.get("created_by", "<unknown>")
        created_dt = history_entry.get("created", "<unknown>")
        empty_layer = history_entry.get("empty_layer", False)

        if not empty_layer and layer_count < len(manifest[0]["Layers"]):
            # The Layers array in the manifest corresponds to non-empty layers
            layer_hash = manifest[0]["Layers"][layer_count].split("/")[-1]
            layer_count += 1
        else:
            # For empty layers, we assign "<empty>" as a placeholder
            layer_hash = "<empty>"

        layers_info.append(
            {
                "LayerHash": layer_hash,
                "CreatedBy": created_by,
                "Created_dt": created_dt,
            }
        )

    # Convert to a DataFrame and return
    df_layers = pd.DataFrame(layers_info)
    return df_layers


def aggregate_files_by_layer(files_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates files in the DataFrame by LayerHash, summing the file sizes, and
    concatenating the CreatedBy commands for each file.

    Parameters
    ----------
    files_df : pd.DataFrame
        DataFrame containing columns FilePath, FileSize_MB, CreatedBy, Created_dt, LayerHash.

    Returns
    -------
    pd.DataFrame
        Aggregated DataFrame with the following columns:
        - FilePath (common path for the files in the layer)
        - FileSize_MB (sum of file sizes in MB)
        - CreatedBy (list of all 'CreatedBy' commands in the group)
        - Created_dt (common creation date for the layer)
    """

    def aggregate_created_by(created_by_series: pd.Series) -> List[str]:
        """Helper function to aggregate the 'FilePath' column into a list."""
        return list(created_by_series.dropna().unique())

    # Group by LayerHash and FilePath, aggregating the other columns
    aggregated_df = (
        files_df.groupby(["LayerHash"])
        .agg(
            {
                "FileSize_MB": "sum",
                "FilePath": aggregate_created_by,
                "Created_dt": "first",  # Assuming the Created_dt is the same for all entries in a group
            }
        )
        .reset_index()
    )

    return aggregated_df


def compare_layers_files(
    files_df: pd.DataFrame, layer_hash_1: str, layer_hash_2: str
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compare files between two layers and group them into added, removed, and modified.

    Parameters
    ----------
    files_df : pd.DataFrame
        DataFrame containing file information with columns: FilePath, FileSize_MB, LayerHash, CreatedBy, Created_dt.
    layer_hash_1 : str
        The hash of the first layer to compare.
    layer_hash_2 : str
        The hash of the second layer to compare.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Three DataFrames containing added, removed, and modified files respectively.
    """

    # Select files in the first and second layers
    layer_1_files = files_df[files_df["LayerHash"] == layer_hash_1][
        ["FilePath", "FileSize_MB", "CreatedBy", "Created_dt"]
    ]
    layer_2_files = files_df[files_df["LayerHash"] == layer_hash_2][
        ["FilePath", "FileSize_MB", "CreatedBy", "Created_dt"]
    ]

    # Merge the two DataFrames on FilePath to compare them
    merged = pd.merge(
        layer_1_files,
        layer_2_files,
        on="FilePath",
        how="outer",
        suffixes=("_layer_1", "_layer_2"),
        indicator=True,
    )

    # Identify added, removed, and modified files
    added_files = merged[
        merged["_merge"] == "right_only"
    ].copy()  # Present only in layer 2
    removed_files = merged[
        merged["_merge"] == "left_only"
    ].copy()  # Present only in layer 1
    modified_files = merged[
        (merged["_merge"] == "both")
        & (merged["FileSize_MB_layer_1"] != merged["FileSize_MB_layer_2"])
    ].copy()  # Present in both layers but with different sizes

    # Drop the '_merge' column from the results
    added_files.drop(columns=["_merge"], inplace=True)
    removed_files.drop(columns=["_merge"], inplace=True)
    modified_files.drop(columns=["_merge"], inplace=True)

    return added_files, removed_files, modified_files


# TODO: REVIEW
def extract_layer(layer_tar_path: str, output_dir: str) -> str:
    """
    Extracts a Docker image layer tarball to a specified directory.

    Parameters
    ----------
    layer_tar_path : str
        Path to the layer tarball file.
    output_dir : str
        Path to the directory where the tarball should be extracted.

    Returns
    -------
    output_dir : str
        Path to the extracted layer directory.
    """

    try:
        with tarfile.open(layer_tar_path, "r") as tar:
            tar.extractall(path=output_dir)
        return output_dir
    except Exception as e:
        logger.error(f"Error extracting layer: {e}")
        return None


# TODO: REVIEW
def list_files_in_layer(extracted_dir: str) -> list:
    """
    List files in an extracted layer with file sizes.

    Parameters
    ----------
    extracted_dir : str
        Path to the directory where the layer was extracted.

    Returns
    -------
    file_info_list : list
        List of dictionaries with file name, size, and type.
    """
    file_info_list = []

    for root, dirs, files in os.walk(extracted_dir):
        for name in files + dirs:
            file_path = os.path.join(root, name)
            file_info = {
                "name": file_path.replace(extracted_dir, ""),
                "size": (
                    os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                ),
                "type": "dir" if os.path.isdir(file_path) else "file",
            }
            file_info_list.append(file_info)

    return file_info_list


# TODO: REVIEW
def save_to_json(data: list, output_file: str) -> None:
    """
    Save a list of dictionaries to a JSON file.

    Parameters
    ----------
    data : list
        List of dictionaries to save.
    output_file : str
        Path to the output JSON file.
    """
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)


# TODO: REVIEW
def inspect_docker_layer(
    layer_hash: str,
    output_json: str,
    layer_tar_dir=f"/var/lib/docker/overlay2/",
) -> None:
    """
    Inspect a Docker image layer and output the file list as a JSON.

    Parameters
    ----------
    layer_hash : str
        The hash ID of the Docker image layer.
    output_json : str
        Path to save the output JSON file with file information.
    """
    # Use `docker save` to save the image layers
    output_dir = f"layers/{layer_hash}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Replace this with your Docker layer tar path (normally stored in /var/lib/docker)
    # You can also use `docker inspect` to find the layer tarball path
    layer_tar_dir = Path(layer_tar_dir)
    if not layer_tar_dir.is_dir():
        raise ValueError(f"{layer_tar_dir} is not a valid directory for finding layers")
    layer_tar_path = f"/var/lib/docker/overlay2/{layer_hash}/diff.tar"

    # Extract the layer to a directory
    extracted_dir = extract_layer(layer_tar_path, output_dir)

    if extracted_dir:
        # List files in the layer
        file_info_list = list_files_in_layer(extracted_dir)

        # Save the list to a JSON file
        save_to_json(file_info_list, output_json)

        logger.info(f"File list saved to {output_json}")
    else:
        logger.error(f"Could not inspect the layer {layer_hash}")


# OK: TODO:REVIEW
def get_image_layers_info(
    image_name: str,
    remove_missing: bool = False,
    sort_by: str = None,
) -> pd.DataFrame:
    """
    Retrieve the layers of a Docker image and return them as a DataFrame.

    Parameters
    ----------
    image_name : str
        The name or ID of the Docker image to inspect.
    remove_missing : bool
        If True, removes the layers which have `hash` equal to `<missing>`.
    sort_by: str
        The name of the column to sort by.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the layers of the Docker image with the following columns:
        - 'hash': The SHA identifier of the layer.
        - 'createdBy': The command or process that created the layer.
        - 'Size_MB': The size of the layer in megabytes.
        - 'Created_dt': The timestamp when the layer was created.
    """
    # Initialize Docker client
    client = docker.from_env()

    try:
        # Get image object
        image = client.images.get(image_name)

        # Get image history (layers)
        history = image.history()

        # Create a list to store layer information
        layers_data = []

        # Parse the history to extract required information
        for layer in history:
            layer_hash = layer.get("Id", "").split(":")[-1]  # Extract SHA hash
            created_by = layer.get(
                "CreatedBy", "Unknown"
            )  # Command that created the layer
            size_mb = layer.get("Size", 0) / (1024 * 1024)  # Convert size to MB
            created_dt = datetime.fromtimestamp(
                layer.get("Created", 0)
            )  # Creation timestamp

            # Append the layer data to the list
            layers_data.append(
                {
                    "hash": layer_hash,
                    "createdBy": created_by,
                    "Size_MB": round(size_mb, 2),
                    "Created_dt": created_dt,
                }
            )

        # Create a DataFrame from the layers data
        df = pd.DataFrame(
            layers_data, columns=["hash", "createdBy", "Size_MB", "Created_dt"]
        )

        if remove_missing:
            return df[df["hash"] != "<missing>"]

        if sort_by:
            return df.sort_values(sort_by)

        return df

    except docker.errors.ImageNotFound:
        logger.error(f"Image '{image_name}' not found.")
        return pd.DataFrame(columns=["hash", "createdBy", "Size_MB", "Created_dt"])

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return pd.DataFrame(columns=["hash", "createdBy", "Size_MB", "Created_dt"])


# TODO:NOTUSED
def inspect_docker_layers_from_tar2(tarball_path: str) -> pd.DataFrame:
    """
    Inspects the layers of a Docker image tarball and returns a DataFrame
    with information about each layer's files, sizes, and creation commands.

    Parameters
    ----------
    tarball_path : str
        The path to the Docker image tarball.

    Returns
    -------
    pd.DataFrame
        DataFrame containing layer information (hash, createdBy, Size_MB, Created_dt).
    """
    layers_info = []

    # Open the Docker image tarball
    with tarfile.open(tarball_path, "r") as tar:
        # Extract the manifest.json file
        manifest_file = tar.extractfile("manifest.json")
        manifest = json.load(manifest_file)

        # Iterate through each layer
        for layer in manifest[0]["Layers"]:
            layer_id = layer.split("/")[0]

            # Open the layer tarball
            layer_tar_path = os.path.join(layer_id, "layer.tar")
            layer_tar = tar.extractfile(layer_tar_path)
            if not layer_tar:
                continue

            # Create a temporary tarfile object for the layer
            with tarfile.open(fileobj=layer_tar) as layer_tarfile:
                total_size = 0
                file_list = []

                # Iterate through the files in the layer
                for member in layer_tarfile.getmembers():
                    file_size = member.size / (1024**2)  # Convert size to MB
                    total_size += file_size
                    file_list.append((member.name, file_size))

                # Get the creation information from the config
                config_file_path = os.path.join(layer_id, "json")
                config_file = tar.extractfile(config_file_path)
                if config_file:
                    config_json = json.load(config_file)
                    created_by = config_json.get("container_config", {}).get("Cmd", "")
                    created_dt = config_json.get("created", "")
                else:
                    created_by = ""
                    created_dt = ""

                # Append the layer info
                layers_info.append(
                    {
                        "hash": layer_id,
                        "createdBy": created_by,
                        "Size_MB": round(total_size, 2),
                        "Created_dt": created_dt,
                    }
                )

    # Convert to a DataFrame
    return pd.DataFrame(layers_info)


# TODO:REVIEW
def inspect_docker_layers_from_tar(tarball_path: str) -> pd.DataFrame:
    """
    Inspects the layers of a Docker image tarball (in OCI format) and returns a DataFrame
    with information about each layer's files, sizes, and creation commands.

    Parameters
    ----------
    tarball_path : str
        The path to the Docker image tarball.

    Returns
    -------
    pd.DataFrame
        DataFrame containing layer information (hash, createdBy, Size_MB, Created_dt).
    """
    layers_info = []

    # Open the Docker image tarball
    with tarfile.open(tarball_path, "r") as tar:
        # Extract and parse the manifest.json file
        manifest_file = tar.extractfile("manifest.json")
        manifest = json.load(manifest_file)

        # Extract and parse the index.json file
        index_file = tar.extractfile("index.json")
        index = json.load(index_file)

        # Get the layer digests from the index.json
        layer_digests = index["manifests"][0]["digest"]

        # Iterate through each layer from the manifest
        for layer in manifest[0]["Layers"]:
            layer_hash = layer.split("/")[
                1
            ]  # Extract the hash value after 'blobs/sha256/'

            # Open the layer tarball
            layer_tar_path = f"blobs/sha256/{layer_hash}"
            try:
                layer_tar = tar.extractfile(layer_tar_path)
                if not layer_tar:
                    continue
            except KeyError:
                logger.error(
                    f"Layer tarball {layer_tar_path} not found in the archive."
                )
                continue

            # Create a temporary tarfile object for the layer
            total_size = 0
            file_list = []

            with tarfile.open(fileobj=layer_tar) as layer_tarfile:
                # Iterate through the files in the layer
                for member in layer_tarfile.getmembers():
                    file_size = member.size / (1024**2)  # Convert size to MB
                    total_size += file_size
                    file_list.append((member.name, file_size))

            # Extract information from the config file in the same tar archive
            config_file_path = f"blobs/sha256/{manifest[0]['Config'].split(':')[-1]}"
            config_file = tar.extractfile(config_file_path)
            if config_file:
                config_json = json.load(config_file)
                created_by = config_json.get("container_config", {}).get("Cmd", "")
                created_dt = config_json.get("created", "")
            else:
                created_by = ""
                created_dt = ""

            # Append the layer info
            layers_info.append(
                {
                    "hash": layer_hash,
                    "createdBy": created_by,
                    "Size_MB": round(total_size, 2),
                    "Created_dt": created_dt,
                }
            )

    # Convert to a DataFrame
    return pd.DataFrame(layers_info)


def inspect_docker_layers_from_extracted_folder(
    extracted_folder_path: str,
) -> pd.DataFrame:
    """
    Inspects the layers of a Docker image from an extracted folder and returns a DataFrame
    with information about each layer's files, sizes, and creation commands.

    Parameters
    ----------
    extracted_folder_path : str
        The path to the extracted Docker image folder.

    Returns
    -------
    pd.DataFrame
        DataFrame containing layer information (hash, createdBy, Size_MB, Created_dt).
    """
    layers_info = []

    extracted_folder = Path(extracted_folder_path)

    # Path to the manifest.json file in the extracted folder
    manifest_file_path = extracted_folder / "manifest.json"

    if not manifest_file_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {extracted_folder}")

    # Load the manifest.json file
    with manifest_file_path.open("r") as manifest_file:
        manifest = json.load(manifest_file)

    # Load the config file
    config_path = extracted_folder / manifest[0]["Config"]
    with config_path.open("r") as f:
        config = json.load(f)

    # Iterate through each layer in the manifest
    for layer_path in manifest[0]["Layers"]:
        layer_tar_path = extracted_folder / layer_path

        if not layer_tar_path.exists():
            logger.warning(f"Layer tarball {layer_tar_path} not found, skipping.")
            continue

        total_size = 0
        file_list = []

        # Open the layer tarball to inspect the files inside
        with tarfile.open(layer_tar_path, "r") as layer_tarfile:
            for member in layer_tarfile.getmembers():
                file_size = member.size / (1024**2)  # Convert size to MB
                total_size += file_size
                file_list.append((member.name, file_size))

        # Get the creation information from the config file associated with the layer
        layer_hash = layer_path.split("/")[0]  # Extract hash from the layer path
        config_file_path = extracted_folder / f"{layer_hash}.json"
        if not config_file_path.exists():
            logger.warning(f"Config file {config_file_path} not found, skipping.")
            created_by = ""
            created_dt = ""
        else:
            with config_file_path.open("r") as config_file:
                config_json = json.load(config_file)
                created_by = config_json.get("container_config", {}).get("Cmd", "")
                created_dt = config_json.get("created", "")

        # Append the layer info
        layers_info.append(
            {
                "hash": layer_hash,
                "createdBy": created_by,
                "Size_MB": round(total_size, 2),
                "Created_dt": created_dt,
            }
        )

    # Convert to a DataFrame
    return pd.DataFrame(layers_info)


# TODO:REVIEW
def analyze_docker_image(tarball_path: str) -> pd.DataFrame:
    """
    Analyzes a Docker image tarball and returns a DataFrame with layer-by-layer
    file additions and sizes.

    Parameters
    ----------
    tarball_path : str
        Path to the Docker image tarball.

    Returns
    -------
    pd.DataFrame
        DataFrame with layer hash, file name, and file size for each layer.
    """
    layers_info = []

    # Open the Docker image tarball
    with tarfile.open(tarball_path, "r") as tar:
        # Extract the manifest.json file
        manifest_file = tar.extractfile("manifest.json")
        manifest = json.load(manifest_file)

        previous_files = {}  # To track files from previous layers

        # Iterate through each layer
        for layer in manifest[0]["Layers"]:
            layer_id = layer.split("/")[0]

            # Extract files and sizes for the current layer
            layer_tar_path = os.path.join(layer_id, "layer.tar")
            current_files = extract_layer_files(tar, layer_tar_path)

            # Find new or modified files
            for file_name, file_size in current_files.items():
                if (
                    file_name not in previous_files
                    or previous_files[file_name] != file_size
                ):
                    layers_info.append(
                        {
                            "hash": layer_id,
                            "file_name": file_name,
                            "file_size_MB": round(file_size / (1024**2), 2),
                        }
                    )

            # Update the tracked files to the current layer's files
            previous_files.update(current_files)

    # Convert to DataFrame
    return pd.DataFrame(layers_info)
