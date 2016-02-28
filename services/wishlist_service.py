from google.appengine.ext import ndb

from models.conference_session import ConferenceSessionForms, \
    ConferenceSessionForm
from models.models import ConflictException
from models.profile import Profile
from models.wishlist import Wishlist, WishlistForm
from services.base_service import BaseService
from services.session_service import SessionService
from support.Auth import Auth


class WishlistService(BaseService):
    def __init__(self, auth=None):
        self.auth = auth if auth is not None else Auth()

    def get_sessions_in_wishlist(self, user):
        wishlist_key = self.get_wishlist_key(user)
        session_keys = [ndb.Key(urlsafe=wsck) for wsck in
                        wishlist_key.get().sessionKeys]
        sessions = ndb.get_multi(session_keys)

        session_service = SessionService()
        return ConferenceSessionForms(
            items=[
                session_service.copy_entity_to_form(
                    ConferenceSessionForm(), session)
                for session in sessions])

    def get_wishlist_key(self, user):
        user_id = self.auth.getUserId(user)
        p_key = ndb.Key(Profile, user_id)

        wishlists = Wishlist.query(ancestor=p_key).fetch()
        if wishlists:
            return wishlists[0].key

        wl_id = Wishlist.allocate_ids(size=1, parent=p_key)[0]
        wl_k = ndb.Key(Wishlist, wl_id, parent=p_key)
        Wishlist(**{'key': wl_k}).put()

        return wl_k

    def add_session_to_wishlist(self, websafe_session_key, user):
        wl_key = self.get_wishlist_key(user)

        wishlist = wl_key.get()

        if websafe_session_key in wishlist.sessionKeys:
            raise ConflictException(
                "You already have this session in your wishlist.")

        wishlist.sessionKeys.append(websafe_session_key)
        wishlist.put()

        return self.to_message(wishlist)

    def remove_session_from_wishlist(self, websafe_session_key, user):
        wishlist = self.get_wishlist_key(user).get()
        if wishlist is None or wishlist.sessionKeys is []:
            raise ConflictException("This session is not in your wishlist.")

        if websafe_session_key not in wishlist.sessionKeys:
            raise ConflictException(
                "This session is not in your wishlist.")

        wishlist.sessionKeys.remove(websafe_session_key)
        wishlist.put()

        return self.to_message(wishlist)

    def to_message(self, wishlist):
        return WishlistForm(
            sessionKeys=wishlist.sessionKeys
        )
