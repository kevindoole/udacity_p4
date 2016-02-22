import endpoints

from models.speaker import Speaker
from services.base_service import BaseService
from google.appengine.ext import ndb


class SpeakerService(BaseService):
    @staticmethod
    def find_or_create(email):
        speaker_key = ndb.Key(Speaker, email)
        if speaker_key.get() is None:
            speaker_key = Speaker(email=email).put().urlsafe()
        else:
            speaker_key = speaker_key.get().urlsafe()

        return speaker_key
