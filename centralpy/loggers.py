"""Module for logging in centralpy."""
import logging


def setup_logging(log_file: str, verbose: bool) -> None:
    """Set up logging for centralpy."""
    centralpy_logger = logging.getLogger("centralpy")
    centralpy_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    if verbose:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.NOTSET)
        stream_handler.setFormatter(formatter)
        centralpy_logger.addHandler(stream_handler)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.NOTSET)
        file_handler.setFormatter(formatter)
        centralpy_logger.addHandler(file_handler)
