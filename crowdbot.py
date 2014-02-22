# coding=utf-8

from tweepy import OAuthHandler, API
from tweepy.utils import import_simplejson, parse_datetime
from tweepy.models import Model
import argparse
import os
import itertools
import datetime, time
from django.core.management import setup_environ
import nearbysources.settings as settings
import sys, json

if __name__ == "__main__":
    setup_environ(settings)

from nearbysources.questions.models import *

DEBUG = True
METRES = 0.000009

questionnaire = Questionnaire.objects.get(name=sys.argv[1])
tweet = QuestionnaireTweet.objects.get(questionnaire=questionnaire, language=Language.objects.get(code="en")).text

betriebe = []
for loi in LocationOfInterest.objects.filter(campaign=questionnaire.campaign):
    betriebe.append({"name": loi.name, "geometry": {"coordinates": [loi.lng, loi.lat]}, "id": loi.id, "loi": loi})

def twitter_request_already_exists(handle, questionnaire, location=None):
    try:
        if location:
            TwitterRequest.objects.get(handle=handle, questionnaire=questionnaire, location=location)
        else:
            TwitterRequest.objects.get(handle=handle, questionnaire=questionnaire)
        return True
    except:
        return False

if __name__ == '__main__':
    consumer_key = os.environ["CONSUMER_KEY"]
    consumer_secret = os.environ["CONSUMER_SECRET"]

    access_token = os.environ["ACCESS_TOKEN"]
    access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = API(auth)
