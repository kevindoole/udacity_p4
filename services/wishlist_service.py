#!/usr/bin/env python

"""speaker_service.py

Handle requests related to Wishlists.
"""

from google.appengine.ext import ndb

from models.conference_session import ConferenceSessionForms, \
    ConferenceSessionForm, ConferenceSession
from models.models import ConflictException
from models.profile import Profile
from models.speaker import SpeakerForm, SpeakerForms
from models.wishlist import Wishlist, WishlistForm
from services.base_service import BaseService
from services.session_service import SessionService
from services.speaker_service import SpeakerService
from support.Auth import Auth


class WishlistService(BaseService):
    """Interface between the client and Wishlist Data Store."""

    def __init__(self, auth=None):
        self.speaker_service = SpeakerService()
        self.auth = auth if auth is not None else Auth()

    def get_sessions_in_wishlist(self, user):
        """Gets all the sessions in this user's wishlist.

        Args:
            user (endpoints.user)

        Returns:
             ConferenceSessionForms
        """
        sessions = self.wishlist_sessions(user)

        session_service = SessionService()
        return ConferenceSessionForms(
            items=[
                session_service.copy_entity_to_form(
                    ConferenceSessionForm(), session)
                for session in sessions])

    def wishlist_sessions(self, user):
        """Helper gets a list of sessions given a user."""
        wishlist_key = self.get_wishlist_key(user)
        session_keys = [ndb.Key(urlsafe=wsck) for wsck in
                        wishlist_key.get().sessionKeys]
        sessions = ndb.get_multi(session_keys)
        return sessions

    def get_wishlist_key(self, user):
        """Helper gets a wishlist key, given a user."""
        user_id = self.auth.get_user_id(user)
        p_key = ndb.Key(Profile, user_id)

        wishlists = Wishlist.query(ancestor=p_key).fetch()
        if wishlists:
            return wishlists[0].key

        wl_id = Wishlist.allocate_ids(size=1, parent=p_key)[0]
        wl_k = ndb.Key(Wishlist, wl_id, parent=p_key)
        Wishlist(**{'key': wl_k}).put()

        return wl_k

    def add_session_to_wishlist(self, websafe_session_key, user):
        """Adds a session to the user's wishlist.

        Args:
            websafe_session_key (string)
            user (endpoints.user)

        Returns:
             WishlistForm
        """
        wl_key = self.get_wishlist_key(user)

        wishlist = wl_key.get()

        if websafe_session_key in wishlist.sessionKeys:
            raise ConflictException(
                "You already have this session in your wishlist.")

        wishlist.sessionKeys.append(websafe_session_key)
        wishlist.put()

        return self.to_message(wishlist)

    def remove_session_from_wishlist(self, websafe_session_key, user):
        """Removes a session from the user's wishlist.

        Args:
            websafe_session_key (string)
            user (endpoints.user)

        Returns:
             WishlistForm
        """
        wishlist = self.get_wishlist_key(user).get()
        if wishlist is None or wishlist.sessionKeys is []:
            raise ConflictException("This session is not in your wishlist.")

        if websafe_session_key not in wishlist.sessionKeys:
            raise ConflictException(
                "This session is not in your wishlist.")

        wishlist.sessionKeys.remove(websafe_session_key)
        wishlist.put()

        return self.to_message(wishlist)

    def get_sessions_by_speaker_in_wishlist(self, user):
        """Gets a list of sessions by speakers referenced in user's wishlist.

        Args:
            user (endpoints.user)

        Returns:
             ConferenceSessionForms
        """
        sessions = self.wishlist_sessions(user)

        speaker_keys = []
        for s in sessions:
            sk = getattr(s, 'speakerKeys', [])
            speaker_keys += sk

        if not speaker_keys:
            return ConferenceSessionForms()

        sessions = ConferenceSession.query(
            ConferenceSession.speakerKeys.IN(speaker_keys)
        ).fetch()

        return ConferenceSessionForms(
            items=[self.copy_entity_to_form(ConferenceSessionForm(), s)
                   for s in sessions])

    def get_sessions_by_types_in_wishlist(self, user):
        """Gets a list of sessions with types referenced in user's wishlist.

        Args:
            user (endpoints.user)

        Returns:
             ConferenceSessionForms
        """
        sessions = self.wishlist_sessions(user)

        types = [getattr(s, 'typeOfSession') for s in sessions]

        sessions = ConferenceSession.query(
            ConferenceSession.typeOfSession.IN(types)
        ).fetch()

        return ConferenceSessionForms(
            items=[self.copy_entity_to_form(ConferenceSessionForm(), s)
                   for s in sessions])

    def to_message(self, wishlist):
        """Helper takes a wishlist entity and returns a message.

        Args:
            wishlist (Wishlist)

        Returns:
            WishlistForm
        """
        return WishlistForm(
            sessionKeys=wishlist.sessionKeys
        )
