import requests

class BybitClient:
    def __init__(self):
        self.base_url = "https://api.bybit.com/v5/announcements/index"

    def get_announcements(self) -> dict:
        params = {
            "locale": "en-US",
            "limit": 5,
            "type": "delistings"
        }
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()
