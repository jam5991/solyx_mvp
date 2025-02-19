import logging


def configure_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,
    )

    # Configure Ray logging
    ray_logger = logging.getLogger("ray")
    ray_logger.setLevel(logging.ERROR)
    ray_logger.propagate = False
