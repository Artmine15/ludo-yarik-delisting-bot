from binance_ws import process_binance_message

# Sample HTML content for a Binance article
BINANCE_ARTICLE_HTML = """
<html><body>
    <p>Based on our most recent reviews, we have decided to delist and cease trading on all spot trading pairs for the following token(s) at <strong>2025-02-28 03:00 (UTC)</strong>:</p>
    <p>The exact trading pairs being removed are: <strong>ANT/BTC, ANT/USDT, DAI/BUSD.</strong></p>
</body></html>
"""

def test_process_binance_new_delist_message(mocker):
    """
    Tests processing a new, valid delisting announcement from Binance, including fetching HTML.
    """
    # Mock external dependencies
    mock_send_notification = mocker.patch('binance_ws.send_telegram_notification')
    mock_save_ids = mocker.patch('binance_ws.save_processed_ids')
    
    # Mock the response from requests.get for the article
    mock_response = mocker.Mock()
    mock_response.ok = True
    mock_response.text = BINANCE_ARTICLE_HTML
    mock_requests_get = mocker.patch('requests.get', return_value=mock_response)

    # Initial state
    processed_ids_list = []
    processed_ids_set = set()

    # A mock message from Binance WebSocket
    mock_message = {
        "channel": "binance_announcements",
        "data": {
            "article_title": "Notice on the Removal of Spot Trading Pairs - 2025-02-28",
            "article_url": "https://www.binance.com/en/support/announcement/some-article",
            "article_id": "new_id_123"
        }
    }

    # Call the function to be tested
    process_binance_message(mock_message, processed_ids_list, processed_ids_set)

    # Assertions
    mock_requests_get.assert_called_once_with("https://www.binance.com/en/support/announcement/some-article", headers=mocker.ANY, timeout=20)
    
    mock_send_notification.assert_called_once()
    sent_message = mock_send_notification.call_args[0][0]
    assert "🚨 <b>BINANCE DELISTING</b>" in sent_message
    assert "ANT, DAI" in sent_message
    assert "2025-02-28" in sent_message
    assert "03:00 (UTC)" in sent_message

    mock_save_ids.assert_called_once()
    saved_ids = mock_save_ids.call_args[0][0]
    assert "binance_ws_new_id_123" in saved_ids


def test_process_already_processed_message(mocker):
    """
    Tests that an already processed message is ignored and does not fetch HTML.
    """
    # Mock external dependencies
    mock_requests_get = mocker.patch('requests.get')
    mock_send_notification = mocker.patch('binance_ws.send_telegram_notification')
    mock_save_ids = mocker.patch('binance_ws.save_processed_ids')

    # Initial state
    processed_ids_list = ["binance_ws_existing_id"]
    processed_ids_set = set(processed_ids_list)

    # A mock message that has already been processed
    mock_message = {
        "channel": "binance_announcements",
        "data": {
            "article_title": "Delisting Announcement",
            "article_url": "https://www.binance.com/en/support/announcement/some-article",
            "article_id": "existing_id"
        }
    }

    # Call the function
    process_binance_message(mock_message, processed_ids_list, processed_ids_set)

    # Assertions: Nothing should happen
    mock_requests_get.assert_not_called()
    mock_send_notification.assert_not_called()
    mock_save_ids.assert_not_called()


def test_process_non_delist_message(mocker):
    """
    Tests that a message without delisting keywords is ignored.
    """
    # Mock external dependencies
    mock_requests_get = mocker.patch('requests.get')
    mock_send_notification = mocker.patch('binance_ws.send_telegram_notification')
    mock_save_ids = mocker.patch('binance_ws.save_processed_ids')
    
    # Initial state
    processed_ids_list = []
    processed_ids_set = set()

    # A mock message without delisting keywords
    mock_message = {
        "channel": "binance_announcements",
        "data": {
            "article_title": "Binance Lists New Token",
            "article_url": "https://www.binance.com/en/support/announcement/67890",
            "article_id": "fghij"
        }
    }

    # Call the function
    process_binance_message(mock_message, processed_ids_list, processed_ids_set)

    # Assertions: Nothing should happen
    mock_requests_get.assert_not_called()
    mock_send_notification.assert_not_called()
    mock_save_ids.assert_not_called()
