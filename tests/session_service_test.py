import datetime

import endpoints
from google.appengine.ext import ndb

from models.conference import Conference
from models.conference_session import ConferenceSessionForm, ConferenceSession
from models.profile import Profile
from service_test_case import ServiceTestCase
from services.session_service import SessionService
from services.speaker_service import SpeakerService


class TestSessionService(ServiceTestCase):
    def test_it_can_create_sessions(self):
        p_key = ndb.Key(Profile, 'kdoole@gmail.com')
        profile = Profile(mainEmail='kdoole@gmail.com', key=p_key).put()

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

        auth = self.mock_auth('kdoole@gmail.com')
        session_service = SessionService(auth=auth)
        session_service.create_conference_session(request, profile)

        self.assertEqual(1, len(ConferenceSession.query().fetch(2)))

        session = ConferenceSession.query(
            ConferenceSession.websafeConferenceKey == conf_id).fetch()

        self.assertEquals(data['title'], session[0].title)
        self.assertEquals(data['highlights'], session[0].highlights)
        self.assertEquals(data['typeOfSession'], session[0].typeOfSession)
        self.assertEquals(data['duration'], session[0].duration)
        self.assertEquals(datetime.datetime(2016, 12, 12, 13, 15),
                          session[0].dateTime)

        speaker = ndb.Key(urlsafe=session[0].speakerKeys[0]).get()
        self.assertEquals(speaker.email, 'test@mail.com')

    def test_only_owners_can_create_sessions(self):
        auth = self.mock_auth('not.an.owner@hacker.com')

        conf_id, profile = self.make_conference(conf_name='a conference',
                                                email='kdoole@gmail.com')
        request = ConferenceSessionForm(
            title='This is the title',
            date="2016-12-12",
            startTime="13:15",
            websafeConferenceKey=conf_id,
        )

        session_service = SessionService(auth=auth)
        self.assertRaises(
            endpoints.BadRequestException,
            session_service.create_conference_session, request, profile)

    def test_it_can_get_conference_sessions_by_conference_id(self):
        session_service = SessionService()

        conf_id = Conference(name="a conference").put().urlsafe()
        ConferenceSession(
            title='This is the title',
            dateTime=datetime.datetime(2016, 12, 12, 13, 15),
            highlights="blah blah ha",
            websafeConferenceKey=conf_id,
            duration=12,
            typeOfSession='snails'
        ).put().urlsafe()
        ConferenceSession(
            title='This is the other title',
            dateTime=datetime.datetime(2017, 12, 12, 23, 32),
            highlights="blah hahahaha blah ha",
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
            dateTime=datetime.datetime(2016, 12, 12, 13, 15),
            highlights="blah blah ha",
            websafeConferenceKey=conf_id,
            duration=12,
            typeOfSession='dance'
        ).put().urlsafe()
        ConferenceSession(
            title='This is the other title',
            dateTime=datetime.datetime(2017, 12, 12, 23, 32),
            highlights="blah hahahaha blah ha",
            websafeConferenceKey=conf_id,
            duration=1,
            typeOfSession='snails'
        ).put().urlsafe()

        sessions = session_service.get_conference_sessions_by_type(conf_id,
                                                                   'dance')
        self.assertEqual(1, len(sessions.items))

    def test_it_can_find_speaker_sessions(self):
        # Make two sessions by the same speaker at 2 separate conferences.
        websafe_speaker_key = SpeakerService.find_or_create('test@mail.com')
        websafe_speaker_key_2 = SpeakerService.find_or_create('test2@mail2.com')
        conf_id = Conference(name="a conference").put().urlsafe()
        ConferenceSession(
            title='This is the title',
            dateTime=datetime.datetime(2016, 12, 12, 13, 15),
            websafeConferenceKey=conf_id,
            speakerKeys=[websafe_speaker_key, websafe_speaker_key_2]
        ).put().urlsafe()
        conf_id_2 = Conference(name="another conference").put().urlsafe()
        ConferenceSession(
            title='This is another title',
            dateTime=datetime.datetime(2016, 12, 12, 13, 15),
            websafeConferenceKey=conf_id_2,
            speakerKeys=[websafe_speaker_key]
        ).put().urlsafe()

        session_service = SessionService()
        sessions = session_service.get_speaker_sessions(websafe_speaker_key)
        self.assertEqual(2, len(sessions.items))

        sessions = session_service.get_speaker_sessions(websafe_speaker_key_2)
        self.assertEqual(1, len(sessions.items))
