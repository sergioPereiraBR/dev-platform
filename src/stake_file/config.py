#   src/dev_platform/infrastructure/config.py
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
#   You might want to handle the case where DATABASE_URL is not set