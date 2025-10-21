import os
from dotenv import load_dotenv
from pathlib import Path
import requests

env_path = Path(__file__).parent.parent / "mesh-client" / ".env"
load_dotenv(env_path)

api_key = os.getenv("BLOCKFROST_PROJECT_ID")
print(f"API Key: {api_key[:20]}...")

# Probar con la API directamente
url = "https://cardano-preview.blockfrost.io/api/v0/epochs/latest"
headers = {"project_id": api_key}

response = requests.get(url, headers=headers)
print(f"\nStatus: {response.status_code}")
print(f"Response: {response.json()}")
