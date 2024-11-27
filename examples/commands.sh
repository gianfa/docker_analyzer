#!/bin/bash
# This script provides example CLI commands for using docker_analyzer.
# 
# Preparation is required for development purposes only. 
# If docker_analyzer is already available as a CLI command, skip the preparation section.
# 

# -- Parameters --
IMAGE_1="python:3.9-slim"
IMAGE_2="python:3.9-slim-bookworm"

# Uncomment the following lines to pull the images if they are not already present.
# docker pull $IMAGE_1
# docker pull $IMAGE_2

# -- PREPARATION (for development purposes only) --
this_file_dir="$(dirname "$(realpath "$0")")"
docker_analyzer_dir="$(realpath $this_file_dir/..)"
echo "Docker Analyzer Directory: $docker_analyzer_dir"

alias docker_analyzer="python $docker_analyzer_dir/docker_analyzer/cli.py"

# -- Example CLI Commands --

# Get the temporary directory used for inspection
docker_analyzer get-temp-dir

# Display help for the CLI
docker_analyzer

# Display help for the 'compare' command
docker_analyzer compare

# Launch the web GUI
docker_analyzer web-gui

# Display the version of docker_analyzer
docker_analyzer version --only-version

# List all Docker images on the system
docker_analyzer list-images

# Compare shared layers between two images
docker_analyzer compare shared-layers $IMAGE_1 $IMAGE_2

# Compare duplicated layers between two images and output the result as JSON
docker_analyzer compare duplicated-layers $IMAGE_1 $IMAGE_2 --to-json

# Compare the number of layers between two images
docker_analyzer compare number-of-layers $IMAGE_1 $IMAGE_2

# Compare the total sizes of two images
docker_analyzer compare total-sizes $IMAGE_1 $IMAGE_2

# Compare non-shared layers between two images
docker_analyzer compare non-shared-layers $IMAGE_1 $IMAGE_2
