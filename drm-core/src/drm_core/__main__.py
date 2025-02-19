"""Entry point for running DRM Core as a module"""
import asyncio
import logging

from .core import main

logger = logging.getLogger(__name__)


def run():
    """Run the DRM Core service"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        raise


if __name__ == "__main__":
    run()
