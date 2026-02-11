import os
import json

def _get_required_env_var(var_name: str) -> str:
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"Environment variable {var_name} must be set.")
    return value

BOT_TOKEN = _get_required_env_var("BOT_TOKEN")
_chat_ids_json_string = _get_required_env_var("CHAT_IDS")
try:
    CHAT_IDS_LIST = json.loads(_chat_ids_json_string)
    if not isinstance(CHAT_IDS_LIST, list):
        raise ValueError("CHAT_IDS environment variable must be a JSON array.")
    for item in CHAT_IDS_LIST:
        if isinstance(item, str):
            # Simple chat ID
            if not item:
                raise ValueError("Chat ID string cannot be empty.")
        elif isinstance(item, dict):
            # Chat ID with message_thread_id
            if "chat_id" not in item or "message_thread_id" not in item:
                raise ValueError("Each object in CHAT_IDS must contain 'chat_id' and 'message_thread_id'.")
            if not isinstance(item["chat_id"], str) or not item["chat_id"]:
                raise ValueError("chat_id in CHAT_IDS object must be a non-empty string.")
            if not isinstance(item["message_thread_id"], int):
                raise ValueError("message_thread_id in CHAT_IDS object must be an integer.")
        else:
            raise ValueError("Each item in CHAT_IDS must be either a string or an object with 'chat_id' and 'message_thread_id'.")
except json.JSONDecodeError:
    raise ValueError("CHAT_IDS environment variable is not a valid JSON string.")

BUCKET_NAME = _get_required_env_var("BUCKET_NAME")
AWS_ACCESS_KEY_ID = _get_required_env_var("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = _get_required_env_var("AWS_SECRET_ACCESS_KEY")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "https://storage.yandexcloud.net")