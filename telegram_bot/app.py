import asyncio
import logging
import sys

from aiogram import Dispatcher, html

from bot import bot, BotConfig
from handlers import main_handlers

def register_routers(dp: Dispatcher) -> None:
    """Registers routers"""

    dp.include_router(main_handlers.main_router)

async def main() -> None:

    # Prepare configurations
    config = BotConfig(
        intro_message=f"Welcome to SchemesSG! I am your companion in searching for public assistance in Singapore. Do describe to me the help you need and I will try to find the most suitable assistance scheme for you. Please be specific but do not give any identifiable information. \n\n {html.italic('(E.g. I am a dialysis patient in need of financial assistance and food support after being retrenched due to COVID 19.)')}",
        similarity_threshold=2
        )

    # All handlers should be attached to the Router (or Dispatcher)
    dp = Dispatcher()
    dp["config"] = config
    register_routers(dp)

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())