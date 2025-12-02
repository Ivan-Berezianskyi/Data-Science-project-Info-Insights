import requests
import json
import sys

def test_notebooks():
    print("\n--- Testing Notebooks Endpoint ---")
    url = "http://localhost:8000/api/notebooks/"
    print(f"GET {url}")
    print("To verify, run the backend server and then:")
    print(f"curl -X GET {url}")

def test_chat_completion_with_notebooks():
    print("\n--- Testing Chat Completion with Notebooks ---")
    url = "http://localhost:8000/api/chat/completion"
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, search in my notebook."}
        ],
        "notebooks": ["test_notebook"]
    }
    
    print(f"Testing {url} with payload: {json.dumps(payload, indent=2)}")
    print("To verify, run the backend server and then:")
    print(f"curl -X POST {url} -H 'Content-Type: application/json' -d '{json.dumps(payload)}'")
    print("\nCheck the response for 'tool_calls' field.")

if __name__ == "__main__":
    test_notebooks()
    test_chat_completion_with_notebooks()
