from binance_ws import process_binance_message

def test_process_binance_new_delist_message(mocker):
    """
    Tests processing a new, valid delisting announcement from Binance.
    """
    # Mock external dependencies
    mock_send_notification = mocker.patch('binance_ws.send_telegram_notification')
    mock_save_ids = mocker.patch('binance_ws.save_processed_ids')

    # Initial state
    processed_ids_list = ["binance_ws_123"]
    processed_ids_set = set(processed_ids_list)

    # A mock message from Binance WebSocket
    mock_message = {
        "channel": "binance_announcements",
        "data": {
            "article_title": "Binance to Delist TORN on 2023-12-25",
            "article_url": "https://www.binance.com/en/support/announcement/12345",
            "article_id": "abcde"
        }
    }

    # Call the function to be tested
    process_binance_message(mock_message, processed_ids_list, processed_ids_set)

    # Assertions
    mock_send_notification.assert_called_once()
    sent_message = mock_send_notification.call_args[0][0]
    assert "🚨 <b>BINANCE DELISTING</b>" in sent_message
    assert "TORN" in sent_message
    assert "2023-12-25" in sent_message
    assert "https://www.binance.com/en/support/announcement/12345" in sent_message

    mock_save_ids.assert_called_once()
    saved_ids = mock_save_ids.call_args[0][0]
    assert "binance_ws_abcde" in saved_ids
    assert "binance_ws_123" in saved_ids


def test_process_already_processed_message(mocker):
    """
    Tests that an already processed message is ignored.
    """
    # Mock external dependencies
    mock_send_notification = mocker.patch('binance_ws.send_telegram_notification')
    mock_save_ids = mocker.patch('binance_ws.save_processed_ids')

    # Initial state
    processed_ids_list = ["binance_ws_abcde"]
    processed_ids_set = set(processed_ids_list)

    # A mock message that has already been processed
    mock_message = {
        "channel": "binance_announcements",
        "data": {
            "article_title": "Binance to Delist TORN on 2023-12-25",
            "article_url": "https://www.binance.com/en/support/announcement/12345",
            "article_id": "abcde"
        }
    }

    # Call the function
    process_binance_message(mock_message, processed_ids_list, processed_ids_set)

    # Assertions: Nothing should happen
    mock_send_notification.assert_not_called()
    mock_save_ids.assert_not_called()


def test_process_non_delist_message(mocker):
    """
    Tests that a message without delisting keywords is ignored.
    """
    # Mock external dependencies
    mock_send_notification = mocker.patch('binance_ws.send_telegram_notification')
    mock_save_ids = mocker.patch('binance_ws.save_processed_ids')

    # Initial state
    processed_ids_list = []
    processed_ids_set = set(processed_ids_list)

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
    mock_send_notification.assert_not_called()
    mock_save_ids.assert_not_called()
