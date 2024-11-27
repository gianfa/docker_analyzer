# Docker Analyzer CLI

[![Python](https://img.shields.io/badge/python->=3.10,<3.14%2B-blue.svg)](https://www.python.org/)
![publish workflow](https://github.com/gianfa/docks/actions/workflows/publish.yml/badge.svg?branch=main)
[![PyPI version](https://img.shields.io/pypi/v/docks.svg)](https://pypi.org/project/docks/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img src='./docs/imgs/logo-dark.png' width='200px'>

**Finally a lightweight tool to inspect and compare Docker images instantly, focusing on layer analysis.**

## Overview

Docker Analyzer CLI is a Python-based command-line interface designed to analyze and compare Docker images. It provides quick insights into image layers, size optimizations, and differences, making it an essential tool for developers and DevOps engineers.

## Features

- **Layer Analysis**: Inspect Docker image layers to identify redundancies or inefficiencies.
- **Image Comparison**: Compare two images to find shared, duplicated, or non-shared layers.
- **CLI Interface**: A powerful and flexible command-line interface.
- **Web GUI Integration**: Optionally launch a web-based interface for interactive analysis.
- **Custom Configuration**: Configure temporary directories, logging, and output formats.

## Installation

### Via PIP

   ```bash
   pip install docker_analyzer
   ```

### Via Poetry

   ```bash
   poetry add docker_analyzer
   ```

## CLI Usage

### Getting Help

To view all available commands and options:

```bash
docker_analyzer --help
```

### Common Commands

#### Get Temporary Directory

Displays the temporary directory used for file storage:

```bash
docker_analyzer get-temp-dir
```

#### List Docker Images

Lists all Docker images available on the system:

```bash
docker_analyzer list-images
```

#### Launch Web GUI

Starts the web-based graphical interface:

```bash
docker_analyzer web-gui
```

Navigate to `http://localhost:5002` in your browser to use the GUI.

### Comparison Examples

#### Compare Shared Layers

Identify layers that are shared between two images:

```bash
docker_analyzer compare shared-layers python:3.9-slim python:3.9
```

#### Compare Duplicated Layers

Find duplicated layers within an image or across two images:

```bash
docker_analyzer compare duplicated-layers python:3.9-slim python:3.9
```

#### Compare Non-Shared Layers

Identify layers unique to each image:

```bash
docker_analyzer compare non-shared-layers python:3.9-slim python:3.9
```

#### Compare Total Sizes

Compare the total sizes of two images:

```bash
docker_analyzer compare total-sizes python:3.9-slim python:3.9
```

## Development

### Running Tests

Run all tests using pytest:

```bash
poetry run pytest
```

### Code Style

The project adheres to PEP 8. Check code formatting using `black`:

```bash
poetry run black .
```

## Contributing

We welcome contributions! To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request with a detailed description.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
