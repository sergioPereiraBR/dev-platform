#   src/infrastructure/config.py (similar to your config.py, but in the Infrastructure layer)
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
#   You might want to handle the case where DATABASE_URL is not set