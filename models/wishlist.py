from google.appengine.ext import ndb
from protorpc import messages


class Wishlist(ndb.Model):
    """Wishlist -- Wishlist object"""
    sessionKeys = ndb.StringProperty(repeated=True)


class WishlistForm(messages.Message):
    """Wishlist message"""
    sessionKeys = messages.StringField(2, repeated=True)
