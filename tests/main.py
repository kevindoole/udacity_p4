import unittest

from session_service_test import TestSessionService
from speaker_service_test import TestSpeakerService
from wishlist_service_test import TestWishlistService

session = unittest.TestLoader().loadTestsFromTestCase(TestSessionService)
speaker = unittest.TestLoader().loadTestsFromTestCase(TestSpeakerService)
wishist = unittest.TestLoader().loadTestsFromTestCase(TestWishlistService)

allTests = unittest.TestSuite([session, speaker])
unittest.TextTestRunner(verbosity=2).run(allTests)
