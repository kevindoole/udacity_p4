import random

import webapp2
from google.appengine.api import memcache
from google.appengine.ext import ndb

from models.conference_session import ConferenceSession

MEMCACHE_FEATURED_SPEAKER_KEY = "FEATURED_SPEAKER"


class FeaturesSpeakers(webapp2.RequestHandler):
    def post(self):
        keys = self.request.get('speakers').split('|||')

        c_key = ndb.Key(urlsafe=self.request.get('websafe_conference_key'))

        featured_speakers = []

        # Check for multiple keys in speakerKeys
        for key in keys:
            sessions = ConferenceSession.query(
                ConferenceSession.speakerKeys == key, ancestor=c_key).fetch()

            if len(sessions) > 1:
                featured_speakers.append(key)

        if not featured_speakers:
            return

        featured_key = random.choice(featured_speakers)

        memcache.set(MEMCACHE_FEATURED_SPEAKER_KEY, featured_key)
