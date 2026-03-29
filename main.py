from google import genai
from dotenv import find_dotenv,load_dotenv
import os
dotenv_path = find_dotenv()

load_dotenv(dotenv_path)

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-3-flash-preview",contents="Explain what is a Newsletter"
)

print(response.text)