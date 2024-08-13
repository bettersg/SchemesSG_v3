import os
import json
import uuid

from dotenv import load_dotenv
import requests

from aiogram.filters import Command, callback_data
from aiogram import Router, types, html
from aiogram.utils.keyboard import InlineKeyboardBuilder 

from bot import BotConfig, bot

main_router = Router()

load_dotenv()
backend_url = os.getenv("BACKEND_URL")

NUM_SCHEME_PER_PAGE = 5
QUERY_RECORDS_FP = 'data/query_records.json'

class SearchResultsCallback(callback_data.CallbackData, prefix="respg"):
    page_num: int
    query_id: str

def present_scheme(idx: int, scheme) -> str:
    """
    Formats the text message reply for each scheme
    """

    return (html.bold(f'{str(idx+1)}. {html.link(scheme["Scheme"], scheme["Link"])}') + "\n" + 
            html.italic(scheme["Agency"]) + "\n\n" + 
            scheme["Description"] + "\n\n" + 
            html.italic(f'Similarity score: {round(scheme["Similarity"],4 )}'))

def paginator(page: int, query_id: str, last:bool = False) -> types.InlineKeyboardMarkup:
    """
    Returns Back/Next buttons for pagination
    """

    num_buttons = 1 if last or page == 1 else 2 

    keyboard_builder = InlineKeyboardBuilder()
    if page!=1: 
        keyboard_builder.button(text='Back', callback_data=SearchResultsCallback(page_num=page-1, query_id=query_id).pack())
    if not last: 
        keyboard_builder.button(text='Next', callback_data=SearchResultsCallback(page_num=page+1, query_id=query_id).pack())
    
    keyboard_builder.adjust(num_buttons)
    return keyboard_builder.as_markup()

def update_query_records(query_id: str, schemes) -> None:
    """
    Updates Json file with query records
    """

    # Creates the file if it doesn't exist
    if not os.path.exists(QUERY_RECORDS_FP):
        os.makedirs('data', exist_ok=True)
        with open(QUERY_RECORDS_FP, 'w') as file:
            json.dump({}, file, indent=4) 

    # Load existing data, append new data, and write back to the file
    with open(QUERY_RECORDS_FP, 'r+') as file:
        data = json.load(file)
        data[query_id] = schemes
        file.seek(0)
        json.dump(data, file, indent=4)

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

    if res.status_code != 200: #Error
        await message.answer("I am unable to search for suitable assistance schemes. Please try again!")

    schemes = res.json()['data']

    if len(schemes) == 0: #No suitable schemes found
        await message.answer("Sorry, I am unable to find a suitable assistance scheme to address your needs. ")

    query_id = str(uuid.uuid4())
    update_query_records(query_id, schemes)

    num_schemes_to_show = min(len(schemes), NUM_SCHEME_PER_PAGE)
    reply_arr = [present_scheme(idx, scheme) for idx, scheme in enumerate(schemes[:num_schemes_to_show])]
    reply_message = "Here are some schemes I found that might address your concerns.\n\n" + "\n\n\n".join(reply_arr)  

    if len(schemes) <= NUM_SCHEME_PER_PAGE: await message.answer(reply_message)
    else: await message.answer(reply_message, reply_markup=paginator(1,query_id))

@main_router.callback_query(SearchResultsCallback.filter())
async def search_callback_handler(query: types.CallbackQuery, callback_data:SearchResultsCallback):
    """
    Callback Query Handler edits the initial text message based on Back/Next buttons.
    """
    pgnum = callback_data.page_num
    query_id = callback_data.query_id

    with open(QUERY_RECORDS_FP, 'r') as rec_files:
        schemes = json.load(rec_files)[query_id]

    is_last_page = (pgnum * NUM_SCHEME_PER_PAGE >= len(schemes))

    reply_arr = [present_scheme(idx + (pgnum-1)*NUM_SCHEME_PER_PAGE, scheme) for idx, scheme in enumerate(schemes[((pgnum-1)*NUM_SCHEME_PER_PAGE):(len(schemes) if is_last_page else pgnum*NUM_SCHEME_PER_PAGE)])]
    greet_message = "Here are some schemes I found that might address your concerns.\n\n" if pgnum == 1 else ""
    reply_message = greet_message + "\n\n\n".join(reply_arr)  

    await bot.edit_message_text(
        reply_message, 
        message_id=query.message.message_id,
        chat_id=query.message.chat.id,
        reply_markup=paginator(pgnum,query_id,last=is_last_page)
        )

    await bot.answer_callback_query(query.id)
    
