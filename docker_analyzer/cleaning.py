from docker_analyzer.logger import get_logger

logger = get_logger(__name__)


def cleanup_temp_files(temp_dir: str) -> bool:
    """
    Remove any leftover temporary files from the previous run.
    """
    for file_path in temp_dir.glob("*.json"):
        try:
            file_path.unlink()
            logger.info(f"Removed leftover temp file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error removing temp file {file_path}: {e}")
