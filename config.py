# config.py
import os
from dotenv import load_dotenv

load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my-secret-token")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "your_whatsapp_access_token")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "your_phone_number_id")
