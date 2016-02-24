from models.speaker import Speaker
from services.base_service import BaseService


class SpeakerService(BaseService):
    @staticmethod
    def find_or_create(email):
        speaker = Speaker.query(Speaker.email == email).get()

        if speaker is not None:
            return speaker.key.urlsafe()
        else:
            return Speaker(email=email).put().urlsafe()
