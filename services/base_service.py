class BaseService(object):
    def copy_entity_to_form(self, form, session):
        """Copy relevant fields from Conference to ConferenceForm.
        :param session:
        :param form:
        """
        for field in form.all_fields():
            if hasattr(session, field.name):
                # convert Date to date string; just copy others
                if field.name == 'date' or field.name == 'startTime':
                    setattr(form, field.name, str(getattr(session, field.name)))
                else:
                    setattr(form, field.name, getattr(session, field.name))
            elif field.name == "websafeKey":
                setattr(form, field.name, session.key.urlsafe())
        form.check_initialized()
        return form