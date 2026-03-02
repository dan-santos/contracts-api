import os
from dotenv import load_dotenv

load_dotenv()

configs = {
    "database_url": os.getenv("DATABASE_URL"),
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
}