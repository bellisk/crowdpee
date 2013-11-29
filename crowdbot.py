# coding=utf-8
DEBUG = True
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, Stream, API
from tweepy.utils import import_simplejson, parse_datetime
from tweepy.models import Model
import_simplejson()
import argparse
import os
import itertools
import datetime
from django.core.management import setup_environ
import nearbysources.settings as settings
import sys, json

if __name__ == "__main__":
    setup_environ(settings)

from nearbysources.questions.models import *

questionnaire = Questionnaire.objects.get(name=sys.argv[1])
tweet = QuestionnaireTweet.objects.get(questionnaire=questionnaire, language=Language.objects.get(code="en")).text

betriebe = []
for loi in LocationOfInterest.objects.filter(campaign=questionnaire.campaign):
    betriebe.append({"name": loi.name, "geometry": {"coordinates": [loi.lng, loi.lat]}, "id": loi.id, "loi": loi})

#with open("gwb.json", 'r') as f:
#    betriebe = json.load(f)['features']

def closest(lng, lat):
    return sorted(betriebe, key=lambda b: (b['geometry']['coordinates'][0] - lng) * (b['geometry']['coordinates'][0] - lng) + (b['geometry']['coordinates'][1] - lat) * (b['geometry']['coordinates'][1] - lat))[0]

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

def twitter_request_already_exists(handle, questionnaire):
    try:
        TwitterRequest.objects.get(handle=handle, questionnaire=questionnaire) # removed location so only tweeting each *user* once
        return True
    except:
        return False

class LessListener(StreamListener):
    TIMEOUT = datetime.timedelta(seconds=300)

    def __init__(self, api):
        StreamListener.__init__(self, api)
        self.last = datetime.datetime.now() - self.TIMEOUT
        self.me = self.api.me()

    def on_connect(self):
        me = self.me
        print ("streaming as @%s (#%d)" % (me.screen_name, me.id)).encode('utf-8')
        #self.api.update_status("Running live now.")

    def on_status(self, status):
        if status.coordinates:
            # if not following user, request to follow user
            lng, lat = status.coordinates['coordinates']
            b = closest(lng, lat)
            dist = ((b['geometry']['coordinates'][0] - lng) * (b['geometry']['coordinates'][0] - lng) + (b['geometry']['coordinates'][1] - lat) * (b['geometry']['coordinates'][1] - lat)) ** 0.5
            friendships = self.api.show_friendship(source_screen_name=self.me.screen_name, target_screen_name=status.author.screen_name)
            if dist <= 0.09 and not DEBUG and not friendships[0].following:
                self.api.create_friendship(screen_name=status.author.screen_name)
                print "Requested to follow " + status.author.screen_name
            if dist <= 0.0009:
                response = "@" + status.author.screen_name + " " + tweet.replace("{{url}}", "http://nearbysources.com/q/" + str(questionnaire.id) + "/" + str(b["id"]) + "/en")
                # if following user, send response
                if not DEBUG and not twitter_request_already_exists(handle=status.author.screen_name, questionnaire=questionnaire) and friendships[0].following:
                    self.api.update_status(response, in_reply_to_status=status.id)
                    TwitterRequest(handle=status.author.screen_name, questionnaire=questionnaire, location=b["loi"]).save()
                    print response.encode('utf-8')
            print status.text.encode('utf-8')
            print status.coordinates['coordinates']
            print b['name'].encode('utf-8')
            print dist
            print
            print

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
    # CH: [5.47, 45.37, 10.65, 47.96]
    stream.filter(locations=[8.41, 47.31, 8.62, 47.48])
