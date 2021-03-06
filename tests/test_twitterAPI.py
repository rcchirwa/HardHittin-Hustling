from nose.tools import *
from twitter.twitterAPI import (get_twitter_user_by_screenname,
                                get_twitter_user_followers_count,
                                get_twitter_users_by_ids,
                                get_chunked_twiiter_users_by_ids,
                                get_bulk_users_by_ids,
                                get_authentication,
                                get_epochalypse_now,
                                get_api_reset_time_and_requests_remaining,
                                get_new_followers_user_profiles,
                                get_followers_by_screen_name,
                                get_rate_limit,
                                get_cursor_twitter_rate_limit)
import unittest
import pickle
import os
import json
import time
from mock import patch, mock_open, MagicMock
from twitter.model import User as MongoUser
from tweepy.error import TweepError


class MyTest(unittest.TestCase):
    def get_data_from_json(self, file_name):
        import os
        print os.listdir(".")
        file_path = os.path.join('tests', 'test_data', file_name)
        with open(file_path, "rb") as f:
            data = json.loads(f.read())
        return data

    def test_getepochalypse_now(self):
        epochalypse_now = get_epochalypse_now()
        self.assertAlmostEqual(int(time.time()), epochalypse_now)

    @patch('tweepy.OAuthHandler')
    @patch('tweepy.API')
    @patch('twitter.twitterAPI.logger')
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
    def test_get_api_reset_time_and_requests_remaining(self, mock_api):
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

    @patch('twitter.twitterAPI.get_epochalypse_now')
    @patch('twitter.twitterAPI.get_api_reset_time_and_requests_remaining')
    @patch('tweepy.API')
    def test_get_rate_limit_with_requests_remaining(self, api_mock,
                                                    mock_remaining,
                                                    mock_epoch):
        resource = 'followers'
        path = '/followers/ids'
        json_from_api = self.get_data_from_json("api_limit_status.json")

        rate_limit_resource_path = json_from_api['resources'][resource][path]
        request_window_reset_time = rate_limit_resource_path['reset']
        requests_remaining_in_window = 15
        time_delta = 60*requests_remaining_in_window
        mock_epoch.return_value = request_window_reset_time - time_delta
        mock_remaining.return_value = (request_window_reset_time,
                                       requests_remaining_in_window)
        interval_between_requests1, requests_remaining_in_window1,  request_window_reset_time1 =\
            get_rate_limit(api_mock, resource, path)

        self.assertEqual(60, interval_between_requests1)
        self.assertEqual(requests_remaining_in_window,
                         requests_remaining_in_window1)
        self.assertEqual(request_window_reset_time, request_window_reset_time1)

    @patch('twitter.twitterAPI.get_epochalypse_now')
    @patch('twitter.twitterAPI.get_api_reset_time_and_requests_remaining')
    @patch('tweepy.API')
    def test_get_rate_limit_without_requests_remaining(self, api_mock,
                                                       mock_remaining,
                                                       mock_epoch):
        resource = 'followers'
        path = '/followers/ids'
        json_from_api = self.get_data_from_json("api_limit_status.json")

        rate_limit_resource_path = json_from_api['resources'][resource][path]
        request_window_reset_time = rate_limit_resource_path['reset']
        requests_remaining_in_window = 0
        time_delta = 60*10
        mock_epoch.return_value = request_window_reset_time - time_delta
        mock_remaining.return_value = (request_window_reset_time,
                                       requests_remaining_in_window)
        interval_between_requests1, requests_remaining_in_window1,  request_window_reset_time1 =\
            get_rate_limit(api_mock, resource, path)

        self.assertEqual(time_delta, interval_between_requests1)
        self.assertEqual(0, requests_remaining_in_window1)
        self.assertEqual(request_window_reset_time, request_window_reset_time1)

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

    @patch('twitter.twitterAPI.get_twitter_users_by_ids')
    @patch('twitter.twitterAPI.get_chunked_twiiter_users_by_ids')
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

    @patch('twitter.twitterAPI.User')
    @patch('twitter.twitterAPI.get_bulk_users_by_ids')
    @patch('tweepy.API')
    def test_get_new_followers_user_profiles(self, tweepy_mock,
                                             mocked_get_balk,
                                             user):
        user.objects.return_value.get.return_value =\
            MongoUser(followers_ids=range(1, 201))
        user.objects.return_value.scalar.return_value = range(1, 101)
        get_new_followers_user_profiles(tweepy_mock, "wiz")

        user.objects.return_value.get.assert_called_with()
        user.objects.return_value.scalar.assert_called_with("user_id")
        mocked_get_balk.assert_called_once_with(tweepy_mock,
                                                range(101, 201), 100)

    @patch('twitter.twitterAPI.get_cursor_twitter_rate_limit')
    @patch('tweepy.Cursor')
    @patch('tweepy.API')
    @patch('twitter.twitterAPI.logger')
    def test_get_followers_by_screen_name_success(self,
                                                  mock_logger,
                                                  mock_api,
                                                  tweepy_cursor,
                                                  mock_get_rate_limit):

        mock_get_rate_limit.return_value = (1, 2, 3)
        tweepy_cursor.return_value.pages.return_value = (range(1, 11),
                                                         range(11, 21),
                                                         range(21, 31))

        resource = 'followers'
        path = '/followers/ids'
        screen_name = "Wiz"
        ids, requests = get_followers_by_screen_name(mock_api, screen_name)

        mock_get_rate_limit.assert_called_once_with(mock_api, screen_name,
                                                    resource, path,
                                                    5000)

        self.assertEqual(ids, range(1, 31))
        self.assertEqual(requests, 3)
        self.assertEqual(mock_logger.info.call_count, 6)

    @patch('twitter.twitterAPI.get_cursor_twitter_rate_limit')
    @patch('tweepy.Cursor')
    @patch('tweepy.API')
    @patch('twitter.twitterAPI.logger')
    def test_get_followers_by_screen_name_error(self,
                                                mock_logger,
                                                mock_api,
                                                tweepy_cursor,
                                                mock_get_rate_limit):

        mock_get_rate_limit.return_value = (1, 2, 3)
        error_msg = "Could not authenticate you"
        resp = "32"
        tweepy_cursor.return_value.pages.side_effect = TweepError(error_msg,
                                                                  resp)
        resource = 'followers'
        path = '/followers/ids'
        screen_name = "Wiz"
        ids, requests = get_followers_by_screen_name(mock_api, screen_name)

        mock_get_rate_limit.assert_called_once_with(mock_api, screen_name,
                                                    resource, path,
                                                    5000)
        self.assertEqual(ids, [])
        self.assertEqual(requests, 0)
        mock_logger.error.assert_called_with('Could not authenticate you')

    @patch('twitter.twitterAPI.get_rate_limit')
    @patch('twitter.twitterAPI.get_twitter_user_followers_count')
    @patch('tweepy.API')
    def test_get_cursor_twitter_rate_limit(self, mock_api,
                                           mock_user_follower_count,
                                           mock_get_rate_limit):

        resource = 'followers'
        path = '/followers/ids'
        cursor_size = 5000
        screen_name = 'Wiz'

        mock_user_follower_count.return_value = 20000
        mock_get_rate_limit.return_value = (60, None, None)

        iterations, multiple_iterations, sleep_time =\
            get_cursor_twitter_rate_limit(mock_api, screen_name,
                                          resource, path,
                                          cursor_size)

        self.assertEqual(iterations, 4)
        self.assertTrue(multiple_iterations)
        self.assertEqual(sleep_time, 60)

        mock_user_follower_count.return_value = 12500
        mock_get_rate_limit.return_value = (84, None, None)

        iterations, multiple_iterations, sleep_time =\
            get_cursor_twitter_rate_limit(mock_api, screen_name,
                                          resource, path,
                                          cursor_size)

        self.assertEqual(iterations, 3)
        self.assertTrue(multiple_iterations)
        self.assertEqual(sleep_time, 84)

    @patch('twitter.twitterAPI.get_rate_limit')
    @patch('twitter.twitterAPI.get_twitter_user_followers_count')
    @patch('tweepy.API')
    def test_get_cursor_twitter_rate_limit_one_iteration(self,
                                                         mock_api,
                                                         mock_follower_count,
                                                         mock_get_rate_limit):
        resource = 'followers'
        path = '/followers/ids'
        cursor_size = 5000
        screen_name = 'Wiz'

        mock_follower_count.return_value = 1234
        mock_get_rate_limit.return_value = (60, None, None)

        iterations, multiple_iterations, sleep_time =\
            get_cursor_twitter_rate_limit(mock_api, screen_name,
                                          resource, path,
                                          cursor_size)

        self.assertEqual(iterations, 1)
        self.assertFalse(multiple_iterations)
        self.assertEqual(sleep_time, 0)

if __name__ == '__main__':
    unittest.main()
