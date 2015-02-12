import time
import datetime

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import tweepy
from model import User as User


def get_epochalypse_now():
    return int(time.time())


def get_authentication(twitter_keys):
    logger.info('Attempt Twitter Authentication')
    access_token = twitter_keys['access_token']
    access_token_secret = twitter_keys['access_token_secret']
    consumer_key = twitter_keys["consumer_key"]
    consumer_secret = twitter_keys["consumer_secret"]

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    logger.info('Twitter Authentication Successful')

    return api


def get_api_reset_time_and_requests_remaining(api, resource, path):
    rate_limit_json = api.rate_limit_status()
    rate_limit_resource_path = rate_limit_json['resources'][resource][path]
    request_window_reset_time = rate_limit_resource_path['reset']
    requests_remaining_in_window = rate_limit_resource_path['remaining']
    return request_window_reset_time, requests_remaining_in_window


def get_rate_limit(api, resource, path):
    request_window_reset_time, requests_remaining_in_window =\
        get_api_reset_time_and_requests_remaining(api, resource, path)
    epochalpse_now = get_epochalypse_now()

    time_delta = (request_window_reset_time-epochalpse_now)

    if requests_remaining_in_window != 0:
        interval_between_requests = time_delta/requests_remaining_in_window
    else:
        interval_between_requests = time_delta

    return (interval_between_requests,
            requests_remaining_in_window, request_window_reset_time)


def get_cursor_twitter_rate_limit(api, screen_name, cursor_size):
    multiple_iterations = False
    api_followers_count = get_twitter_user_followers_count(api, screen_name)

    iterations = api_followers_count/cursor_size + 1
    sleep_time = 0

    if iterations > 1:
        sleep_time, _, _ = get_rate_limit(api, 'followers', '/followers/ids')
        multiple_iterations = True

    return iterations, multiple_iterations, sleep_time


def get_followers_by_screen_name(api, screen_name, cursor_size=5000):
    logger.info("get the followers for %s", screen_name)
    extracted_user_ids = []
    requested_used = 0

    iterations, multiple_iterations, sleep_time =\
        get_cursor_twitter_rate_limit(api, screen_name, cursor_size)

    try:
        #  5000 count returned
        tweepy_cursor = tweepy.Cursor(api.followers_ids,
                                      screen_name=screen_name)

        for index, page in enumerate(tweepy_cursor.pages(), start=1):
            logger.info('extracting page %s of %s' % (index, iterations))
            extracted_user_ids.extend(page)
            requested_used = index

            #  do not do last one because no need to wait
            if (multiple_iterations and (index != iterations)):
                logger.info('current sleep time: %s ' % sleep_time)
                time.sleep(sleep_time)

    except Exception, e:

        logger.error("failed Error for the screenname: %s ", screen_name)
        logger.error(str(e))
        return extracted_user_ids, requested_used

    return extracted_user_ids, requested_used


def get_twitter_user_by_screenname(api, screen_name):
    try:
        return api.get_user(screen_name)
    except Exception, e:
        user = User.flag_suspect_profile(screen_name)
        print user
        logger.error("failed Error for the screenname: %s ", screen_name)
        logger.error(str(e))
        User.flag_suspect_profile(screen_name)


def get_twitter_user_followers_count(api, screen_name):
    try:
        return api.get_user(screen_name).followers_count
    except Exception, e:
        user = User.flag_suspect_profile(screen_name)
        print user
        logger.error("failed Error for the screenname: %s ", screen_name)
        logger.error(str(e))
        User.flag_suspect_profile(screen_name)

def get_twitter_users_by_ids(api, ids):
    return api.lookup_users(user_ids=ids)


def get_chunked_twiiter_users_by_ids(ids, batch_size=100):
    modulated_number = len(ids)/batch_size*batch_size

    for i in xrange(0, modulated_number, batch_size):
        user_ids = ids[i: i+batch_size]
        yield user_ids

    tail_of_user_ids = ids[modulated_number:]

    yield tail_of_user_ids


def get_bulk_users_by_ids(api, ids, batch_size=100):
    for chunked_ids in get_chunked_twiiter_users_by_ids(ids, batch_size):
        users = get_twitter_users_by_ids(api, chunked_ids)
        yield users

def get_new_followers_user_profiles(api, user_screen_name):
    users_followers = User.objects(screen_name=user_screen_name).get()
    user_ids = User.objects().scalar('user_id')
    ids_to_populate = list(set(users_followers.followers_ids).difference(user_ids))

    for user in get_bulk_users_by_ids(api, ids_to_populate, 100):
        User.bulk_create_and_save_users_from_api_reponse(user)
