import os

from dotenv import load_dotenv


load_dotenv(override=True)

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

DELAY = 10
MESSAGE = ""
AUTO_REPLY_MESSAGE = ""