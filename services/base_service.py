#!/usr/bin/env python

"""base_service.py

Provide generic functionality useful to all services. In this application, the
service layer provides the interface through which the client side (the
endpoints API methods) interact with Data Store.

The service layer expects all auth to be handled already, and should always
return a protorpc message class which can be piped through directly to the
API response.

"""


class BaseService(object):
    """Generic functionality for the service layer."""

    def copy_entity_to_form(self, form, entity):
        """Copy relevant fields from a Data Store entity to a protorpc message.

        Args:
            form (messages.Message)
            entity (ndb.Model)

        Returns:
             messages.Message
        """

        for field in form.all_fields():
            if (field.name is 'teeShirtSize'):
                continue
            if hasattr(entity, field.name):
                setattr(form, field.name, getattr(entity, field.name))
            elif field.name == "websafeKey":
                setattr(form, field.name, entity.key.urlsafe())
        form.check_initialized()

        return form
