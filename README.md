# Conferences API

This API provides endpoints through which to manage all the various
elements of a a conference, from creating a conference, to organizing
sessions and speakers, to registration, as well as various conference
attendee-focused features.

This is a project created by the Udacity team as part of the Full-Stack
Developer Nanodegree program. To that end, various comments below
are made to address questions posed in the course material.

## Architecture

At a high level, the API is organized into three layers: the domain
layer, the service layer and the client layer.
- The domain layer defines all of the models and form messages.
- The service layer handles business logic when it comes to interacting
with the domain layer.
- The client layer handles authorization and provides the actual
endpoints that users of the API will use to interact with data.

TODO: Models and messages in the domain layer extend base model and
message classes which simplify composing messages from models, and back.

### Session and speaker implementation

Task one in this project was to implement sessions and speakers.

Sessions only exist as part of a conference, so they are descendants
of the Conference model. In order to simplify finding sessions belonging
to a conference, each session entity includes a urlsafe conference key.

Speakers are implemented as simply as possible, with nothing more than
an email address identifier, and a name. It did not seem reasonable that
a speaker would need to know anything about sessions, so there is no
direct link from a speaker to a session. On the flip side, sessions are
greatly impacted by having or not having speakers, so keeping a list
of speakers on the session entity seemed to be well worth our while.

To enable API users to work with sessions and users easily, each have
their own service class that helps simplify interacting with datastore.

On the API side, in addition to the requested endpoints
(getConferenceSessions, getConferenceSessionsByType, createSession,
getSessionsBySpeaker), we also have getSpeakers, which helps us find
urlsafe speaker keys, to use with getSessionsBySpeaker.

rubric: https://docs.google.com/document/d/1lVFoZDY-jjg6SoI8g5uZ72V3TDp7iLTz2UGWAI5ZvfE/pub
https://docs.google.com/document/d/1H9anIDV4QCPttiQEwpGe6MnMBx92XCOlz0B4ciD7lOs/pub
https://www.udacity.com/course/viewer#!/c-nd004/l-3566359178/m-3636408594



task 3:
2 additioal queries:
- get other conferences or sessions that speakers in the user's wishlist are involved in
- get other sessions on the same topic as are in the user's wishlist
