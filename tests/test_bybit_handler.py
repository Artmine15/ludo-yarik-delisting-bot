import json
from bybit_handler import handler

def test_bybit_handler_new_announcement(mocker):
    """
    Tests the bybit_handler when there is a new announcement.
    """
    # Mock external dependencies
    mocker.patch('bybit_handler.get_processed_ids', return_value=["bybit_old_url"])
    mock_save_ids = mocker.patch('bybit_handler.save_processed_ids')
    mock_send_notification = mocker.patch('bybit_handler.send_telegram_notification')
    
    # Mock the response from requests.get
    mock_response = mocker.Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {
                    "title": "Bybit Will Delist the NEWCOIN/USDT Spot Trading Pair",
                    "url": "https://bybit.com/new_announcement"
                },
                {
                    "title": "Old announcement",
                    "url": "old_url"
                }
            ]
        }
    }
    mocker.patch('requests.get', return_value=mock_response)

    # Call the handler
    response = handler(None, None)

    # Assertions
    mock_send_notification.assert_called_once()
    
    # Check that the message sent is correct
    sent_message = mock_send_notification.call_args[0][0]
    assert "⚠️ <b>BYBIT DELISTING</b>" in sent_message
    assert "NEWCOIN" in sent_message
    assert "https://bybit.com/new_announcement" in sent_message

    # Check that state is saved correctly
    mock_save_ids.assert_called_once()
    saved_ids = mock_save_ids.call_args[0][0]
    assert "bybit_https://bybit.com/new_announcement" in saved_ids
    assert "bybit_old_url" in saved_ids
    
    # Check the handler response
    assert response['statusCode'] == 200
    assert json.loads(response['body'])['sent'] == 1

def test_bybit_handler_no_new_announcement(mocker):
    """
    Tests the bybit_handler when there are no new announcements.
    """
    # Mock external dependencies
    mocker.patch('bybit_handler.get_processed_ids', return_value=["bybit_https://bybit.com/new_announcement"])
    mock_save_ids = mocker.patch('bybit_handler.save_processed_ids')
    mock_send_notification = mocker.patch('bybit_handler.send_telegram_notification')
    
    # Mock the response from requests.get
    mock_response = mocker.Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {
                    "title": "Bybit Will Delist the NEWCOIN/USDT Spot Trading Pair",
                    "url": "https://bybit.com/new_announcement"
                }
            ]
        }
    }
    mocker.patch('requests.get', return_value=mock_response)

    # Call the handler
    response = handler(None, None)

    # Assertions
    mock_send_notification.assert_not_called()
    mock_save_ids.assert_not_called()
    
    assert response['statusCode'] == 200
    assert json.loads(response['body'])['status'] == "no_new_alerts"
