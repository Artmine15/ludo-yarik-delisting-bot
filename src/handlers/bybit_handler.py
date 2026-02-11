from src.repositories.bybit.bybit_client import BybitClient
from src.bot.output_message_sender import OutputMessageSender
from src.repositories.bybit.bybit_storage import BybitStorage
from src.utils.bybit.bybit_parser import parse_description
from src.utils.output_message_formatter import format_delisting_message

def handle_bybit_announcements(event, context):
    """
    Handles the Bybit announcement check.
    This function is intended to be called by a Yandex Cloud Function.
    """
    bybit_client = BybitClient()
    output_sender = OutputMessageSender()
    bybit_storage = BybitStorage() # Initialize BybitStorage

    try:
        announcements = bybit_client.get_announcements()
        current_state_urls = bybit_storage.load_state() # Load current state
        new_urls_to_store = list(current_state_urls) # Copy for modifications

        if "result" in announcements and "list" in announcements["result"]:
            for announcement in announcements["result"]["list"]:
                if "description" in announcement and "url" in announcement:
                    url = announcement["url"]
                    if url not in current_state_urls: # Check if URL is new
                        description = announcement["description"]
                        
                        # Parse description
                        parsed_data = parse_description(description)
                        
                        # Format message
                        formatted_message = format_delisting_message(
                            header="BYBIT", # Static header for now
                            tickers=parsed_data.get("tickers"),
                            date=parsed_data.get("date"),
                            time=parsed_data.get("time"),
                            announcement_url=url
                        )
                        output_sender.send_telegram_message(formatted_message)
                        
                        # Add new URL to the state, trimming if necessary
                        new_urls_to_store = bybit_storage.add_and_trim_url(url, new_urls_to_store)
        else:
            # Handle case where expected structure is not found
            error_message = "Bybit announcements response did not contain expected 'result.list' structure."
            print(error_message)
            output_sender.send_telegram_message(f"Error: {error_message}")
        
        bybit_storage.save_state(new_urls_to_store) # Save updated state

        return {
            'statusCode': 200,
            'body': 'Successfully processed and sent Bybit delisting announcements.'
        }
    except Exception as e:
        error_message = f"Error handling Bybit announcements: {e}"
        print(error_message)
        output_sender.send_telegram_message(f"Error: {error_message}")
        return {
            'statusCode': 500,
            'body': error_message
        }
