from src.load_env import load_env
from src import App
import asyncio

async def main():
    api_data = load_env()
    app = App.channel_builder(api_data)
    app.run()
    

if __name__ == "__main__":
    asyncio.run(main())