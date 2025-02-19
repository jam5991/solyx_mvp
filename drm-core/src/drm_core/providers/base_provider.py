import json
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

import aiohttp

from ..models import GPUInstance

logger = logging.getLogger(__name__)


class BaseCloudProvider(ABC):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger(self.__class__.__name__)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.logger.info(f"Initializing provider with base URL: {base_url}")

    async def _make_request(
        self, endpoint: str, method: str = "GET"
    ) -> Optional[dict]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint.lstrip('/')}"
                self.logger.info(
                    f"\n=== Making {method} request to: {url} ==="
                )

                async with session.request(
                    method, url, headers=self.headers
                ) as response:
                    response_text = await response.text()
                    self.logger.info(f"Response status: {response.status}")

                    if response.status == 200:
                        try:
                            data = await response.json()
                            # Pretty print the first part of the response
                            formatted_data = json.dumps(data, indent=2)
                            preview = "\n".join(
                                formatted_data.split("\n")[:20]
                            )  # First 20 lines
                            self.logger.info(
                                f"\n=== Response Preview ===\n{preview}\n..."
                            )
                            return data
                        except Exception as e:
                            self.logger.error(
                                f"Failed to parse JSON response: {e}"
                            )
                            self.logger.error(
                                f"Raw response: {response_text[:200]}..."
                            )
                            return None
                    else:
                        self.logger.error(
                            f"Request failed with status {response.status}"
                        )
                        self.logger.error(f"Error response: {response_text}")
                        return None

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error during request: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(
                f"Unexpected error during request: {str(e)}", exc_info=True
            )
            return None

    @abstractmethod
    async def list_available_gpus(self) -> List[GPUInstance]:
        """List available GPUs from the provider"""

    def _parse_gpu_instance(self, data: dict) -> GPUInstance:
        raise NotImplementedError

    def _log_gpu_details(self, gpu: GPUInstance):
        """Log details of a GPU instance"""
        self.logger.info(
            f"\nGPU Details:\n"
            f"    Provider: {gpu.provider}\n"
            f"    ID: {gpu.id}\n"
            f"    Type: {gpu.gpu_type}\n"
            f"    Memory: {gpu.memory_gb}GB\n"
            f"    Price: ${gpu.price_per_hour}/hour\n"
            f"    Region: {gpu.region}\n"
            f"    Status: {gpu.status}\n"
            f"    Available: {gpu.available}"
        )
