# docker_interaction.py
from typing import List

import docker


def get_docker_images() -> List[str]:
    """
    Fetches the list of Docker image names available on the system.

    Returns
    -------
    List[str]
        A list of Docker image names.
    """
    client = docker.from_env()
    images = client.images.list()
    image_names = [tag for image in images for tag in image.tags]

    if not image_names:
        raise ValueError("No Docker images found.")

    return image_names
