from twitterAPI import (get_twitter_user_by_screenname,
                        get_twitter_user_followers_count,
                        get_twitter_users_by_ids,
                        get_chunked_twiiter_users_by_ids,
                        get_bulk_users_by_ids,
                        get_authentication,
                        get_epochalypse_now,
                        get_api_reset_time_and_requests_remaining)
import tweepy
import unittest
import pickle
import os
import json
import time
from mock import patch, mock_open, MagicMock


class MyTest(unittest.TestCase):
    def get_data_from_json(self, file_name):
        import os
        print os.listdir(".")
        file_path = os.path.join('twitter','test_data', file_name)
        with open(file_path, "rb") as f:
            data = json.loads(f.read())
        return data

    def test_getepochalypse_now(self):
        epochalypse_now = get_epochalypse_now()
        self.assertAlmostEqual(int(time.time()), epochalypse_now)

    @patch('tweepy.OAuthHandler')
    @patch('tweepy.API')
    @patch('twitterAPI.logger')
    def test_get_authentication(self, mock_logger, mock_api,
                                mock_oauth):

        fake_keys = dict(access_token="access_token",
                         access_token_secret="access_token_secret",
                         consumer_key="consumer_key",
                         consumer_secret="consumer_secret")
        get_authentication(fake_keys)

        mock_oauth.assert_called_once_with("consumer_key",
                                           "consumer_secret")
        mock_oauth.return_value.set_access_token.assert_called_once_with(
            "access_token", "access_token_secret")
        mock_api.assert_called_once()
        self.assertEqual(mock_logger.info.call_count, 2)


    @patch('tweepy.API')
    def test_get_api_reset_time_and_requests_remaining(self,
        mock_api):
        resource = 'followers' 
        path = '/followers/ids'
        json_from_api = self.get_data_from_json("api_limit_status.json")

        mock_api.rate_limit_status.return_value = json_from_api
        limit_info = {u'reset': 1423182262,
            u'limit': 15, u'remaining': 4} 
        request_window_reset_time, requests_remaining_in_window =\
        get_api_reset_time_and_requests_remaining(mock_api,
            resource, 
            path)

        self.assertEqual(request_window_reset_time, limit_info['reset'])
        self.assertEqual(requests_remaining_in_window, limit_info['remaining'])


    @patch('tweepy.API')
    def test_get_twitter_user_by_screenname(self, tweepy_mock):
        get_twitter_user_by_screenname(tweepy_mock, 'HardHittinEnt')
        tweepy_mock.get_user.assert_called_with('HardHittinEnt')

    @patch('tweepy.API')
    def test_get_twitter_user_followers_count(self, tweepy_mock):
        get_twitter_user_followers_count(tweepy_mock, 'HardHittinEnt')
        tweepy_mock.get_user.assert_called_with('HardHittinEnt')

    @patch('tweepy.API')
    def test_get_twitter_users_by_ids(self, tweepy_mock):
        a = range(0, 10)
        get_twitter_users_by_ids(tweepy_mock, a)
        tweepy_mock.lookup_users.assert_called_with(user_ids=a)

    def test_get_chunked_twiiter_users_by_ids(self):
        ids = range(1, 21)
        batch_size = 4

        iterator = get_chunked_twiiter_users_by_ids(ids, batch_size=batch_size)
        self.assertEqual(iterator.next(), range(1, 5))
        self.assertEqual(iterator.next(), range(5, 9))
        self.assertEqual(iterator.next(), range(9, 13))
        self.assertEqual(iterator.next(), range(13, 17))
        self.assertEqual(iterator.next(), range(17, 21))

    @patch('twitterAPI.get_twitter_users_by_ids')
    @patch('twitterAPI.get_chunked_twiiter_users_by_ids')
    @patch('tweepy.API')
    def test_get_bulk_users_by_ids(self, tweepy_mock, mocked_chunked,
                                   mocked_get_user):
        full_range = range(1, 12)
        subset1 = range(1, 7)
        subset2 = range(7, 12)
        subset3 = ['a', 'b', 'c', 'd', 'e', 'f']
        subset4 = ['g', 'h', 'i', 'j', 'k']
        mocked_chunked.return_value = iter([subset1, subset2])
        mocked_get_user.side_effect = [subset3, subset4]

        iterator = get_bulk_users_by_ids(tweepy_mock, full_range, batch_size=6)
        self.assertEqual(iterator.next(), subset3)
        self.assertEqual(iterator.next(), subset4)

if __name__ == '__main__':
    unittest.main()
