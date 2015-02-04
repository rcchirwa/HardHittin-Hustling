from twitterAPI import (get_twitter_user_by_screenname,
                        get_twitter_user_followers_count,
                        get_twitter_users_by_ids,
                        get_chunked_twiiter_users_by_ids,
                        get_bulk_users_by_ids)
import tweepy
import unittest
import pickle
import os
from mock import patch, mock_open, MagicMock


class MyTest(unittest.TestCase):
    '''def setUp(self):
        self.row_form_board = self.get_data_from_dat("board_as_rows.dat")
        self.flat_board = self.get_data_from_dat("board_as_series.dat")'''

    def get_data_from_dat(self, file_name):
        file_path = os.path.join('unitest_data', file_name)
        with open(file_path, "rb") as f:
            data = pickle.load(f)
        return data

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
