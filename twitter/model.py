from mongoengine import *
from mongoengine import signals

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import datetime


class User(Document):
    screen_name = StringField(unique=True, required=True)
    name = StringField(required=True)
    user_id = IntField(unique=True, required=True)
    user_id_str = StringField(unique=True, required=True)
    description = StringField()

    location = StringField()
    time_zone = StringField()
    lang = StringField()

    geo_enabled = BooleanField()
    protected = BooleanField()

    followers_count = IntField()
    friends_count = IntField()
    statuses_count = IntField()
    listed_count = IntField()

    followers_ids = ListField()
    common_followers = ListField()

    suspect_profile = BooleanField(default=False)

    date_modified = DateTimeField(default=datetime.datetime.now)

    @classmethod
    def get_twiiter_users_without_followers(cls, cut_off=20000):
        filtered_users = cls.objects(followers_count__lte=cut_off,
                                     protected=False, followers_ids=[],
                                     suspect_profile__ne=True)
        users_without_followers = filtered_users.scalar('screen_name')
        return users_without_followers

    @classmethod
    def set_followers(cls, screen_name, followers_ids):
        identified_user = cls.objects(screen_name=screen_name).get()
        identified_user.followers_ids = followers_ids
        identified_user.followers_count = len(followers_ids)
        identified_user.save()

    @classmethod
    def get_followers(cls, screen_name):
        identified_user = cls.objects(screen_name=screen_name).first()
        return identified_user.followers_ids

    @classmethod
    def flag_suspect_profile(cls, screen_name):
        identified_user = cls.objects(screen_name=screen_name).first()
        identified_user.suspect_profile = True
        identified_user.save()

    @classmethod
    def is_suspect_profile(cls, screen_name):
        identified_user = cls.objects(screen_name=screen_name).first()
        return identified_user.suspect_profile

    @classmethod
    def create_user_profile_from_api_response(cls, twitter_user):
        user_profile = cls()
        user_profile.screen_name = twitter_user.screen_name
        user_profile.name = twitter_user.name
        user_profile.location = twitter_user.location
        user_profile.user_id = twitter_user.id
        user_profile.user_id_str = twitter_user.id_str
        user_profile.geo_enabled = twitter_user.geo_enabled
        user_profile.followers_count = twitter_user.followers_count
        user_profile.friends_count = twitter_user.friends_count
        user_profile.statuses_count = twitter_user.statuses_count
        user_profile.time_zone = twitter_user.time_zone
        user_profile.lang = twitter_user.lang
        user_profile.listed_count = twitter_user.listed_count
        user_profile.description = twitter_user.description
        user_profile.protected = twitter_user.protected
        return user_profile

    @classmethod
    def bulk_create_and_save_users_from_api_reponse(cls, twitter_users):
        users_profiles = map(cls.create_user_profile_from_api_response,
                             twitter_users)
        [user_profile.save() for user_profile in users_profiles]

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        logger.info("Post Save: %s" % document.screen_name)

signals.post_save.connect(User.post_save, sender=User)
