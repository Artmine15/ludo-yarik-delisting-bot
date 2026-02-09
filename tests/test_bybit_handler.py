import json
import pytest
from bybit_handler import handler

# Sample HTML content for a Bybit article
BYBIT_ARTICLE_HTML = """
<html><body>
    <p>We will be delisting the <strong>XYZ/USDT</strong> Perpetual Contract at <strong>10AM UTC on Mar 1, 2026</strong>.</p>
</body></html>
"""

@pytest.fixture
def mock_requests_get(mocker):
    """Fixture to mock requests.get with side effects for different URLs."""
    def get_side_effect(url, headers, timeout):
        mock_resp = mocker.Mock()
        mock_resp.ok = True
        
        # Mock for the API call
        if "api.bybit.com" in url:
            mock_resp.json.return_value = {
                "retCode": 0,
                "result": {
                    "list": [
                        {
                            "title": "Delisting of XYZ/USDT",
                            "url": "https://announcements.bybit.com/en/article/xyz-delist"
                        }
                    ]
                }
            }
        # Mock for the article HTML fetch
        elif "announcements.bybit.com" in url:
            mock_resp.text = BYBIT_ARTICLE_HTML
        
        return mock_resp
    
    return mocker.patch('requests.get', side_effect=get_side_effect)


def test_bybit_handler_new_announcement(mocker, mock_requests_get):
    """
    Tests the bybit_handler when there is a new announcement, including fetching and parsing HTML.
    """
    # Mock other external dependencies
    mocker.patch('bybit_handler.get_processed_ids', return_value=[])
    mock_save_ids = mocker.patch('bybit_handler.save_processed_ids')
    mock_send_notification = mocker.patch('bybit_handler.send_telegram_notification')
    
    # Call the handler
    response = handler(None, None)

    # Assertions
    # Check that requests.get was called twice (API + article)
    assert mock_requests_get.call_count == 2
    
    # Check that a notification was sent
    mock_send_notification.assert_called_once()
    sent_message = mock_send_notification.call_args[0][0]
    assert "⚠️ <b>BYBIT DELISTING</b>" in sent_message
    assert "XYZ" in sent_message
    assert "Mar 1, 2026" in sent_message
    assert "10AM UTC" in sent_message

    # Check that state was saved
    mock_save_ids.assert_called_once()
    saved_ids = mock_save_ids.call_args[0][0]
    assert "bybit_https://announcements.bybit.com/en/article/xyz-delist" in saved_ids
    
    # Check the handler's final response
    assert response['statusCode'] == 200
    assert json.loads(response['body'])['sent'] == 1


def test_bybit_handler_no_new_announcement(mocker, mock_requests_get):
    """
    Tests the bybit_handler when the announcement has already been processed.
    """
    # Mock other external dependencies
    mocker.patch('bybit_handler.get_processed_ids', return_value=["bybit_https://announcements.bybit.com/en/article/xyz-delist"])
    mock_save_ids = mocker.patch('bybit_handler.save_processed_ids')
    mock_send_notification = mocker.patch('bybit_handler.send_telegram_notification')
    
    # Call the handler
    response = handler(None, None)

    # Assertions
    # requests.get is still called once for the API, but not for the article
    assert mock_requests_get.call_count == 1
    
    mock_send_notification.assert_not_called()
    mock_save_ids.assert_not_called()
    
    assert response['statusCode'] == 200
    assert json.loads(response['body'])['status'] == "no_new_alerts"
