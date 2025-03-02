from enum import Enum

from aiogram import Router, html, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, callback_data
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import BotConfig, bot
from utils.api import retrieve_scheme_results, search_schemes, send_chat_message


main_router = Router()

NUM_SCHEME_PER_PAGE = 5


class Mode(Enum):
    """Enum class for view or chat mode"""

    VIEW = "view"
    CHAT = "chat"


class SearchResultsCallback(callback_data.CallbackData, prefix="respg"):
    """Class for callback data (used to pass page number and query ID through messages and for pagination)"""

    page_num: int
    query_id: str
    mode: Mode = Mode.VIEW


class Form(StatesGroup):
    """Conversational state manager"""

    search = State()
    chat = State()


def present_scheme(idx: int, scheme: dict[str, str | int]) -> str:
    """
    Formats the text message reply for each scheme

    Args:
        idx (int): scheme index
        scheme (dict[str, str | int]): dictionary containing details of a scheme

    Returns
        str: message with details of scheme presented as a string
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


def paginator(page: int, query_id: str, last: bool = False, is_error: bool = False) -> types.InlineKeyboardMarkup:
    """
    Returns Back/Next buttons for pagination

    Args:
        page (int): current page number
        query_id (int): ID of search query
        last (bool): if current page is last
        is_error (bool): if pagination request resulted in error

    Returns:
        types.InlineKeyboardMarkup: Inline Keyboard Markup for telegram bot
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

    if is_error:
        keyboard_builder.button(
            text="Refresh", callback_data=SearchResultsCallback(page_num=page, query_id=query_id)
        )
    else:
        keyboard_builder.button(
            text="Let's Chat!", callback_data=SearchResultsCallback(page_num=page, query_id=query_id, mode=Mode.CHAT).pack()
        )

    keyboard_builder.adjust(num_buttons)
    return keyboard_builder.as_markup()


@main_router.message(Command("start", "help"))
async def command_start_handler(message: types.Message, config: BotConfig, state: FSMContext) -> None:
    """
    This handler receives messages with the `/start` and `/help` commands

    Args:
        message (types.Message): message sent by user
        config (BotConfig): configuration of telegram bot
        state (FSMContext): state manager of telegram bot
    """

    await state.set_state(Form.search)
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}! {config.intro_message}")


@main_router.message(Form.chat, Command("exit"))
async def exit_chat_handler(message: types.Message, config: BotConfig, state: FSMContext) -> None:
    """
    This handler receives messages with the `/exit` commands when in the chat state

    Args:
        message (types.Message): message sent by user
        config (BotConfig): configuration of telegram bot
        state (FSMContext): state manager of telegram bot
    """

    await state.clear()
    await state.set_state(Form.search)
    await message.answer("You have exited Schemes Support Chat. Hope that we were able to help!")


@main_router.message(Form.chat)
async def chat_handler(message: types.Message, config: BotConfig, state: FSMContext) -> None:
    """
    Search Handler will make a query to the FASTAPI backend to search for most relevant scheme.

    Args:
        message (types.Message): message sent by user
        config (BotConfig): configuration of telegram bot
        state (FSMContext): state manager of telegram bot
    """

    if not message.text:
        message.answer("Please phrase your request in text.")


    data = await state.get_data()
    query_id = data["search"]
    # Use query ID to fetch search results and feed into chatbot

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

    Args:
        message (types.Message): message sent by user
        config (BotConfig): configuration of telegram bot
        state (FSMContext): state manager of telegram bot
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

    Args:
        query (types.CallbackQuery): query initiated by user clicking on a button in the inline keyboard
        callback_data (SearchResultsCallback): callback data from message with the inline keyboard that the user clicked from
        state (FSMContext): state manager of telegram bot
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

    schemes = retrieve_scheme_results(query_id)

    if not schemes:
        # Error when retrieving scheme results

        try:
            await bot.edit_message_text(
                "I am unable to retrieve your schemes.",
                message_id=query.message.message_id,
                chat_id=query.message.chat.id,
                reply_markup=paginator(1, query_id, True, True),
            )

            await bot.answer_callback_query(query.id)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        return

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
