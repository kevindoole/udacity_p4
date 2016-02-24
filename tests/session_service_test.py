import datetime

import endpoints
from google.appengine.ext import ndb
from mock import MagicMock

from models.conference import Conference
from models.conference_session import ConferenceSessionForm, ConferenceSession
from models.profile import Profile
from models.speaker import Speaker
from services.session_service import SessionService
from service_test_case import ServiceTestCase
from services.speaker_service import SpeakerService
from utils import Auth


class TestSessionService(ServiceTestCase):
    def test_it_can_create_sessions(self):
        p_key = ndb.Key(Profile, 'kdoole@gmail.com')
        profile = Profile(mainEmail='kdoole@gmail.com', key=p_key).put()

        auth = Auth()
        auth.getUserId = MagicMock(return_value=unicode('kdoole@gmail.com'))

        conf_id = Conference(name="a conference",
                             organizerUserId='kdoole@gmail.com',
                             parent=p_key).put().urlsafe()
        request = ConferenceSessionForm(
            title='This is the title',
            date="2016-12-12",
            highlights="blah blah ha",
            startTime="13:15",
            websafeConferenceKey=conf_id,
            speakerEmails=['test@mail.com'],
            duration=12,
            typeOfSession='snails'
        )
        data = {field.name: getattr(request, field.name) for field in
                request.all_fields()}

        session_service = SessionService(auth=auth)
        session_service.create_session(request, profile)

        self.assertEqual(1, len(ConferenceSession.query().fetch(2)))

        session = ConferenceSession.query(
            ConferenceSession.websafeConferenceKey == conf_id).fetch()

        self.assertEquals(data['title'], session[0].title)
        self.assertEquals(data['highlights'], session[0].highlights)
        self.assertEquals(data['typeOfSession'], session[0].typeOfSession)
        self.assertEquals(data['duration'], session[0].duration)
        self.assertEquals(datetime.time(13, 15), session[0].startTime)
        self.assertEquals(datetime.date(2016, 12, 12), session[0].date)

        speaker = ndb.Key(urlsafe=session[0].speakerKeys[0]).get()
        self.assertEquals(speaker.email, 'test@mail.com')

    def test_only_owners_can_create_sessions(self):
        p_key = ndb.Key(Profile, 'kdoole@gmail.com')
        profile = Profile(mainEmail='kdoole@gmail.com', key=p_key).put()

        auth = Auth()
        auth.getUserId = MagicMock(
            return_value=unicode('not.an.owner@hacker.com'))

        conf_id = Conference(name="a conference",
                             organizerUserId='kdoole@gmail.com',
                             parent=p_key).put().urlsafe()
        request = ConferenceSessionForm(
            title='This is the title',
            date="2016-12-12",
            startTime="13:15",
            websafeConferenceKey=conf_id,
        )

        session_service = SessionService(auth=auth)
        self.assertRaises(
            endpoints.BadRequestException,
            session_service.create_session, request, profile)

    def test_it_can_get_conference_sessions_by_conference_id(self):
        session_service = SessionService()

        conf_id = Conference(name="a conference").put().urlsafe()
        ConferenceSession(
            title='This is the title',
            date=datetime.date(2016, 12, 12),
            highlights="blah blah ha",
            startTime=datetime.time(13, 15),
            websafeConferenceKey=conf_id,
            duration=12,
            typeOfSession='snails'
        ).put().urlsafe()
        ConferenceSession(
            title='This is the other title',
            date=datetime.date(2017, 12, 12),
            highlights="blah hahahaha blah ha",
            startTime=datetime.time(23, 32),
            websafeConferenceKey=conf_id,
            duration=1,
            typeOfSession='snails'
        ).put().urlsafe()

        sessions = session_service.get_conference_sessions(conf_id)
        self.assertEqual(2, len(sessions.items))

    def test_it_can_get_sessions_by_conf_id_and_type(self):
        session_service = SessionService()

        conf_id = Conference(name="a conference").put().urlsafe()
        ConferenceSession(
            title='This is the title',
            date=datetime.date(2016, 12, 12),
            highlights="blah blah ha",
            startTime=datetime.time(13, 15),
            websafeConferenceKey=conf_id,
            duration=12,
            typeOfSession='dance'
        ).put().urlsafe()
        ConferenceSession(
            title='This is the other title',
            date=datetime.date(2017, 12, 12),
            highlights="blah hahahaha blah ha",
            startTime=datetime.time(23, 32),
            websafeConferenceKey=conf_id,
            duration=1,
            typeOfSession='snails'
        ).put().urlsafe()

        sessions = session_service.get_conference_sessions_by_type(conf_id, 'dance')
        self.assertEqual(1, len(sessions.items))

    def test_it_can_find_speaker_sessions(self):
        # Make two sessions by the same speaker at 2 separate conferences.
        websafe_speaker_key = SpeakerService.find_or_create('test@mail.com')
        websafe_speaker_key_2 = SpeakerService.find_or_create('test2@mail2.com')
        conf_id = Conference(name="a conference").put().urlsafe()
        ConferenceSession(
            title='This is the title',
            date=datetime.date(2016, 12, 12),
            startTime=datetime.time(13, 15),
            websafeConferenceKey=conf_id,
            speakerKeys=[websafe_speaker_key, websafe_speaker_key_2]
        ).put().urlsafe()
        conf_id_2 = Conference(name="another conference").put().urlsafe()
        ConferenceSession(
            title='This is another title',
            date=datetime.date(2016, 12, 12),
            startTime=datetime.time(13, 15),
            websafeConferenceKey=conf_id_2,
            speakerKeys=[websafe_speaker_key]
        ).put().urlsafe()

        session_service = SessionService()
        sessions = session_service.get_speaker_sessions(websafe_speaker_key)
        self.assertEqual(2, len(sessions.items))

        sessions = session_service.get_speaker_sessions(websafe_speaker_key_2)
        self.assertEqual(1, len(sessions.items))