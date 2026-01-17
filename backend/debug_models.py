import google.generativeai as genai
import os
from dotenv import load_dotenv

print(f"GenAI Version: {genai.__version__}")

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")
print(f"Key: {api_key[:5]}...{api_key[-5:]}")

genai.configure(api_key=api_key)

print("\nListing models...")
try:
    for m in genai.list_models():
        print(f"- {m.name}")
        print(f"  Methods: {m.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTesting gemini-1.5-flash...")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hi")
    print(f"Success! {response.text}")
except Exception as e:
    print(f"Flash failed: {e}")

print("\nTesting gemini-pro...")
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hi")
    print(f"Success! {response.text}")
except Exception as e:
    print(f"Pro failed: {e}")
