import os
import requests
from dotenv import load_dotenv

load_dotenv()

public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
secret_key = os.environ["LANGFUSE_SECRET_KEY"]
host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

auth = (public_key, secret_key)
url = f"{host}/api/public/traces"

response = requests.get(url, auth=auth)
if response.status_code == 200:
    data = response.json()
    print("Total traces:", data.get("meta", {}).get("totalItems"))
    for t in data.get("data", [])[:5]:
        print("Trace ID:", t["id"], "Timestamp:", t["timestamp"], "Name:", t.get("name"))
else:
    print("Error:", response.status_code, response.text)
