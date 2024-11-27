import json
import tarfile
from pathlib import Path

import pandas as pd
import pytest

from docker_analyzer.inspection import (
    aggregate_files_by_layer,
    extract_image_tar,
    inspect_all_image_layers_and_get_files_from_extracted_tar,
    load_manifest_and_config_from_extracted_tar,
    save_docker_image,
)
from docker_analyzer.logger import get_logger

# Directory for sample images
SAMPLE_IMAGES_DIR = Path("tests/sample_images")
PYTHON_39_JSON = SAMPLE_IMAGES_DIR / "python_3.9.json"
PYTHON_39_SLIM_JSON = SAMPLE_IMAGES_DIR / "python_3.9_slim.json"

logger = get_logger(__name__)


@pytest.fixture
def mock_image_tarball(tmp_path):
    """Creates a sample tarball to simulate saving a Docker image."""
    tarball_path = tmp_path / "sample_image.tar"
    # Create a valid tarball with a sample file
    with tarfile.open(tarball_path, "w") as tar:
        file_path = tmp_path / "example_file.txt"
        file_path.write_text("Sample content")
        tar.add(file_path, arcname="example_file.txt")
    return tarball_path


@pytest.fixture
def extracted_tarball_dir(tmp_path):
    """Simulates a directory extracted from a Docker tarball with valid layers."""
    extracted_dir = tmp_path / "extracted_image"
    extracted_dir.mkdir()
    # Create the manifest.json
    (extracted_dir / "manifest.json").write_text(
        '[{"Config": "config.json", "Layers": ["layer1.tar", "layer2.tar"]}]'
    )
    # Create the config.json
    (extracted_dir / "config.json").write_text(
        '{"container_config": {}, "history": []}'
    )
    # Create valid layer tarballs
    for layer_name in ["layer1.tar", "layer2.tar"]:
        layer_path = extracted_dir / layer_name
        with tarfile.open(layer_path, "w") as tar:
            file_path = tmp_path / f"{layer_name}_file.txt"
            file_path.write_text(f"Content of {layer_name}")
            tar.add(file_path, arcname=f"{layer_name}_file.txt")
    return extracted_dir


def test_save_docker_image(mock_image_tarball):
    """Test for the save_docker_image function."""
    image_name = "python:3.9"
    tarball_path = save_docker_image(image_name, output_file=mock_image_tarball)
    assert Path(tarball_path).is_file()


def test_extract_image_tar(mock_image_tarball, tmp_path):
    """Test for the extract_image_tar function."""
    extracted_dir = tmp_path / "extracted_image"
    extracted_path = extract_image_tar(mock_image_tarball, output_dir=extracted_dir)
    assert extracted_path is not None, "Extraction failed, returned None"
    assert Path(extracted_path).is_dir(), "Extracted path is not a directory"
    # Verify that the extracted file exists
    extracted_file = extracted_dir / "example_file.txt"
    assert extracted_file.is_file(), f"Expected file {extracted_file} not found"


def test_load_manifest_and_config_from_extracted_tar(extracted_tarball_dir):
    """Test for loading manifest.json and config.json."""
    manifest, config = load_manifest_and_config_from_extracted_tar(
        extracted_tarball_dir
    )
    assert manifest is not None
    assert config is not None
    assert "Config" in manifest[0]
    assert "container_config" in config


def inspect_all_image_layers_and_get_files_from_extracted_tar(
    extracted_folder_path: str,
) -> pd.DataFrame:
    layers_info = []
    extracted_folder = Path(extracted_folder_path)

    # Path to the manifest.json file
    manifest_file_path = extracted_folder / "manifest.json"

    if not manifest_file_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {extracted_folder}")

    # Load manifest.json
    with manifest_file_path.open("r") as manifest_file:
        manifest = json.load(manifest_file)

    # Path to the config file
    config_file_path = extracted_folder / manifest[0]["Config"]

    if not config_file_path.exists():
        raise FileNotFoundError(f"Config file {config_file_path} not found.")

    # Load config.json
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
        layer_hash = Path(layer_path).stem  # Extract the hash from the file name
        layer_files_df["LayerHash"] = layer_hash
        layer_files_df["CreatedBy"] = created_by
        layer_files_df["Created_dt"] = created_dt

        layers_info.append(layer_files_df)

    if not layers_info:
        raise ValueError("No layer information found")

    return pd.concat(layers_info, ignore_index=True)


def test_aggregate_files_by_layer(extracted_tarball_dir):
    """Test for aggregating files by layer."""
    # Simulate a DataFrame of files by layer
    files_df = pd.DataFrame(
        {
            "LayerHash": ["layer1", "layer1", "layer2"],
            "FilePath": ["/file1", "/file2", "/file3"],
            "FileSize_MB": [1.2, 2.3, 3.4],
            "CreatedBy": ["RUN apt-get", "RUN touch", "RUN echo"],
            "Created_dt": ["2024-01-01", "2024-01-01", "2024-01-02"],
        }
    )
    aggregated_df = aggregate_files_by_layer(files_df)
    assert isinstance(aggregated_df, pd.DataFrame)
    assert len(aggregated_df) == 2  # Two layers
