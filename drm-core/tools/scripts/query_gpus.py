#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from drm_core.providers.coreweave import CoreWeaveProvider
from drm_core.providers.lambdalabs import LambdaLabsProvider
from drm_core.providers.vastai import VastAIProvider

# Get the project root directory
ROOT_DIR = Path(__file__).parent.parent.parent

# Database setup - use the same test database
DB_PATH = ROOT_DIR / "test_gpu_tracker.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"


async def query_provider(name: str, provider):
    """Query a single provider and print results"""
    print(f"\n=== {name} GPUs ===")
    try:
        gpus = await provider.list_available_gpus()
        if not gpus:
            print("No GPUs found or provider not accessible")
            return

        print(f"Found {len(gpus)} GPUs:")
        for gpu in gpus:
            # Skip cuda_version if not present in the GPUInstance model
            print(f"\n• {gpu.gpu_type}")
            print(f"  - ID: {gpu.instance_id}")
            print(f"  - Memory: {gpu.memory_gb}GB")
            print(f"  - Price: ${gpu.price_per_hour:.2f}/hour")
            print(f"  - Region: {gpu.region}")
            print(f"  - Available: {gpu.available}")
            # Only print cuda_version if it exists as an attribute
            if hasattr(gpu, "cuda_version"):
                print(f"  - CUDA: {gpu.cuda_version}")
    except Exception as e:
        print(f"Error querying {name}: {e}")


async def main():
    # Load environment variables from the correct path
    config_path = Path(__file__).parent.parent.parent / "config.env"
    print(f"Looking for config at: {config_path}")
    load_dotenv(config_path)

    # Initialize providers with API keys
    providers = {}

    if vast_key := os.getenv("VAST_API_KEY"):
        providers["Vast.ai"] = VastAIProvider(vast_key)
        print("Found Vast.ai API key")

    if lambda_key := os.getenv("LAMBDA_API_KEY"):
        providers["Lambda Labs"] = LambdaLabsProvider(lambda_key)
        print("Found Lambda Labs API key")

    if coreweave_key := os.getenv("COREWEAVE_API_KEY"):
        providers["CoreWeave"] = CoreWeaveProvider(coreweave_key)
        print("Found CoreWeave API key")

    if not providers:
        print(
            "\nNo API keys found. Please check if config.env exists at:",
            config_path,
        )
        return

    # Query each provider
    for name, provider in providers.items():
        await query_provider(name, provider)


if __name__ == "__main__":
    asyncio.run(main())
