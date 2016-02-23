import unittest

from session_service_test import TestSessionService
from speaker_service_test import TestSpeakerService

session = unittest.TestLoader().loadTestsFromTestCase(TestSessionService)
speaker = unittest.TestLoader().loadTestsFromTestCase(TestSpeakerService)

allTests = unittest.TestSuite([session, speaker])
unittest.TextTestRunner(verbosity=2).run(allTests)