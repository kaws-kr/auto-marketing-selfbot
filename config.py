import os

from dotenv import load_dotenv


load_dotenv(override=True)

TOKEN = os.getenv("TOKEN")

DELAY = 10
MESSAGE = ""
AUTO_REPLY_MESSAGE = ""