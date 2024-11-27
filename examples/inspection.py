# %%
from docker_analyzer.inspection import (
    aggregate_files_by_layer,
    extract_image_tar,
    get_image_history,
    get_image_layers_info,
    inspect_all_image_layers_and_get_files_from_extracted_tar,
    load_manifest_and_config_from_extracted_tar,
    save_docker_image,
)

# %%

IMAGE = "python:3.9-slim"

# %%

df = get_image_history(IMAGE)

# %%

image_name = IMAGE
df = get_image_layers_info(image_name, remove_missing=True)
df

# %%

image_name = IMAGE

# Save the image as a tarball
output_tar = save_docker_image(image_name)
output_tar

# %% Extract and inspect the layers from a tarball

output_extracted_dir = extract_image_tar(output_tar, overwrite=True)
output_extracted_dir

# %%

manifest_json, config_json = load_manifest_and_config_from_extracted_tar(
    output_extracted_dir
)
manifest_json

# %% Extract all the files added to layers

files_df = inspect_all_image_layers_and_get_files_from_extracted_tar(
    output_extracted_dir
)
files_df

# %% Get all the files added per layer

files_by_layer = aggregate_files_by_layer(files_df)
files_by_layer
