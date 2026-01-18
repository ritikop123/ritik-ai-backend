import requests
import json
import time

def test_backend():
    print("Testing backend health...")
    try:
        r = requests.get("http://localhost:8000/health")
        print(f"Health check: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    print("\nTesting chat endpoint...")
    try:
        payload = {
            "message": "Who made you?",
            "conversation_history": []
        }
        r = requests.post("http://localhost:8000/api/chat", json=payload)
        print(f"Chat check: {r.status_code}")
        if r.status_code == 200:
            print(f"Response Text: {r.json()['response']}")
        else:
            print(f"Error: {r.text}")
            print(f"Full response: {r.content}")
    except Exception as e:
        print(f"Chat check failed: {e}")

if __name__ == "__main__":
    test_backend()
