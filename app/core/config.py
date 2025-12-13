from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DB_SERVER = os.getenv("DB_SERVER")
    DB_NAME = os.getenv("DB_NAME")
    DB_DRIVER = os.getenv("DB_DRIVER")

settings = Settings()
