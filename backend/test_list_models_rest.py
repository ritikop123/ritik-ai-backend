import requests
import json

API_KEY = "AIzaSyCyIT_X2QM_I0o_DpqYEd425CM51tMxuU8"
URL = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

print(f"Testing List Models with Key: {API_KEY[:5]}...")

try:
    response = requests.get(URL)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        models = response.json().get('models', [])
        print(f"Found {len(models)} models:")
        with open("models_list.txt", "w") as f:
            for m in models:
                name = m['name']
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    f.write(f"AVAILABLE: {name}\n")
        print("Models list written to models_list.txt")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
