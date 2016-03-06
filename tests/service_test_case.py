import unittest

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import taskqueue
from google.appengine.ext import testbed
from mock import MagicMock

from models.conference import Conference
from models.profile import Profile

from support.Auth import Auth


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_user_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_taskqueue_stub()
        # Clear ndb's in-context cache between tests.
        # This prevents data from leaking between tests.
        # Alternatively, you could disable caching by
        # using ndb.get_context().set_cache_policy(False)
        ndb.get_context().clear_cache()

    def tearDown(self):
        self.testbed.deactivate()

    def mock_auth(self, email_address):
        auth = Auth()
        auth.get_user_id = MagicMock(return_value=unicode(email_address))
        return auth

    def loginUser(self, email='user@example.com', id='123', is_admin=False):
        self.testbed.setup_env(
            user_email=email,
            user_id=id,
            user_is_admin='1' if is_admin else '0',
            overwrite=True)

    def testLogin(self):
        assert not users.get_current_user()
        self.loginUser()
        assert users.get_current_user().email() == 'user@example.com'
        self.loginUser(is_admin=True)
        assert users.is_current_user_admin()

    def make_conference(self, conf_name, email):
        p_key = ndb.Key(Profile, email)
        profile = Profile(mainEmail=email, key=p_key).put()
        conf_id = Conference(name=conf_name,
                             organizerUserId=email,
                             parent=p_key).put().urlsafe()
        return conf_id, profile
