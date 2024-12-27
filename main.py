import asyncio
from src.load_env import load_env
from src.App import TelegramBot
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        api_data = load_env()
        bot = TelegramBot(api_data)
        await bot.start()
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        await main()

if __name__ == "__main__":
    asyncio.run(main())
