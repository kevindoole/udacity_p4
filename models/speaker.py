#!/usr/bin/env python

"""speaker.py

Models for the Speaker ndb kind and protorpc messages.

"""

from protorpc import messages
from google.appengine.ext import ndb


class Speaker(ndb.Model):
    """Speaker object"""
    name = ndb.StringProperty()
    email = ndb.StringProperty(required=True)


class SpeakerForm(messages.Message):
    """SpeakerForm inbound form message"""
    name = messages.StringField(1)
    email = messages.StringField(2, required=True)
    websafeKey = messages.StringField(3)


class SpeakerForms(messages.Message):
    """Multiple SpeakerForm inbound form message"""
    items = messages.MessageField(SpeakerForm, 1, repeated=True)
