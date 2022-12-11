import asyncio
from typing import List, Dict, Union, Optional
from datetime import datetime
from telegram import ReplyKeyboardMarkup, constants, Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, User
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import GOOGLE_DOCS_CREDENTIALS_FILE_NAME, SPREADSHEET_ID, TELEGRAM_BOT_TOKEN, BOT_ADMINS, \
    ANALYTICS_SHEET_NAME

from google_sheets import GoogleSheets
from util import QuestionKey, hash_string, get_user_familiar


class FaqTelegramBot(object):
    def __init__(self, telegram_bot_token: str, spreadsheet_id: str, google_credentials_file_name: str,
                 bot_admins: Optional[str] = None):

        self.sections: Dict[str, Dict[str, Union[Dict[QuestionKey, List[str]], InlineKeyboardMarkup]]] = {}
        self.section_lookup: Dict[QuestionKey, str] = {}

        self.admins: List[str] = bot_admins.replace(" ", "").split(",")

        self.application = Application.builder().token(telegram_bot_token).build()
        self.sheets = GoogleSheets(spreadsheet_id, google_credentials_file_name)

    def init(self):
        result = {}
        result_lookup = {}
        for sheet_name in self.sheets.get_sheet_names():
            if sheet_name[0] == "_":  # SKIP service sheets(ex. '_Analytics')
                continue

            rows = self.sheets.get_sheet_rows(sheet_name)

            content = {hash_string(v[0]): v for v in rows}  # convert [0, 1] to {hash(0): [0, 1}
            buttons = InlineKeyboardMarkup([[InlineKeyboardButton(v[0], callback_data=k)] for k, v in content.items()])

            result[sheet_name] = dict(content=content, buttons=buttons)

            result_lookup = {**result_lookup, **{k: sheet_name for k in content.keys()}}

        self.sections = result
        self.section_lookup = result_lookup

        return self

    def start(self):
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("update", self._reload_command))

        self.application.add_handler(MessageHandler(filters.TEXT, self._show_section_items))
        self.application.add_handler(CallbackQueryHandler(self._section_item_click_callback))
        # self.application.add_error_handler()
        self.application.run_polling()

    def _is_user_admin(self, message: Message) -> bool:
        return message.from_user.username in self.admins

    def _get_reply_markup(self):
        reply_keyboard = [[v] for v in self.sections.keys()]

        return ReplyKeyboardMarkup(
                reply_keyboard, input_field_placeholder=" 👉 Выберите что вас интересует...",
                resize_keyboard=True
            )

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        from_user = update.message.from_user

        name = get_user_familiar(from_user)
        # f"⭐ Welcome <b>{name}!</b> here you can get actual information! ⭐",

        await update.message.reply_text(
            f"⭐ ️Бот 'Гоа Инфо' приветствует тебя <b>{name}!</b> ⭐",
            parse_mode=constants.ParseMode.HTML,
            reply_markup=self._get_reply_markup(),
        )

        await self._do_analytics(from_user, "/START")

    async def _reload_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        if self._is_user_admin(update.message):
            self.init()
            await update.message.reply_text("🛠 Bot was updated!", reply_markup=self._get_reply_markup())
        else:
            await update.message.reply_text("⛔️ Not allowed!", reply_markup=self._get_reply_markup())

    async def _show_section_items(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        section_data = self.sections.get(text, False)
        if section_data:
            await update.message.reply_text(text, reply_markup=section_data['buttons'])

        # await update.message.delete()

        await self._do_analytics(update.message.from_user, text)

    async def _section_item_click_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        question_key = QuestionKey(query.data)

        section_name = self.section_lookup.get(question_key, False)

        if not section_name:
            return await update.message.reply_text("Answer not found ... 😟")

        section_data = self.sections[section_name]
        question, answer = section_data['content'][question_key]

        # section_name = self.get_section_name_by_question(question_key)
        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()

        await query.edit_message_text(text=f"<b>{question}</b>\r\n\r\n{answer}", parse_mode=constants.ParseMode.HTML,
                                      reply_markup=section_data['buttons'])

        await self._do_analytics(query.from_user, section_name, question)

    async def _do_analytics(self, from_user: User, section: str, question: Optional[str] = None):
        """
        Simple analytics. Make record to g-sheet about user interaction
        :param from_user:
        :param section:
        :param question:
        """
        record = [str(datetime.now()), from_user.username, get_user_familiar(from_user), section, question]
        self.sheets.add_sheet_rows(ANALYTICS_SHEET_NAME, [record])

        await asyncio.sleep(0)


if __name__ == "__main__":
    FaqTelegramBot(telegram_bot_token=TELEGRAM_BOT_TOKEN,
                   spreadsheet_id=SPREADSHEET_ID,
                   google_credentials_file_name=GOOGLE_DOCS_CREDENTIALS_FILE_NAME,
                   bot_admins=BOT_ADMINS).init().start()
