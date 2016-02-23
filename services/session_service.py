from datetime import datetime

import endpoints
from google.appengine.ext import ndb

from models.conference_session import ConferenceSession, ConferenceSessionForms, \
    ConferenceSessionForm
from models.profile import Profile
from services.speaker_service import SpeakerService
from services.base_service import BaseService
from utils import Auth


class SessionService(BaseService):
    def __init__(self, auth=None):
        self.auth = auth if auth is not None else Auth()

    def create_session(self, request, user):
        """Create or update Session object, returning SessionForm/request."""

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

        owner_id = conf.organizerUserId
        user_id = self.auth.getUserId(user)
        if user_id != owner_id:
            raise endpoints.BadRequestException("You must be the conference "
                                                "organizer to add sessions")

        # copy SessionForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}

        if request.speakerEmails:
            data['speakerKeys'] = [
                SpeakerService.find_or_create(email)
                for email in request.speakerEmails]

        del data['speakerEmails']
        # TODO: Enable speaker entities to be updated

        # convert dates from strings to Date objects;
        # set month based on start_date
        data['date'] = datetime.strptime(data['date'], "%Y-%m-%d").date()
        data['startTime'] = datetime.strptime(data['startTime'], "%H:%M").time()

        s_id = ConferenceSession.allocate_ids(size=1, parent=c_key)[0]
        s_key = ndb.Key(ConferenceSession, s_id, parent=c_key)
        data['key'] = s_key

        # create ConferenceSession
        ConferenceSession(**data).put()

        return request

    def get_conference_sessions(self, websafeConferenceKey):
        sessions = ConferenceSession.query(
            ConferenceSession.websafeConferenceKey == websafeConferenceKey).fetch()

        return ConferenceSessionForms(
            items=[self.copy_entity_to_form(
                ConferenceSessionForm(), session) for session in sessions])
