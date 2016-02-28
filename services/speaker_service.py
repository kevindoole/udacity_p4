from models.speaker import Speaker, SpeakerForm, SpeakerForms
from services.base_service import BaseService


class SpeakerService(BaseService):
    @staticmethod
    def find_or_create(email):
        speaker = Speaker.query(Speaker.email == email).get()

        if speaker is not None:
            return speaker.key.urlsafe()
        else:
            return Speaker(email=email).put().urlsafe()

    def get_speakers(self):
        speakers = Speaker.query().fetch()

        return SpeakerForms(
            items=[self.copy_entity_to_form(
                SpeakerForm(), speaker) for speaker in speakers])
