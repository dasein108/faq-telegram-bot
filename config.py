import os
import logging
from dotenv import load_dotenv

load_dotenv()

GOOGLE_DOCS_CREDENTIALS_FILE_NAME = os.getenv("GOOGLE_DOCS_CREDENTIALS_FILE_NAME")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_ADMINS = os.getenv("BOT_ADMINS")

ANALYTICS_SHEET_NAME = "_Analytics"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
