from models.speaker import Speaker
from service_test_case import ServiceTestCase
from services.speaker_service import SpeakerService


class TestSpeakerService(ServiceTestCase):
    def test_it_can_create_new_speakers(self):
        SpeakerService.find_or_create('me@whatever.com')

        speakers = Speaker.query().fetch(2)
        self.assertEqual(1, len(speakers))
        self.assertEquals('me@whatever.com', speakers[0].email)

    def test_it_can_find_existing_speakers(self):
        SpeakerService.find_or_create('me@whatever.com')
        SpeakerService.find_or_create('you@whatever.com')
        speakers = Speaker.query().fetch(10)
        self.assertEqual(2, len(speakers))
        speaker1 = speakers[0]

        SpeakerService.find_or_create('you@whatever.com')
        SpeakerService.find_or_create('me@whatever.com')
        speakers = Speaker.query().fetch(10)
        self.assertEqual(2, len(speakers))

        speakers = Speaker.query(Speaker.email == speaker1.email).fetch(10)
        self.assertEqual(1, len(speakers))
