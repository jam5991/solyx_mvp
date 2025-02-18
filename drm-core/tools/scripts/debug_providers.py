#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from drm_core.providers.lambdalabs import LambdaLabsProvider
from drm_core.providers.vastai import VastAIProvider


async def debug_vast():
    print("\n=== Debugging Vast.ai Provider ===")
    vast_key = os.getenv("VAST_API_KEY")
    if not vast_key:
        print("❌ No VAST_API_KEY found")
        return

    provider = VastAIProvider(vast_key)
    try:
        print("📡 Querying Vast.ai...")
        gpus = await provider.list_available_gpus()
        print(f"Found {len(gpus)} GPUs:")
        for gpu in gpus:
            print(f"\nGPU Details:")
            print(f"- Type: {gpu.gpu_type}")
            print(f"- Memory: {gpu.memory_gb}GB")
            print(f"- Price: ${gpu.price_per_hour}/hour")
            print(f"- Region: {gpu.region}")
            print(f"- Available: {gpu.available}")
            print(f"- ID: {gpu.instance_id}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def debug_lambda():
    print("\n=== Debugging Lambda Labs Provider ===")
    lambda_key = os.getenv("LAMBDA_API_KEY")
    if not lambda_key:
        print("❌ No LAMBDA_API_KEY found")
        return

    provider = LambdaLabsProvider(lambda_key)
    try:
        print("📡 Querying Lambda Labs...")
        gpus = await provider.list_available_gpus()
        print(f"Found {len(gpus)} GPUs:")
        for gpu in gpus:
            print(f"\nGPU Details:")
            print(f"- Type: {gpu.gpu_type}")
            print(f"- Memory: {gpu.memory_gb}GB")
            print(f"- Price: ${gpu.price_per_hour}/hour")
            print(f"- Region: {gpu.region}")
            print(f"- Available: {gpu.available}")
            print(f"- ID: {gpu.instance_id}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def main():
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / "config.env"
    load_dotenv(dotenv_path=env_path)

    await debug_vast()
    await debug_lambda()


if __name__ == "__main__":
    asyncio.run(main())
