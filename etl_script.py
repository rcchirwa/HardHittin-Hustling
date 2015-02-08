#! /usr/bin/env python
import time

import twitter.api_keys as twitter_keys
from twitter.model import User
from twitter.twitterAPI import (get_bulk_users_by_ids,
                                get_rate_limit,
                                get_authentication,
                                get_followers_by_screen_name,
                                get_bulk_users_by_ids)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = get_authentication(twitter_keys.api_keys)

screen_name = "HardHittin508"

#  Get the artists info and create profile
tweepy_user = api.get_user(screen_name)

user = User.create_user_profile_from_api_response(tweepy_user)

user.save()

#  Get the artist followers then create the user profiles
followers, requests_used = get_followers_by_screen_name(api, screen_name)

User.set_followers(screen_name, followers)

followers = User.get_followers(screen_name)

for users in get_bulk_users_by_ids(api, followers, 100):
   User.bulk_create_and_save_users_from_api_reponse(users)

# get all the user who do not have followers
no_followers = list(User.get_twiiter_users_without_followers())

no_followers_count = len(no_followers)

request_accumulator = 0
cycles = 1

# get some information form the API to help use avoid the rate limits
sleep_delay, requests_remaining, next_reset_epoch =\
    get_rate_limit(api, 'followers', '/followers/ids')

logger.info("current sleep_delay time: %s", sleep_delay)
logger.info("requests_remaining: %s", requests_remaining)


# lets just do a batch of 60 for now
for index, user in enumerate(no_followers[:60], start=1):
    epochalpse_now = int(time.time())
    # Gather the various parameters from twiiter so we avoid rate limits
    if (request_accumulator == requests_remaining) or \
       (epochalpse_now > next_reset_epoch):
        sleep_delay, requests_remaining, next_reset_epoch =\
            get_rate_limit(api, 'followers', '/followers/ids')
        request_accumulator = 0

    logger_values = (user, index, no_followers_count)
    logger.info('GETTING FOLLOWERS: Processing  %s %s of %s' % logger_values)

    #  acutally get the folowers
    followers, cycles = get_followers_by_screen_name(api, user)
    User.set_followers(user, followers)
    followers = []
    request_accumulator += cycles

    logger.info("request_accumulator: %s" % request_accumulator)
    logger.info("current sleep_delay time: %s", sleep_delay)
    logger.info("requests_remaining: %s", requests_remaining)

    time.sleep(sleep_delay)
