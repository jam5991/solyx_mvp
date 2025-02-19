"""Entry point for running DRM Core as a module"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .core import main

logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Now we can import from data directory
from data.generate_fake_data import generate_fake_training_data


def run():
    """Run the DRM Core service"""
    parser = argparse.ArgumentParser(description="DRM Core Service")
    parser.add_argument(
        "--generate-data",
        action="store_true",
        help="Generate fake training data before starting the service",
    )
    args = parser.parse_args()

    try:
        if args.generate_data:
            logger.info("Generating fake training data...")
            data_dir = generate_fake_training_data()
            logger.info(f"Generated fake dataset at: {data_dir}")

        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        raise


if __name__ == "__main__":
    run()
