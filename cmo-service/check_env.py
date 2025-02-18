import os


def check_env():
    print("Checking environment variables:")
    print(f"VAST_API_KEY: {'SET' if os.getenv('VAST_API_KEY') else 'NOT SET'}")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')}")
    print(f"PORT: {os.getenv('PORT', 'NOT SET')}")


if __name__ == "__main__":
    check_env()
