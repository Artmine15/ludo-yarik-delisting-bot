import json
import logging
import requests
from common import (
    get_headers,
    parse_announcement_data,
    get_processed_ids,
    save_processed_ids,
    send_telegram_notification,
    logger
)

STATE_FILE = "bybit_state.json"

def check_bybit_announcements():
    """Announcements check for Bybit."""
    url = "https://api.bybit.com/v5/announcements/index?category=delistings&limit=10"
    results = []
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if not response.ok:
            logger.error(f"Bybit API error: {response.status_code}")
            return []
        
        data = response.json()
        
        if data.get('retCode') == 0:
            for item in data['result']['list']:
                title = item['title']
                tickers_str, date_str, time_str = parse_announcement_data(title)
                
                results.append({
                    "id": f"bybit_{item['url']}",
                    "message": (
                        f"⚠️ <b>BYBIT DELISTING</b>\n\n"
                        f"🪙 Монеты: {tickers_str}\n"
                        f"📅 Дата: {date_str}\n"
                        f"🕒 Время: {time_str}\n\n"
                        f"🔗 <a href='{item['url']}'>Читать анонс</a>"
                    )
                })
    except Exception as error:
        logger.error(f"Error while checking Bybit: {error}")
        
    return results

def handler(event, context):
    # Check if this is a manual test invocation
    # The event payload should be a JSON like: {"is_test": true}
    if isinstance(event, dict) and event.get('is_test'):
        logger.info("Handling manual test for Bybit handler.")
        test_title = "Gentle Reminder: Bybit Will Delist the ABC/USDT, XYZ/BTC Spot Trading Pairs"
        tickers_str, date_str, time_str = parse_announcement_data(test_title)
        
        message_to_send = (
            f"🧪 <b>TEST BYBIT DELISTING</b> 🧪\n\n"
            f"🪙 Монеты: {tickers_str}\n"
            f"📅 Дата: {date_str}\n"
            f"🕒 Время: {time_str}\n\n"
            f"🔗 <a href='https://www.bybit.com/en/help-center/announcements'>Читать анонс</a>"
        )
        
        send_telegram_notification(message_to_send)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "manual_test_notification_sent"})
        }

    # Regular execution logic
    processed_ids_list = get_processed_ids(STATE_FILE)
    processed_ids_set = set(processed_ids_list)
    
    bybit_news = check_bybit_announcements()
    
    new_alerts_count = 0
    
    for news_item in reversed(bybit_news):
        news_id = news_item['id']
        
        if news_id not in processed_ids_set:
            send_telegram_notification(news_item['message'])
            
            processed_ids_list.append(news_id)
            processed_ids_set.add(news_id)
            new_alerts_count += 1
    
    if new_alerts_count > 0:
        updated_state = processed_ids_list[-50:]
        save_processed_ids(updated_state, STATE_FILE)
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success", "sent": new_alerts_count})
        }
    
    logger.info("No new anouncements for Bybit.")
    return {
        "statusCode": 200,
        "body": json.dumps({"status": "no_new_alerts"})
    }
