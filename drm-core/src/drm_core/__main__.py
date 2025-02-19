"""Entry point for running DRM Core as a module"""
import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from .config import DRMConfig
from .core import DRMCore, main

logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Now we can import from data directory
from data.generate_fake_data import generate_fake_training_data


def run():
    """Run the DRM Core service"""
    # Configure logging first
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="DRM Core Service")
    parser.add_argument(
        "--generate-data",
        action="store_true",
        help="Generate fake training data before starting the service",
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Run training on the generated data",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Training batch size",
    )
    args = parser.parse_args()

    try:
        data_dir = None
        # Handle data generation before DRM initialization
        if args.generate_data:
            logger.info("\n=== Generating Fake Training Data ===")
            data_dir = generate_fake_training_data()
            logger.info(f"Generated fake dataset at: {data_dir}")
            logger.info("=== Data Generation Complete ===\n")

        # Initialize DRM Core first
        logger.info("=== Initializing DRM Core ===")
        config = DRMConfig()
        drm = DRMCore(config)

        # Initialize core services
        asyncio.run(drm.initialize())

        # Run training if requested
        if args.train:
            if data_dir is None:
                data_dir = (
                    Path(__file__).parent.parent.parent.parent
                    / "data"
                    / "fake_dataset"
                )

            if not data_dir.exists():
                logger.error(
                    f"Training data not found at {data_dir}. Please generate data first using --generate-data"
                )
                return

            logger.info("\n=== Submitting Training Job ===")
            job_spec = {
                "job_id": "training_job_"
                + datetime.now().strftime("%Y%m%d_%H%M%S"),
                "gpu_type": None,  # Accept any GPU type
                "min_memory": 8,  # Minimum 8GB VRAM
                "max_price": 2.0,  # Maximum $2/hour
                "workload": {
                    "script": "drm_core.workloads.train_classifier",
                    "function": "train_model",
                    "data_dir": str(data_dir),
                    "epochs": args.epochs,
                    "batch_size": args.batch_size,
                },
            }

            result = asyncio.run(drm.submit_job(job_spec))
            if result["status"] == "failed":
                logger.error(f"Job submission failed: {result.get('reason')}")
                return

            logger.info(f"=== Training Job Submitted: {result} ===")
            if result["status"] == "completed":
                return  # Exit successfully

            # Poll status in a non-async way
            while True:
                status = drm.get_job_status(job_spec["job_id"])
                if status and status["status"] == "completed":
                    logger.info(f"Job completed: {status}")
                    break
                time.sleep(5)  # Use regular sleep instead of asyncio.sleep

        if not args.train:
            # Only start the service if we're not training
            logger.info("=== Starting DRM Core Service ===")
            asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Error running DRM Core: {e}")
        raise


if __name__ == "__main__":
    run()
