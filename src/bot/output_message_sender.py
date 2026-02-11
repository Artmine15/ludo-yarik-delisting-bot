import requests
import os
from src.env import BOT_TOKEN, CHAT_IDS_LIST

class OutputMessageSender:
    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.chat_ids_config = CHAT_IDS_LIST
        self.telegram_api_base = f"https://api.telegram.org/bot{self.bot_token}"

    def send_telegram_message(self, message: str):
        for chat_config in self.chat_ids_config:
            send_message_endpoint = self.telegram_api_base + '/sendMessage'
            payload = {
                'parse_mode': 'HTML',
                'text': message
            }

            if isinstance(chat_config, str):
                payload['chat_id'] = chat_config
                current_chat_id = chat_config
            elif isinstance(chat_config, dict):
                payload['chat_id'] = chat_config['chat_id']
                payload['message_thread_id'] = chat_config['message_thread_id']
                current_chat_id = f"{chat_config['chat_id']}/{chat_config['message_thread_id']}"
            else:
                print(f"Invalid chat configuration type: {type(chat_config)}. Skipping.")
                continue

            try:
                response = requests.post(send_message_endpoint, json=payload)
                response.raise_for_status()
                print(f"Message sent to chat ID {current_chat_id}: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending message to chat ID {current_chat_id}: {e}")
