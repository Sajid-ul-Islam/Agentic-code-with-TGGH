import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_weather(location: str) -> str:
    """Gets the weather for a location"""
    return f"The weather in {location} is 72F and sunny."

model = genai.GenerativeModel("gemini-flash-latest", tools=[get_weather])
chat = model.start_chat()

response = chat.send_message("What is the weather in Tokyo?")
print("Response parts:", response.parts)
fc = response.parts[0].function_call
if fc:
    print("Function call:", fc.name, fc.args)
    # Send function result
    result_response = chat.send_message(
        {
            "function_response": {
                "name": fc.name,
                "response": {"result": get_weather(fc.args['location'])}
            }
        }
    )
    print("Final response:", result_response.text)
