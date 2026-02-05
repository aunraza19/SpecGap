import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load env variables
load_dotenv()

class Settings:
    PROJECT_NAME: str = "SpecGap AI Audit"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

settings = Settings()

# Configure Gemini once at startup
if not settings.GEMINI_API_KEY:
    raise ValueError("❌ API Key missing! Check your .env file.")

genai.configure(api_key=settings.GEMINI_API_KEY)

model_text = genai.GenerativeModel('gemini-3-flash-preview')
model_vision = genai.GenerativeModel('gemini-3-flash-preview')