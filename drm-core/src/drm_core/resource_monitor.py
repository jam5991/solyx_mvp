import psutil
import logging
from datetime import datetime
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class ResourceMonitor:
    def __init__(self, update_interval: int = 60):
        self.update_interval = update_interval
        self.metrics: Dict[str, Any] = {}
        self.running = False

    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        while self.running:
            try:
                self.metrics = await self._collect_metrics()
                logger.debug(f"Updated metrics: {self.metrics}")
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(self.update_interval)

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False

    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system and GPU metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            },
            "gpus": await self._collect_gpu_metrics()
        }
        return metrics

    async def _collect_gpu_metrics(self) -> Dict[str, Any]:
        """Collect GPU-specific metrics"""
        try:
            import pynvml
            pynvml.nvmlInit()
            gpu_metrics = {}
            
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                gpu_metrics[f"gpu_{i}"] = {
                    "memory_total": info.total,
                    "memory_used": info.used,
                    "memory_free": info.free,
                    "gpu_utilization": utilization.gpu,
                    "memory_utilization": utilization.memory
                }
            
            return gpu_metrics
        except Exception as e:
            logger.error(f"Error collecting GPU metrics: {e}")
            return {}

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get the most recent metrics"""
        return self.metrics 