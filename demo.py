#!/usr/bin/env python
"""Demo script to showcase AI Memos functionality."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"


def print_json(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))


def main():
    """Run the demo."""
    print("=" * 60)
    print("AI Memos Demo")
    print("=" * 60)
    
    # Check server health
    print("\n1. Checking server health...")
    response = requests.get(f"{BASE_URL}/health")
    print_json(response.json())
    
    # Create a memo
    print("\n2. Creating a new memo...")
    memo1 = {
        "title": "FastAPI Best Practices",
        "content": "Always use type hints, async/await for I/O operations, and dependency injection.",
        "tags": ["fastapi", "python", "best-practices"]
    }
    response = requests.post(f"{API_URL}/memos", json=memo1)
    memo1_data = response.json()
    memo1_id = memo1_data["id"]
    print_json(memo1_data)
    
    # Create another memo
    print("\n3. Creating another memo...")
    memo2 = {
        "title": "PocketFlow Integration",
        "content": "PocketFlow enables building AI-powered workflows with ease.",
        "tags": ["ai", "pocketflow", "workflow"]
    }
    response = requests.post(f"{API_URL}/memos", json=memo2)
    memo2_data = response.json()
    print_json(memo2_data)
    
    # List all memos
    print("\n4. Listing all memos...")
    response = requests.get(f"{API_URL}/memos")
    print_json(response.json())
    
    # Search for memos
    print("\n5. Searching for 'fastapi'...")
    response = requests.get(f"{API_URL}/memos/search", params={"q": "fastapi"})
    print_json(response.json())
    
    # Update a memo
    print("\n6. Updating the first memo...")
    update_data = {
        "title": "FastAPI Best Practices (Updated)",
        "tags": ["fastapi", "python", "best-practices", "updated"]
    }
    response = requests.put(f"{API_URL}/memos/{memo1_id}", json=update_data)
    print_json(response.json())
    
    # Get specific memo
    print("\n7. Getting the updated memo...")
    response = requests.get(f"{API_URL}/memos/{memo1_id}")
    print_json(response.json())
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Please make sure the server is running with: uv run aimemos")
    except Exception as e:
        print(f"Error: {e}")
