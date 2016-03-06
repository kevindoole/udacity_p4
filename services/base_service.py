class BaseService(object):
    def copy_entity_to_form(self, form, entity):
        """Copy relevant fields from Conference to ConferenceForm.
        :param entity:
        :param form:
        """

        for field in form.all_fields():
            if hasattr(entity, field.name):
                setattr(form, field.name, getattr(entity, field.name))
            elif field.name == "websafeKey":
                setattr(form, field.name, entity.key.urlsafe())
        form.check_initialized()
        return form
