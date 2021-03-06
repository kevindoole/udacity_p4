# Conferences API

This API provides endpoints through which to manage all the various
elements of a a conference, from creating a conference, to organizing
sessions and speakers, to registration, as well as various conference
attendee-focused features.

This is a project created by the Udacity team as part of the Full-Stack
Developer Nanodegree program. To that end, various comments below
are made to address questions posed in the course material.

## Installation

In order to try the api out:

1. Clone the repo `git clone git@github.com:kevindoole/udacity_p4.git`.
2. Install [GoogleAppEngineLauncher](https://cloud.google.com/appengine/downloads).
3. Run AppEngineLauncher and find the option to "Add existing
 application..." which you can use to add the cloned repo.
4. Once you've added the application, run it and visit
 localhost:8080/_ah/api/explorer to use the api explorer.
5. If you have an Google App Engine instance, change the application ID
 at the top of app.yaml to your own, and deploy to use the api online.

## Architecture

At a high level, the API is organized into three layers: the domain
layer, the service layer and the client layer.
- The domain layer defines all of the models and form messages.
- The service layer handles business logic when it comes to interacting
with the domain layer.
- The client layer handles authorization and provides the actual
endpoints that users of the API will use to interact with data.

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

On the API side, in addition to the requested endpoints
(getConferenceSessions, getConferenceSessionsByType, createSession,
getSessionsBySpeaker), we also have getSpeakers, which helps us find
urlsafe speaker keys, to use with getSessionsBySpeaker.

## Task 3: Additional queries

Task 3 asks for 2 additional queries to be created. I found the wishlist
to be a feature of particular value to conference-goers. This segment
of the potential consumer of this API seemed valuable, so I aimed to
create some features around wishlists. I added these endpoints:

- getSessionsByWishlistSpeakers: gets other sessions (from any
conference) that speakers in the user's wishlist are involved in
- getSessionsByWishlistTypes: gets other sessions (from any conference)
with topics that are found in the user's wishlist

## Task 3: Querying for specific sets of sessions

Task 3 asks the questions, "How would you handle a query for all
non-workshop sessions before 7 pm? What is the problem for implementing
this query? What ways to solve it did you think of?"

### Problem

For scalability and performance, Datastore has some limitations on
queries. From the App Engine docs, "To avoid having to scan the entire
index, the query mechanism relies on all of a query's potential results
being adjacent to one another in the index." So a single query cannot
use inequality comparisons on more than one property. For example,
querying for `startTime < 7pm` and `sessionType != workshop` is not
valid.

### Solution

One solution to this problem would be to create a Datastore kind called
SessionType, which ConferenceSessions would descend from. In this way,
it would be possible to query for conference sessions which descend from
a particular session type, and the time is before 7pm.

Another option is to query for all sessions at a particular time, and
then apply the type filter programatically after all records have been
retrieved from Datastore. This solution is not as scalable, but a little
easier to complete.

If I needed to maintain this project beyond the date when I submit it 
for review, I would most definitely opt for creating a SessionType kind.
Because I don't need to maintain it, I'll go with the easier option,
filtering results programatically. See `getSessionsByTypeAndFilters`.
