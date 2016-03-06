#!/usr/bin/env python

"""speaker_service.py

Handle requests related to Speakers.
"""

from models.speaker import Speaker, SpeakerForm, SpeakerForms
from services.base_service import BaseService


class SpeakerService(BaseService):
    """Interface between the client and Speaker Data Store."""

    @staticmethod
    def find_or_create(email):
        """Finds an existing speaker by email, or creates a new one if one does
        not exist.

        Args:
            email (string)

        Returns:
             Speaker
        """
        speaker = Speaker.query(Speaker.email == email).get()

        if speaker is not None:
            return speaker.key.urlsafe()
        else:
            return Speaker(email=email).put().urlsafe()

    def get_speakers(self):
        """Gets a list of all existing speakers.

        Returns:
             SpeakerForms
        """
        speakers = Speaker.query().fetch()

        return SpeakerForms(
            items=[self.copy_entity_to_form(
                SpeakerForm(), speaker) for speaker in speakers])
