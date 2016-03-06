#!/usr/bin/env python

"""wishlist.py

Models for the Wishlist ndb kind and protorpc message.

"""

from google.appengine.ext import ndb
from protorpc import messages


class Wishlist(ndb.Model):
    """Wishlist object"""
    sessionKeys = ndb.StringProperty(repeated=True)


class WishlistForm(messages.Message):
    """Wishlist message"""
    sessionKeys = messages.StringField(2, repeated=True)
