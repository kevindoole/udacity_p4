from protorpc import messages
from google.appengine.ext import ndb


class Speaker(ndb.Model):
    """Speaker -- Speaker object"""
    name = ndb.StringProperty()
    email = ndb.StringProperty(required=True)


class SpeakerForm(messages.Message):
    name = messages.StringField(1)
    email = messages.StringField(2, required=True)
