from os import getenv

from dotenv import load_dotenv
import requests

from aiogram.filters import Command
from aiogram import Router, types, html

from bot import BotConfig

main_router = Router()

load_dotenv()
backend_url = getenv("BACKEND_URL")

def present_scheme(idx: int, scheme) -> str:
    """
    Formats the text message reply for each scheme
    """

    return (html.bold(f'{str(idx+1)}. {html.link(scheme["Scheme"], scheme["Link"])}') + "\n" + 
            html.italic(scheme["Agency"]) + "\n\n" + 
            scheme["Description"] + "\n\n" + 
            html.italic(f'Similarity score: {round(scheme["Similarity"],4 )}'))
    

@main_router.message(Command('start','help'))
async def command_start_handler(message: types.Message, config: BotConfig) -> None:
    """
    This handler receives messages with the `/start` and `/help` commands
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}! {config.intro_message}")


@main_router.message()
async def search_handler(message: types.Message, config: BotConfig) -> None:
    """
    Search Handler will make a query to the FASTAPI backend to search for most relevant scheme.

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """

    if not message.text: message.answer('Please describe the help you need.')

    params = {
        'query': message.text,
        'similarity_threshold': config.similarity_threshold
    }

    endpoint = backend_url + '/schemespredict'

    res = requests.get(endpoint, params)

    if res.status_code != 200:
        await message.answer("I am unable to search for suitable assistance schemes. Please try again!")

    schemes = res.json()['data']

    if len(schemes) == 0: #No suitable schemes found
        await message.answer("Sorry, I am unable to find a suitable assistance scheme to address your needs. ")

    reply_arr = [present_scheme(idx, scheme) for idx, scheme in enumerate(schemes)]

    reply_message = "Here are some schemes I found that might address your concerns.\n\n" + "\n\n\n".join(reply_arr)  

    await message.answer(reply_message)
    # try:
    #     # Send a copy of the received message
    #     await message.send_copy(chat_id=message.chat.id)
    # except TypeError:
    #     # But not all the types is supported to be copied so need to handle it
    #     await message.answer("Nice try!")
