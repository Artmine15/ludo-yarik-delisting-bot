import boto3
import json

from src.env import BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_ENDPOINT_URL

class BybitStorage:
    def __init__(self, storage_file_name: str = "bybit_state.json", max_urls: int = 10):
        s3_config = {
            'aws_access_key_id': AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': AWS_SECRET_ACCESS_KEY,
            'region_name': 'ru-central1'
        }
        if S3_ENDPOINT_URL:
            s3_config['endpoint_url'] = S3_ENDPOINT_URL

        self.s3_client = boto3.client('s3', **s3_config)
        self.bucket_name = BUCKET_NAME
        self.storage_file_name = storage_file_name
        self.max_urls = max_urls

    def load_state(self) -> list[str]:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.storage_file_name)
            file_content = response['Body'].read().decode('utf-8')
            state = json.loads(file_content)
            if not isinstance(state, list):
                print(f"Warning: Loaded state from {self.storage_file_name} is not a list. Initializing with empty list.")
                return []
            return state
        except self.s3_client.exceptions.NoSuchKey:
            print(f"Info: {self.storage_file_name} not found in S3. Initializing with empty list.")
            return []
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {self.storage_file_name}: {e}. Initializing with empty list.")
            return []
        except Exception as e:
            print(f"Error loading state from S3: {e}. Initializing with empty list.")
            return []

    def save_state(self, urls: list[str]):
        try:
            file_content = json.dumps(urls, indent=2)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.storage_file_name,
                Body=file_content,
                ContentType='application/json'
            )
        except Exception as e:
            print(f"Error saving state to S3: {e}")

    def add_and_trim_url(self, new_url: str, current_state: list[str]) -> list[str]:
        if new_url in current_state:
            # If URL already exists, move it to the front (most recent)
            current_state.remove(new_url)
        
        # Add new URL to the front
        current_state.insert(0, new_url)

        # Trim the list if it exceeds max_urls
        return current_state[:self.max_urls]
