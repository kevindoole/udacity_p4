#!/usr/bin/env python

"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21
wesc+api@google.com (Wesley Chun)

"""

import endpoints
from google.appengine.api import memcache
from google.appengine.ext import ndb
from protorpc import messages, message_types, remote

from models.conference import Conference, ConferenceForm, ConferenceForms, \
    ConferenceQueryForms
from models.conference_session import ConferenceSessionForms, \
    ConferenceSessionForm, ConferenceSessionQueryForms
from models.models import ConflictException, StringMessage, BooleanMessage
from models.profile import Profile, ProfileMiniForm, ProfileForm, TeeShirtSize
from models.speaker import SpeakerForms
from models.wishlist import WishlistForm
from services.conference_service import ConferenceService
from services.profile_service import ProfileService
from services.session_service import SessionService
from services.speaker_service import SpeakerService
from services.wishlist_service import WishlistService
from settings import WEB_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID, \
    ANDROID_AUDIENCE
from support.AppliesFilters import AppliesFilters
from support.Auth import Auth

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID
MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT_ANNOUNCEMENTS"
ANNOUNCEMENT_TPL = ('Last chance to attend! The following conferences '
                    'are nearly sold out: %s')
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

DEFAULTS = {"city": "Default City", "maxAttendees": 0, "seatsAvailable": 0,
            "topics": ["Default", "Topic"]}

CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1, required=True)
)

CONF_SESSION_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1, required=True),
    sessionType=messages.StringField(2)
)

CONF_POST_REQUEST = endpoints.ResourceContainer(
    ConferenceForm,
    websafeConferenceKey=messages.StringField(1, required=True)
)

CONF_SPEAKER_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSpeakerKey=messages.StringField(1, required=True)
)

WISHLIST_POST_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey=messages.StringField(1, required=True)
)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


@endpoints.api(name='conference', version='v1', audiences=[ANDROID_AUDIENCE],
               allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID,
                                   ANDROID_CLIENT_ID, IOS_CLIENT_ID],
               scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""

    def __init__(self):
        self.session_service = SessionService()
        self.speaker_service = SpeakerService()
        self.conference_service = ConferenceService()
        self.wishlist_service = WishlistService()
        self.profile_service = ProfileService()
        self.auth = Auth()

    # - - - Conference objects - - - - - - - - - - - - - - - - -

    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
                      http_method='POST', name='createConference')
    def create_conference(self, request):
        """Create new conference."""
        return self.conference_service.create_conference_object(request)

    @endpoints.method(CONF_POST_REQUEST, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='PUT', name='updateConference')
    def update_conference(self, request):
        """Update conference w/provided fields & return w/updated info."""
        return self.conference_service.update_conference_object(request)

    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='GET', name='getConference')
    def get_conference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)
        prof = conf.key.parent().get()
        # return ConferenceForm
        return self.conference_service.copy_conference_to_form(ConferenceForm(),
                                                               conf,
                                                               prof.displayName)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='get-conferences-created', http_method='POST',
                      name='getConferencesCreated')
    def get_conferences_created(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = self.auth.getUserId(user)

        # create ancestor query for all key matches for this user
        confs = Conference.query(ancestor=ndb.Key(Profile, user_id))
        prof = ndb.Key(Profile, user_id).get()
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(items=[
            self.conference_service.copy_conference_to_form(ConferenceForm(),
                                                            conf,
                                                            prof.displayName)
            for conf in confs])

    @endpoints.method(ConferenceQueryForms, ConferenceForms,
                      path='query-conferences', http_method='POST',
                      name='queryConferences')
    def query_conferences(self, request):
        """Query for conferences."""
        filter_maker = AppliesFilters(
            Conference,
            {'int': ["month", "maxAttendees"]},
            {'CITY': 'city', 'TOPIC': 'topics',
             'MONTH': 'month',
             'MAX_ATTENDEES': 'maxAttendees'})
        conferences = filter_maker.get_query(request.filters)

        # need to fetch organiser displayName from profiles
        # get all keys and use get_multi for speed
        organisers = [(ndb.Key(Profile, conf.organizerUserId)) for conf in
                      conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return individual ConferenceForm object per Conference
        return ConferenceForms(items=[
            self.conference_service.copy_conference_to_form(
                ConferenceForm(), conf, names[conf.organizerUserId]
            ) for conf in conferences])

    # - - - Profile objects - - - - - - - - - - - - - - - - - - -

    @endpoints.method(message_types.VoidMessage, ProfileForm, path='profile',
                      http_method='GET', name='getProfile')
    def get_profile(self, request):
        """Return user profile."""
        return self.profile_service.do_profile()

    @endpoints.method(ProfileMiniForm, ProfileForm, path='profile',
                      http_method='POST', name='saveProfile')
    def save_profile(self, request):
        """Update & return user profile."""
        return self.profile_service.do_profile(request)

    # - - - Announcements - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def cache_announcement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(Conference.seatsAvailable <= 5,
                                         Conference.seatsAvailable > 0)).fetch(
            projection=[Conference.name])

        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = ANNOUNCEMENT_TPL % (
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

        return announcement

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='conference/announcement/get', http_method='GET',
                      name='getAnnouncement')
    def get_announcement(self, request):
        """Return Announcement from memcache."""
        return StringMessage(
            data=memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY) or "")

    # - - - Registration - - - - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    def conference_registration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        prof = self.profile_service.get_profile_from_user()  # get user Profile

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException("There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='conferences/attending', http_method='GET',
                      name='getConferencesToAttend')
    def get_conferences_to_attend(self, request):
        """Get list of conferences that user has registered for."""
        prof = self.profile_service.get_profile_from_user()  # get user Profile
        conf_keys = [ndb.Key(urlsafe=wsck) for wsck in
                     prof.conferenceKeysToAttend]
        conferences = ndb.get_multi(conf_keys)

        # get organizers
        organisers = [ndb.Key(Profile, conf.organizerUserId) for conf in
                      conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(items=[
            self.conference_service.copy_conference_to_form(
                ConferenceForm(), conf, names[conf.organizerUserId]
            ) for conf in conferences])

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='POST', name='registerForConference')
    def register_for_conference(self, request):
        """Register user for selected conference."""
        return self.conference_registration(request)

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='DELETE', name='unregisterFromConference')
    def unregister_from_conference(self, request):
        """Unregister user for selected conference."""
        return self.conference_registration(request, reg=False)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='filterPlayground', http_method='GET',
                      name='filterPlayground')
    def filter_playground(self, request):
        """Filter Playground"""
        q = Conference.query()
        # field = "city"
        # operator = "="
        # value = "London"
        # f = ndb.query.FilterNode(field, operator, value)
        # q = q.filter(f)
        q = q.filter(Conference.city == "London")
        q = q.filter(Conference.topics == "Medical Innovations")
        q = q.filter(Conference.month == 6)

        return ConferenceForms(items=[
            self.conference_service.copy_conference_to_form(
                ConferenceForm(), conf, "") for conf in q])

    # - - - Conference sessions  - - - - - - - - - - - - - - - - -
    @endpoints.method(ConferenceSessionForm, ConferenceSessionForm,
                      path='session', http_method='POST',
                      name='createConferenceSession')
    def create_conference_session(self, request):
        """Create new conference session."""
        user = endpoints.get_current_user()

        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        self.session_service.create_conference_session(request, user)
        return request

    @endpoints.method(CONF_GET_REQUEST, ConferenceSessionForms,
                      path='conference/{websafeConferenceKey}/sessions',
                      http_method='GET', name='getConferenceSessions')
    def get_conference_sessions(self, request):
        return self.session_service.get_conference_sessions(
            request.websafeConferenceKey)

    @endpoints.method(CONF_SPEAKER_GET_REQUEST, ConferenceSessionForms,
                      path='speaker/{websafeSpeakerKey}/sessions',
                      http_method='GET', name='getSpeakerSessions')
    def get_speaker_sessions(self, request):
        return self.session_service.get_speaker_sessions(
            request.websafeSpeakerKey)

    @endpoints.method(CONF_SESSION_GET_REQUEST, ConferenceSessionForms,
                      path='conference/{websafeConferenceKey}/sessions/{'
                           'sessionType}', http_method='GET',
                      name='getSessionsByType')
    def get_sessions_by_type(self, request):
        return self.session_service.get_conference_sessions_by_type(
            request.websafeConferenceKey, request.sessionType)

    @endpoints.method(ConferenceSessionQueryForms, ConferenceSessionForms,
                      path='query-sessions', http_method='POST',
                      name='getSessionsByTypeAndFilters')
    def get_sessions_by_type_and_filters(self, request):
        return self.session_service.get_sessions_by_type_and_filters(
            request.websafeConferenceKey,
            request.typeOfSession, request.filters)

    @endpoints.method(message_types.VoidMessage, SpeakerForms, path='speakers',
                      http_method='GET', name='getSpeakers')
    def get_speakers(self, request):
        """Return a list of all speakers."""
        return self.speaker_service.get_speakers()

    @endpoints.method(WISHLIST_POST_REQUEST, WishlistForm, path='wishlist',
                      http_method='POST', name='addToMyWishlist')
    def add_session_to_wishlist(self, request):
        """Return a list of all speakers."""
        return self.wishlist_service.add_session_to_wishlist(
            request.websafeSessionKey, endpoints.get_current_user())

    @endpoints.method(WISHLIST_POST_REQUEST, WishlistForm, path='wishlist',
                      http_method='DELETE', name='removeFromMyWishlist')
    def remove_session_from_wishlist(self, request):
        """Return a list of all speakers."""
        return self.wishlist_service.remove_session_from_wishlist(
            request.websafeSessionKey, endpoints.get_current_user())

    @endpoints.method(message_types.VoidMessage, ConferenceSessionForms,
                      path='wishlist', http_method='GET',
                      name='getSessionsInWishlist')
    def get_sessions_in_wishlist(self, request):
        user = endpoints.get_current_user()
        return self.wishlist_service.get_sessions_in_wishlist(user)

    @endpoints.method(message_types.VoidMessage, ConferenceSessionForms,
                      path='wishlist/sessions-by-wishlist-speakers',
                      http_method='GET',
                      name='getSessionsByWishlistSpeakers')
    def get_sessions_by_speakers_in_wishlist(self, request):
        user = endpoints.get_current_user()
        return self.wishlist_service.get_sessions_by_speaker_in_wishlist(
            user)

    @endpoints.method(message_types.VoidMessage, ConferenceSessionForms,
                      path='wishlist/sessions-by-wishlist-types',
                      http_method='GET',
                      name='getSessionsByWishlistTypes')
    def get_sessions_by_types_in_wishlist(self, request):
        user = endpoints.get_current_user()
        return self.wishlist_service.get_sessions_by_types_in_wishlist(
            user)


api = endpoints.api_server([ConferenceApi])  # register API
