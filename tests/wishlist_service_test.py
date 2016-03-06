from google.appengine.api import users

from models.conference_session import ConferenceSessionForm
from service_test_case import ServiceTestCase
from services.session_service import SessionService
from services.speaker_service import SpeakerService
from services.wishlist_service import WishlistService


class TestWishlistService(ServiceTestCase):
    def test_it_gets_a_users_wishlist(self):
        wishlist_service = WishlistService()
        self.loginUser('test@example.com')
        user = users.get_current_user()
        wishlist = wishlist_service.get_wishlist_key(user).get()
        self.assertIsNotNone(wishlist)
        should_be_same_wishlist = wishlist_service.get_wishlist_key(user).get()
        self.assertEqual(wishlist, should_be_same_wishlist)

    def test_it_saves_and_removes_sessions_to_the_wishlist(self):
        user, websafe_session_key = self.make_conference_and_session()

        wishlist_service = WishlistService()
        wishlist_service.add_session_to_wishlist(websafe_session_key, user)
        wishlist = wishlist_service.get_wishlist_key(user).get()

        self.assertIn(websafe_session_key, wishlist.sessionKeys)

        wishlist_service.remove_session_from_wishlist(websafe_session_key, user)
        wishlist = wishlist_service.get_wishlist_key(user).get()

        self.assertNotIn(websafe_session_key, wishlist.sessionKeys)

    def test_it_lists_sessions_in_wishlist(self):
        user, websafe_session_key = self.make_conference_and_session()

        wishlist_service = WishlistService()
        wishlist_service.add_session_to_wishlist(websafe_session_key, user)

        sessions = wishlist_service.get_sessions_in_wishlist(user)
        self.assertEquals('This is the title', sessions.items[0].title)

    def test_it_gets_speakers_from_wishlist(self):
        user, websafe_session_key = self.make_conference_and_session()

        wishlist_service = WishlistService()
        wishlist_service.add_session_to_wishlist(websafe_session_key, user)

        sessions = wishlist_service.get_sessions_by_speaker_in_wishlist(user)
        session = sessions.items[0]

        data = data = {field.name: getattr(session, field.name) for field in
                       session.all_fields()}

        self.assertEqual(1, len(sessions.items))
        self.assertEquals('This is the title', data['title'])

    def test_it_gets_types_from_wishlist(self):
        user, websafe_session_key = self.make_conference_and_session()

        wishlist_service = WishlistService()
        wishlist_service.add_session_to_wishlist(websafe_session_key, user)

        sessions = wishlist_service.get_sessions_by_types_in_wishlist(user)
        session = sessions.items[0]
        data = data = {field.name: getattr(session, field.name) for field in
                       session.all_fields()}

        self.assertEqual(1, len(sessions.items))
        self.assertEquals('This is the title', data['title'])

    def make_conference_and_session(self):
        email = 'kdoole@gmail.com'
        self.loginUser(email)
        user = users.get_current_user()
        conf_id, profile = self.make_conference(conf_name='a conference',
                                                email=email)

        request = ConferenceSessionForm(
            title='This is the title',
            date="2016-12-12",
            typeOfSession="workshop",
            startTime="13:15",
            websafeConferenceKey=conf_id,
            speakerEmails=['a.speaker@test.com']
        )
        session_service = SessionService()
        websafe_session_key = session_service.create_conference_session(
            request, user)
        return user, websafe_session_key
