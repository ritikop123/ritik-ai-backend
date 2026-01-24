import requests
import json
import os

API_KEY = "AIzaSyCyIT_X2QM_I0o_DpqYEd425CM51tMxuU8"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

payload = {
    "contents": [{
        "parts": [{"text": "Hello"}]
    }]
}

headers = {
    "Content-Type": "application/json"
}

print(f"Testing API Key: {API_KEY[:5]}...")
print(f"URL: {URL[:50]}...")

try:
    response = requests.post(URL, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
