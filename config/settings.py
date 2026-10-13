import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "DrishtiCare AI"
APP_ENV = os.getenv("APP_ENV", "development")
PUBLIC_DEMO = os.getenv("PUBLIC_DEMO", "true").lower() == "true"
UPLOAD_MAX_MB = int(os.getenv("UPLOAD_MAX_MB", "10"))
