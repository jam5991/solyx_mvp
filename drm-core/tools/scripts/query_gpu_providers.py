#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import aiohttp
import logging
from tabulate import tabulate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def query_lambda_labs():
    """Query Lambda Labs API for your instances"""
    if not (api_key := os.getenv("LAMBDA_API_KEY")):
        logger.warning("⚠️  No Lambda Labs API key found")
        return None

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        async with aiohttp.ClientSession() as session:
            # Query instances endpoint for your active instances
            async with session.get(
                "https://cloud.lambdalabs.com/api/v1/instances",
                headers=headers
            ) as response:
                if response.status != 200:
                    logger.error(f"❌ Lambda Labs API error: {response.status}")
                    return None
                data = await response.json()
                
                my_instances = []
                for instance in data.get("data", []):
                    my_instances.append({
                        "provider": "lambda",
                        "instance_id": instance.get("id"),
                        "gpu_name": instance.get("instance_type", {}).get("name", "Unknown"),
                        "status": instance.get("status"),
                        "region": instance.get("region", {}).get("name", "Unknown"),
                        "ip_address": instance.get("ip"),
                        "launched_at": instance.get("launched_at")
                    })
                return my_instances
    except Exception as e:
        logger.error(f"❌ Lambda Labs API error: {str(e)}")
        return None

async def query_vast_ai():
    """Query Vast.ai API for your instances"""
    if not (api_key := os.getenv("VAST_AI_KEY")):
        logger.warning("⚠️  No Vast.ai API key found")
        return None

    try:
        async with aiohttp.ClientSession() as session:
            # Query instances endpoint for your active instances
            async with session.get(
                f"https://console.vast.ai/api/v0/instances/?api_key={api_key}"
            ) as response:
                if response.status != 200:
                    logger.error(f"❌ Vast.ai API error: {response.status}")
                    return None
                data = await response.json()
                
                my_instances = []
                for instance in data.get("instances", []):
                    my_instances.append({
                        "provider": "vast.ai",
                        "instance_id": instance.get("id"),
                        "gpu_name": instance.get("gpu_name"),
                        "status": instance.get("actual_status"),
                        "location": instance.get("geolocation", "Unknown"),
                        "ip_address": instance.get("public_ipaddr"),
                        "launched_at": instance.get("start_date")
                    })
                return my_instances
    except Exception as e:
        logger.error(f"❌ Vast.ai API error: {str(e)}")
        return None

async def main():
    """Query and display your GPU instances from all providers"""
    # Load environment variables
    config_path = Path(__file__).parent.parent.parent / "config.env"
    load_dotenv(dotenv_path=config_path)
    
    my_instances = []
    
    # Query each provider
    logger.info("\n=== Querying Your GPU Instances ===")
    
    # Lambda Labs
    if lambda_instances := await query_lambda_labs():
        my_instances.extend(lambda_instances)
    
    # Vast.ai
    if vast_instances := await query_vast_ai():
        my_instances.extend(vast_instances)
    
    if not my_instances:
        logger.warning("No active instances found!")
        return
    
    # Display results
    print("\n🖥️  Your Active GPU Instances:")
    print(tabulate(
        my_instances,
        headers={
            "provider": "Provider",
            "instance_id": "Instance ID",
            "gpu_name": "GPU Model",
            "status": "Status",
            "region": "Region",
            "ip_address": "IP Address",
            "launched_at": "Launched At"
        },
        tablefmt="pretty"
    ))
    
    # Print summary
    providers = set(inst["provider"] for inst in my_instances)
    total_instances = len(my_instances)
    
    print(f"\n📈 Summary:")
    print(f"Active Providers: {', '.join(providers)}")
    print(f"Total Active Instances: {total_instances}")

if __name__ == "__main__":
    asyncio.run(main()) 