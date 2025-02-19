import logging
import os
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Get the project root directory (one level up from drm-core)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

# Load environment variables from config.env
config_path = PROJECT_ROOT / "drm-core" / "config.env"
if config_path.exists():
    load_dotenv(config_path)
    logger.info(f"Loaded configuration from {config_path}")


class DRMConfig(BaseSettings):
    # Class variables (not settings)
    default_db_path: ClassVar[Path] = PROJECT_ROOT / "data" / "gpu_tracker.db"

    # Settings with type annotations
    db_url: str = f"sqlite:///{default_db_path}"
    lambda_api_key: str = os.getenv("LAMBDA_API_KEY", "")
    vast_api_key: str = os.getenv("VAST_API_KEY", "")

    # Ray settings
    ray_dashboard: bool = False
    ray_logging_level: str = "ERROR"

    # GPU requirements
    default_max_price: float = 3.0
    min_memory_gb: int = 8

    class Config:
        env_file = str(config_path)
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls, init_settings, env_settings, file_secret_settings
        ):
            # Debug: Print current working directory
            logger.info(f"Current working directory: {Path.cwd()}")

            # Debug: Print environment variables
            logger.info("Environment variables:")
            logger.info(
                f"VAST_API_KEY present: {bool(os.getenv('VAST_API_KEY'))}"
            )
            logger.info(
                f"LAMBDA_API_KEY present: {bool(os.getenv('LAMBDA_API_KEY'))}"
            )

            # Debug: Print all possible config file locations
            logger.info("\nChecking config files:")
            for env_file in cls.possible_env_files:
                exists = env_file.exists()
                logger.info(
                    f"Checking config file: {env_file} {'[EXISTS]' if exists else '[NOT FOUND]'}"
                )
                if exists:
                    logger.info(f"Found config file at: {env_file}")
                    try:
                        with open(env_file) as f:
                            logger.info(
                                f"Config file contents (first line): {f.readline().strip()}"
                            )
                        cls.env_file = env_file
                        break
                    except Exception as e:
                        logger.error(f"Error reading config file: {e}")
            else:
                logger.error("\nNo config.env found in any location!")
                logger.error("Please ensure config.env exists in one of:")
                for path in cls.possible_env_files:
                    logger.error(f"  - {path}")
                logger.error("\nOr set environment variables directly:")
                logger.error("  export VAST_API_KEY=your_key")
                logger.error("  export LAMBDA_API_KEY=your_key")

            return init_settings, env_settings, file_secret_settings

    def get_db_path(self) -> Path:
        """Get the database file path from the URL"""
        path_str = self.db_url.replace("sqlite:///", "")
        db_path = Path(path_str).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using database at: {db_path}")
        return db_path
