import asyncio
import logging
from datetime import datetime, timedelta

import ray

logger = logging.getLogger(__name__)


class RayService:
    """Singleton service for managing Ray initialization"""

    _instance = None
    IDLE_TIMEOUT = 300  # 5 minutes timeout

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RayService, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance._last_activity = None
        return cls._instance

    def __init__(self):
        self.initialized = False
        self._shutdown_task = None

    async def initialize(self):
        """Initialize Ray cluster"""
        try:
            if not self.initialized:
                logger.info("Starting Ray cluster...")
                ray.init(
                    ignore_reinit_error=True,
                    logging_level=logging.ERROR,
                    include_dashboard=False,
                )
                self.initialized = True
                self._last_activity = datetime.now()
                logger.info("Ray cluster initialized successfully")

                # Start the idle timeout monitor
                self._shutdown_task = asyncio.create_task(
                    self._monitor_idle_timeout()
                )
        except Exception as e:
            logger.error(f"Failed to initialize Ray cluster: {e}")
            raise

    async def _monitor_idle_timeout(self):
        """Monitor for idle timeout and shutdown if exceeded"""
        while self.initialized:
            await asyncio.sleep(60)  # Check every minute
            if self._last_activity:
                idle_time = datetime.now() - self._last_activity
                if idle_time > timedelta(seconds=self.IDLE_TIMEOUT):
                    logger.info(
                        f"Ray cluster idle for {idle_time.seconds}s, shutting down"
                    )
                    await self.shutdown()
                    break

    def record_activity(self):
        """Record activity to prevent timeout"""
        self._last_activity = datetime.now()

    async def shutdown(self):
        """Shutdown Ray if initialized"""
        if self.initialized and ray.is_initialized():
            logger.info("Shutting down Ray...")
            if self._shutdown_task:
                self._shutdown_task.cancel()
            ray.shutdown()
            self.initialized = False
            self._last_activity = None
            logger.info("Ray cluster shutdown complete")
