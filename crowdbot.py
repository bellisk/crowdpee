# coding=utf-8
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, Stream, API
from tweepy.utils import import_simplejson, parse_datetime
from tweepy.models import Model
json = import_simplejson()
import argparse
import os
import sys
import itertools
import datetime

class Event(Model):
    @classmethod
    def parse(cls, api, json):
        event = cls(api)
        for k, v in json.items():
            if k == 'target':
                user_model = getattr(api.parser.model_factory, 'user')
                user = user_model.parse(api, v)
                setattr(event, 'target', user)
            elif k == 'source':
                user_model = getattr(api.parser.model_factory, 'user')
                user = user_model.parse(api, v)
                setattr(event, 'source', user)
            elif k == 'created_at':
                setattr(event, k, parse_datetime(v))
            elif k == 'target_object':
                setattr(event, 'target_object', v)
            elif k == 'event':
                setattr(event, 'event', v)
            else:
                setattr(event, k, v)
        return event

class LessListener(StreamListener):
    TIMEOUT = datetime.timedelta(seconds=120)

    def __init__(self, api):
        StreamListener.__init__(self, api)
        self.last = datetime.datetime.now() - self.TIMEOUT
        self.me = self.api.me()

    def on_connect(self):
        me = self.me
        print "streaming as @%s (#%d)" % (me.screen_name, me.id)

    def on_status(self, status):
        print status.text

if __name__ == '__main__':
    consumer_key = os.environ["CONSUMER_KEY"]
    consumer_secret = os.environ["CONSUMER_SECRET"]

    access_token = os.environ["ACCESS_TOKEN"]
    access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = API(auth)
    l = LessListener(api)

    stream = Stream(auth, l)
    stream.filter(track=['less'])