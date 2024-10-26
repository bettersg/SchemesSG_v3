from os import getenv  # noqa: I001

#aiogram
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from dotenv import load_dotenv


#Bot Config Class
class BotConfig:
    """Config for Telegram Bot"""

    def __init__(self, intro_message:str, similarity_threshold:int) -> None:
        self.intro_message = intro_message
        self.similarity_threshold = similarity_threshold

# Bot token can be obtained via https://t.me/BotFather
load_dotenv()
TOKEN = getenv("API_KEY")

# Initialize Bot instance with default bot properties which will be passed to all API calls
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

