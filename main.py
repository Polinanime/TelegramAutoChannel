from src.load_env import load_env
from src.App import load_app
import asyncio
from pyrogram.client import Client

def main():
    api_data = load_env()
    app = load_app(api_data)
    app.run()
    

if __name__ == "__main__":
    main()  # TODO: Run parallelized 