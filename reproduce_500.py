import httpx
import json

try:
    resp = httpx.post("http://localhost:8000/api/v1/auth/login", json={"username": "xt765", "password": "123456"}, timeout=10.0)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
