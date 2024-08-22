from src.load_env import load_env
from src.App import load_app
import asyncio
from pyrogram.client import Client

def main():
    try: 
        api_data = load_env()
        app = load_app(api_data)
        app.run()
    except Exception:
        return
    

if __name__ == "__main__":
    main()  # TODO: Run parallelized 
