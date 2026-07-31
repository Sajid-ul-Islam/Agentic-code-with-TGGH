import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

messages = [
    {
        "role": "user",
        "parts": ["hello"]
    }
]

model = genai.GenerativeModel("gemini-flash-latest")
try:
    response = model.generate_content(messages)
    print("Success:", response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
