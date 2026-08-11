import os
import requests
from dotenv import load_dotenv


def main() -> int:
    """Fetch a small Langfuse trace summary when run explicitly.

    Keep network access out of module import so pytest collection remains
    deterministic and does not require Langfuse credentials or DNS access.
    """
    load_dotenv()

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        print("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required")
        return 1

    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")
    response = requests.get(
        f"{host}/api/public/traces",
        auth=(public_key, secret_key),
        timeout=10,
    )
    if response.status_code == 200:
        data = response.json()
        print("Total traces:", data.get("meta", {}).get("totalItems"))
        for trace in data.get("data", [])[:5]:
            print(
                "Trace ID:",
                trace["id"],
                "Timestamp:",
                trace["timestamp"],
                "Name:",
                trace.get("name"),
            )
        return 0

    print("Error:", response.status_code, response.text)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
