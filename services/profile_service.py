#!/usr/bin/env python

"""profile_service.py

Handle requests related to Profiles.
"""

import endpoints
from google.appengine.ext import ndb

from models.profile import Profile, TeeShirtSize, ProfileForm
from services.base_service import BaseService
from support.Auth import Auth


class ProfileService(BaseService):
    """Interface between the client and Profile Data Store."""

    def __init__(self):
        self.auth = Auth()

    def copy_profile_to_form(self, profile_form, profile):
        """Copies a Profile entity to a ProfileForm.

        Args:
            form (ProfileForm)
            entity (Profile)

        Returns:
             ProfileForm
        """
        tee_shirt_size = str(getattr(TeeShirtSize, profile.teeShirtSize))
        if tee_shirt_size is not None:
            profile_form.teeShirtSize = getattr(TeeShirtSize, tee_shirt_size)

        return super(ProfileService, self).copy_entity_to_form(
            profile_form, profile)

    def get_profile_from_user(self):
        """Return user Profile from datastore, creating new one if
        non-existent."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get Profile from datastore
        user_id = self.auth.get_user_id(user)
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        # create new Profile if not there
        if not profile:
            profile = Profile(key=p_key, displayName=user.nickname(),
                              mainEmail=user.email(),
                              teeShirtSize=str(TeeShirtSize.NOT_SPECIFIED), )
            profile.put()

        return profile  # return Profile

    def do_profile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self.get_profile_from_user()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
                        # if field == 'teeShirtSize':
                        #    setattr(prof, field, str(val).upper())
                        # else:
                        #    setattr(prof, field, val)
                        prof.put()

        # return ProfileForm
        return self.copy_profile_to_form(ProfileForm(), prof)
