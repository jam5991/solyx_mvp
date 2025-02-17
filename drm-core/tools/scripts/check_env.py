#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv

def check_env():
    # Load .env file from drm-core directory
    env_path = Path(__file__).parent.parent.parent / 'config.env'
    print(f"Looking for .env file at: {env_path}")
    
    load_dotenv(dotenv_path=env_path)
    
    # Check for API keys
    providers = {
        'VAST_API_KEY': os.getenv('VAST_API_KEY'),
        'LAMBDA_API_KEY': os.getenv('LAMBDA_API_KEY'),
        'COREWEAVE_API_KEY': os.getenv('COREWEAVE_API_KEY')
    }
    
    print("\nAPI Key Status:")
    for provider, key in providers.items():
        status = "✅ Found" if key else "❌ Missing"
        print(f"{provider}: {status}")
        if key:
            # Show first few characters of the key
            print(f"  Key preview: {key[:8]}...")

if __name__ == "__main__":
    check_env() 