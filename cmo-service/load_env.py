from dotenv import load_dotenv
import os

def load_env():
    # Load environment variables from config.env
    load_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.env')
    load_dotenv(load_env_path)
    
    print("Environment variables loaded:")
    print(f"VAST_API_KEY: {'SET' if os.getenv('VAST_API_KEY') else 'NOT SET'}")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')}")
    print(f"PORT: {os.getenv('PORT', 'NOT SET')}")

if __name__ == "__main__":
    load_env() 