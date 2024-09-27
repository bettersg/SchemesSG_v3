from enum import Enum

from aiogram import Router, html, types
from aiogram.filters import Command, callback_data
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import BotConfig, bot
from utils.api import search_schemes, send_chat_message
from utils.data import read_query_records, update_query_records


main_router = Router()

NUM_SCHEME_PER_PAGE = 5


class Mode(Enum):
    VIEW = "view"
    CHAT = "chat"


class SearchResultsCallback(callback_data.CallbackData, prefix="respg"):
    page_num: int
    query_id: str
    mode: Mode = Mode.VIEW


class Form(StatesGroup):
    search = State()
    chat = State()


def present_scheme(idx: int, scheme) -> str:
    """
    Formats the text message reply for each scheme
    """

    return (
        html.bold(f'{str(idx+1)}. {html.link(scheme["Scheme"], scheme["Link"])}')
        + "\n"
        + html.italic(scheme["Agency"])
        + "\n\n"
        + scheme["Description"]
        + "\n\n"
        + html.italic(f'Similarity score: {round(scheme["Similarity"],4 )}')
    )


def paginator(page: int, query_id: str, last: bool = False) -> types.InlineKeyboardMarkup:
    """
    Returns Back/Next buttons for pagination
    """

    num_buttons = 1 if last or page == 1 else 2

    keyboard_builder = InlineKeyboardBuilder()
    if page != 1:
        keyboard_builder.button(
            text="Back", callback_data=SearchResultsCallback(page_num=page - 1, query_id=query_id).pack()
        )
    if not last:
        keyboard_builder.button(
            text="Next", callback_data=SearchResultsCallback(page_num=page + 1, query_id=query_id).pack()
        )

    keyboard_builder.button(
        text="Let's Chat!", callback_data=SearchResultsCallback(page_num=page, query_id=query_id, mode=Mode.CHAT).pack()
    )

    keyboard_builder.adjust(num_buttons)
    return keyboard_builder.as_markup()


@main_router.message(Command("start", "help"))
async def command_start_handler(message: types.Message, config: BotConfig, state: FSMContext) -> None:
    """
    This handler receives messages with the `/start` and `/help` commands
    """
    await state.set_state(Form.search)
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}! {config.intro_message}")


@main_router.message(Form.chat, Command("exit"))
async def exit_chat_handler(message: types.Message, config: BotConfig, state: FSMContext) -> None:
    """
    This handler receives messages with the `/exit` commands when in the chat state
    """
    await state.clear()
    await state.set_state(Form.search)
    await message.answer("You have exited Schemes Support Chat. Hope that we were able to help!")


@main_router.message(Form.chat)
async def chat_handler(message: types.Message, config: BotConfig, state: FSMContext) -> None:
    """
    Search Handler will make a query to the FASTAPI backend to search for most relevant scheme.
    """

    if not message.text:
        message.answer("Please phrase your request in text.")


    data = await state.get_data()
    query_id = data["search"]
    #print(query_id)  # Use query ID to fetch search results and feed into chatbot

    chat_response, err_message = send_chat_message(message.text, query_id)
    if err_message:
            await message.answer(err_message)
            return

    await message.answer(chat_response, parse_mode="Markdown")


@main_router.message()
async def search_handler(message: types.Message, config: BotConfig, state: FSMContext) -> None:
    """
    Search Handler will make a query to the FASTAPI backend to search for most relevant scheme.

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """

    curr_state = await state.get_state()
    if curr_state is None:
        await state.set_state(Form.search)

    if not message.text:
        message.answer("Please describe the help you need.")
        return

    query_id, schemes, err_message = search_schemes(message.text, config.similarity_threshold)
    if err_message:
        await message.answer(err_message)
        return

    update_query_records(query_id, schemes)

    num_schemes_to_show = min(len(schemes), NUM_SCHEME_PER_PAGE)
    reply_arr = [present_scheme(idx, scheme) for idx, scheme in enumerate(schemes[:num_schemes_to_show])]
    reply_message = "Here are some schemes I found that might address your concerns.\n\n" + "\n\n\n".join(reply_arr)

    if len(schemes) <= NUM_SCHEME_PER_PAGE:
        await message.answer(reply_message)
    else:
        await message.answer(reply_message, reply_markup=paginator(1, query_id))


@main_router.callback_query(SearchResultsCallback.filter())
async def search_callback_handler(
    query: types.CallbackQuery, callback_data: SearchResultsCallback, state: FSMContext
) -> None:
    """
    Callback Query Handler edits the initial text message based on Back/Next buttons.
    """
    pgnum = callback_data.page_num
    query_id = callback_data.query_id
    mode = callback_data.mode

    if mode == Mode.CHAT:  # If "Let's Chat!" button is pressed
        chat_init_msg = "Welcome to Schemes Support Chat! What would you like to know about the schemes listed here?\n\nUse the command /exit to exit Schemes Support Chat"
        await state.update_data(search=query_id)
        await state.set_state(Form.chat)
        await bot.send_message(
            chat_id=query.message.chat.id, text=chat_init_msg, reply_to_message_id=query.message.message_id
        )
        await bot.answer_callback_query(query.id)
        return

    schemes = read_query_records(query_id)

    is_last_page = pgnum * NUM_SCHEME_PER_PAGE >= len(schemes)

    reply_arr = [
        present_scheme(idx + (pgnum - 1) * NUM_SCHEME_PER_PAGE, scheme)
        for idx, scheme in enumerate(
            schemes[
                ((pgnum - 1) * NUM_SCHEME_PER_PAGE) : (len(schemes) if is_last_page else pgnum * NUM_SCHEME_PER_PAGE)
            ]
        )
    ]
    greet_message = "Here are some schemes I found that might address your concerns.\n\n" if pgnum == 1 else ""
    reply_message = greet_message + "\n\n\n".join(reply_arr)

    await bot.edit_message_text(
        reply_message,
        message_id=query.message.message_id,
        chat_id=query.message.chat.id,
        reply_markup=paginator(pgnum, query_id, last=is_last_page),
    )

    await bot.answer_callback_query(query.id)
