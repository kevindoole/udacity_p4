#!/usr/bin/env python

"""profile_service.py

Handle requests related to ConferenceSessions.
"""

from datetime import datetime

import endpoints
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models.conference_session import ConferenceSession, ConferenceSessionForms
from models.conference_session import ConferenceSessionForm
from services.base_service import BaseService
from services.speaker_service import SpeakerService
from support.AppliesFilters import AppliesFilters
from support.Auth import Auth


class SessionService(BaseService):
    """Interface between the client and ConferenceSession Data Store."""

    def __init__(self, auth=None):
        self.auth = auth if auth is not None else Auth()

    def copy_entity_to_form(self, form, entity):
        """Copies a Session entity to a SessionForm.

        Args:
            form (SessionForm)
            entity (Session)

        Returns:
             SessionForm
        """
        speaker_keys = getattr(entity, 'speakerKeys', None)
        if speaker_keys is not None:
            speaker_emails = [ndb.Key(urlsafe=key).get().email for key in
                              speaker_keys]
            form.speakerEmails = speaker_emails

        form.websafeSessionKey = entity.key.urlsafe()

        date, time = str(entity.dateTime.date()), str(entity.dateTime.time())
        form.date = date
        form.startTime = time

        return super(SessionService, self).copy_entity_to_form(form, entity)

    def create_conference_session(self, request, user):
        """Create or update Session object, returning SessionForm/request.

        Args:
            request (ConferenceSessionForm)
            user (User)

        Returns:
            string

        Raises:
            endpoints.BadRequestException
        """

        if not request.title:
            raise endpoints.BadRequestException(
                "Session 'title' field required")

        if not request.startTime:
            raise endpoints.BadRequestException("Session 'startTime' field "
                                                "required")

        if not request.date:
            raise endpoints.BadRequestException("Session 'date' field required")

        c_key = ndb.Key(urlsafe=request.websafeConferenceKey)
        conf = c_key.get()

        # TODO: This should be in the client
        self.check_owner(conf, user)

        data = {field.name: getattr(request, field.name) for field in
                request.all_fields()}

        if request.speakerEmails:
            data['speakerKeys'] = [SpeakerService.find_or_create(email) for
                                   email in request.speakerEmails]
            taskqueue.add(
                params={'speakers': '|||'.join(data['speakerKeys']),
                        'websafe_conference_key': request.websafeConferenceKey},
                url='/tasks/cache_featured_speaker')

        del data['speakerEmails']
        # TODO: Enable speaker entities to be updated

        del data['websafeSessionKey']

        # convert dates from strings to Date objects;
        # set month based on start_date
        data['dateTime'] = datetime.strptime(
            data['date'] + ' ' + data['startTime'], "%Y-%m-%d %H:%M")
        data['hour'] = data['dateTime'].hour

        del data['date']
        del data['startTime']

        s_id = ConferenceSession.allocate_ids(size=1, parent=c_key)[0]
        s_key = ndb.Key(ConferenceSession, s_id, parent=c_key)
        data['key'] = s_key

        sess = ConferenceSession(**data).put()

        return sess.urlsafe()

    def check_owner(self, conf, user):
        """Checks the owner of a conference.

        Args:
            conf (Conference)
            user (endpoints.user)

        Raises:
            endpoints.BadRequestException
        """
        owner_id = conf.organizerUserId
        user_id = self.auth.get_user_id(user)
        if user_id != owner_id:
            raise endpoints.BadRequestException("You must be the conference "
                                                "organizer to add sessions")

    def get_conference_sessions(self, websafe_conference_key):
        """Gets all the sessions associated with a conference.

        Args:
            websafe_conference_key (string)
        Returns:
            ConferenceSessionForms
        """
        sessions = ConferenceSession.query(
            ConferenceSession.websafeConferenceKey ==
            websafe_conference_key).fetch()

        return ConferenceSessionForms(
            items=[self.copy_entity_to_form(ConferenceSessionForm(), session)
                   for session in sessions])

    def get_speaker_sessions(self, websafe_speaker_key):
        """Gets a list of sessions featuring this speaker.

        Args:
             websafe_speaker_key (string)

        Returns:
            ConferenceSessionForms
        """
        sessions = ConferenceSession.query(
            ConferenceSession.speakerKeys == websafe_speaker_key).fetch()

        return ConferenceSessionForms(
            items=[self.copy_entity_to_form(ConferenceSessionForm(), session)
                   for session in sessions])

    def get_conference_sessions_by_type(self, websafe_conference_key,
                                        session_type):
        """Gets a list of sessions in a conference with a specific type.

        Args:
             websafe_conference_key (string)

        Returns:
            ConferenceSessionForms
        """
        sessions = ConferenceSession.query(ndb.AND(
            ConferenceSession.websafeConferenceKey == websafe_conference_key,
            ConferenceSession.typeOfSession == session_type)).fetch()

        return ConferenceSessionForms(
            items=[self.copy_entity_to_form(ConferenceSessionForm(), session)
                   for session in sessions])

    def get_sessions_by_type_and_filters(self, websafe_conference_key,
                                         session_type, filters):
        """Gets a list of sessions with a specific type and arbitrary filters.

        Args:
             websafe_conference_key (string)
             session_type (string)
             filters (list)

        Returns:
            ConferenceSessionForms
        """
        if filters:
            filter_maker = AppliesFilters(
                ConferenceSession,
                {'datetime': ['dateTime'],
                 'int': ['duration', 'hour']},
                {'TITLE': 'title',
                 'DURATION': 'duration',
                 'DATE': 'dateTime',
                 'HOUR': 'hour'})
            sessions = filter_maker.get_query(
                filters, 'title', websafe_conference_key).fetch()
        else:
            sessions = ConferenceSession.query(
                ConferenceSession.websafeConferenceKey == websafe_conference_key
            ).fetch()

        return ConferenceSessionForms(
            items=[self.copy_entity_to_form(ConferenceSessionForm(), s)
                   for s in sessions if
                   s.typeOfSession == unicode(session_type)])
