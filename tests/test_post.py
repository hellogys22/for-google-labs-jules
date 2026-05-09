import unittest
from unittest.mock import patch, MagicMock
import os
import time

from agents.post_agent import post_to_instagram

class TestPostAgent(unittest.TestCase):

    @patch('agents.post_agent.requests.post')
    @patch('agents.post_agent.get_db')
    @patch('agents.post_agent.requests.get')
    @patch('agents.post_agent.time.sleep') # mock sleep so tests run fast
    @patch('agents.post_agent.access_token', 'test_token')
    @patch('agents.post_agent.account_id', 'test_account')
    def test_post_to_instagram_success(self, mock_sleep, mock_get, mock_get_db, mock_post):
        """Test the successful flow of posting to Instagram."""
        # 1. Mock create media container
        mock_create_response = MagicMock()
        mock_create_response.json.return_value = {'id': '12345'}

        # 2. Mock publish media
        mock_publish_response = MagicMock()
        mock_publish_response.json.return_value = {'id': '98765'}

        mock_post.side_effect = [mock_create_response, mock_publish_response]

        # Mock status polling (first ERROR or IN_PROGRESS, then FINISHED)
        mock_status_response_1 = MagicMock()
        mock_status_response_1.json.return_value = {'status_code': 'IN_PROGRESS'}

        mock_status_response_2 = MagicMock()
        mock_status_response_2.json.return_value = {'status_code': 'FINISHED'}

        mock_get.side_effect = [mock_status_response_1, mock_status_response_2]

        post_id = post_to_instagram("http://test.mp4", "Test caption")

        self.assertEqual(post_id, '98765')
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('agents.post_agent.requests.post')
    @patch('agents.post_agent.requests.get')
    @patch('agents.post_agent.time.sleep')
    @patch('agents.post_agent.access_token', 'test_token')
    @patch('agents.post_agent.account_id', 'test_account')
    def test_post_to_instagram_timeout(self, mock_sleep, mock_get, mock_post):
        """Test exponential backoff timeout."""
        mock_create_response = MagicMock()
        mock_create_response.json.return_value = {'id': '12345'}
        mock_post.return_value = mock_create_response

        # Always return IN_PROGRESS
        mock_status_response = MagicMock()
        mock_status_response.json.return_value = {'status_code': 'IN_PROGRESS'}
        mock_get.return_value = mock_status_response

        with self.assertRaises(Exception) as context:
            post_to_instagram("http://test.mp4", "Test caption")

        self.assertTrue("timed out" in str(context.exception))
        self.assertEqual(mock_get.call_count, 3) # Max 3 retries

if __name__ == '__main__':
    unittest.main()