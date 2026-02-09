import json
import logging
import requests
from common import (
    get_headers,
    parse_article_content,
    get_processed_ids,
    save_processed_ids,
    send_telegram_notification,
    format_delisting_message,
    logger
)

STATE_FILE = "bybit_state.json"

def get_bybit_announcements():
    """Fetches a list of delisting announcement summaries from Bybit."""
    api_url = "https://api.bybit.com/v5/announcements/index?category=delistings&limit=10"
    announcements = []
    
    try:
        response = requests.get(api_url, headers=get_headers(), timeout=15)
        if not response.ok:
            logger.error(f"Bybit API error: {response.status_code}")
            return []
        
        data = response.json()
        
        if data.get('retCode') == 0:
            for item in data['result']['list']:
                title = item.get('title', '')
                keywords = ["delist", "removal", "cease"]
                if any(word in title.lower() for word in keywords):
                    announcements.append({
                        "title": title,
                        "url": item.get('url')
                    })
    except Exception as error:
        logger.error(f"Error while fetching Bybit announcements: {error}")
        
    return announcements

def handler(event, context):
    # Check if this is a manual test invocation
    if isinstance(event, dict) and event.get('is_test'):
        logger.info("Handling manual test for Bybit handler.")
        
        html_content = event.get('html_content')
        url = event.get('url')

        if not html_content or not url:
            logger.warning("Test invocation is missing 'html_content' or 'url' in payload.")
            return {
                "statusCode": 400,
                "body": json.dumps({"status": "error", "message": "Missing 'html_content' or 'url' for test."})
            }

        tickers_str, date_str, time_str = parse_article_content(html_content, url)
        
        message_to_send = format_delisting_message(
            "BYBIT", tickers_str, date_str, time_str, url, is_test=True
        )
        
        send_telegram_notification(message_to_send)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "manual_test_notification_sent"})
        }

    # Regular execution logic
    processed_ids_list = get_processed_ids(STATE_FILE)
    processed_ids_set = set(processed_ids_list)
    
    announcements = get_bybit_announcements()
    new_alerts_count = 0
    
    for ann in reversed(announcements):
        news_id = f"bybit_{ann['url']}"
        
        if news_id not in processed_ids_set:
            try:
                # Fetch article content
                response = requests.get(ann['url'], headers=get_headers(), timeout=20)
                if not response.ok:
                    logger.error(f"Failed to fetch Bybit article {ann['url']}: Status {response.status_code}")
                    continue

                # Parse content to get details
                tickers_str, date_str, time_str = parse_article_content(response.text, ann['url'])

                # Format and send message
                message = format_delisting_message(
                    "BYBIT", tickers_str, date_str, time_str, ann['url']
                )
                send_telegram_notification(message)

                # Update state
                processed_ids_list.append(news_id)
                processed_ids_set.add(news_id)
                new_alerts_count += 1

            except Exception as e:
                logger.error(f"Error processing Bybit announcement {ann['url']}: {e}")

    if new_alerts_count > 0:
        updated_state = processed_ids_list[-50:]
        save_processed_ids(updated_state, STATE_FILE)
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success", "sent": new_alerts_count})
        }
    
    logger.info("No new announcements for Bybit.")
    return {
        "statusCode": 200,
        "body": json.dumps({"status": "no_new_alerts"})
    }
