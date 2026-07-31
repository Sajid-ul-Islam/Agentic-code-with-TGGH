import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    model = genai.GenerativeModel("gemini-flash-latest")
    response = model.generate_content("hello")
    print(response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
