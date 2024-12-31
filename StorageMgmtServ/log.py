import httpx
import dotenv
import os

# Load environment variables from .env file
dotenv.load_dotenv()

url = os.getenv("LOG_URL")


def send_log(username, service_name, log_level, message):
    log_entry = {
        "username": username,
        "service_name": service_name,
        "log_level": log_level,
        "message": message,
    }
    try:
        httpx.post(f"{url}/log/", json=log_entry)
    except Exception as e:
        print(f"Failed to send log: {e}")
