from protorpc import messages
from google.appengine.ext import ndb


class ConferenceSession(ndb.Model):
    """Session -- Session object"""
    title = ndb.StringProperty(required=True)
    highlights = ndb.TextProperty()
    websafeConferenceKey = ndb.StringProperty()
    speakerKeys = ndb.TextProperty(repeated=True, indexed=True)
    duration = ndb.IntegerProperty()
    typeOfSession = ndb.StringProperty()
    dateTime = ndb.DateTimeProperty(required=True)
    hour = ndb.IntegerProperty()


class ConferenceSessionForm(messages.Message):
    """SessionForm -- Session query inbound form message"""
    title = messages.StringField(1)
    highlights = messages.StringField(2)
    speakerEmails = messages.StringField(3, repeated=True)
    duration = messages.IntegerField(4)
    typeOfSession = messages.StringField(5)
    date = messages.StringField(6)
    startTime = messages.StringField(7)
    websafeConferenceKey = messages.StringField(8)
    websafeSessionKey = messages.StringField(9)


class ConferenceSessionForms(messages.Message):
    """SessionForms -- multiple Session outbound form message"""
    items = messages.MessageField(ConferenceSessionForm, 1, repeated=True)


class ConferenceSessionQueryForm(messages.Message):
    """ConferenceQueryForm -- Conference query inbound form message"""
    field = messages.StringField(1)
    operator = messages.StringField(2)
    value = messages.StringField(3)


class ConferenceSessionQueryForms(messages.Message):
    """ConferenceQueryForms -- multiple ConferenceQueryForm inbound form
    message"""
    filters = messages.MessageField(ConferenceSessionQueryForm, 1,
                                    repeated=True)
    typeOfSession = messages.StringField(2, required=True)
    websafeConferenceKey = messages.StringField(3)
