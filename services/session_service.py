from datetime import datetime

import endpoints
from google.appengine.ext import ndb

from models.conference_session import ConferenceSession, ConferenceSessionForms
from models.conference_session import ConferenceSessionForm
from services.base_service import BaseService
from services.speaker_service import SpeakerService
from support.Auth import Auth


class SessionService(BaseService):
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
        speaker_keys = entity.speakerKeys
        if speaker_keys is not None:
            speaker_emails = [ndb.Key(urlsafe=key).get().email for key in
                              speaker_keys]
            form.speakerEmails = speaker_emails

        form.websafeSessionKey = entity.key.urlsafe()

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

        del data['speakerEmails']
        # TODO: Enable speaker entities to be updated

        del data['websafeSessionKey']

        # convert dates from strings to Date objects;
        # set month based on start_date
        data['date'] = datetime.strptime(data['date'], "%Y-%m-%d").date()
        data['startTime'] = datetime.strptime(data['startTime'], "%H:%M").time()

        s_id = ConferenceSession.allocate_ids(size=1, parent=c_key)[0]
        s_key = ndb.Key(ConferenceSession, s_id, parent=c_key)
        data['key'] = s_key

        sess = ConferenceSession(**data).put()

        return sess.urlsafe()

    def check_owner(self, conf, user):
        owner_id = conf.organizerUserId
        user_id = self.auth.getUserId(user)
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
        sessions = ConferenceSession.query(ndb.AND(
            ConferenceSession.websafeConferenceKey == websafe_conference_key,
            ConferenceSession.typeOfSession == session_type)).fetch()

        return ConferenceSessionForms(
            items=[self.copy_entity_to_form(ConferenceSessionForm(), session)
                   for session in sessions])
