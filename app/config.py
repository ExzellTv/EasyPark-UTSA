import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
CAMERA_FEED_URL = os.getenv("CAMERA_FEED_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
