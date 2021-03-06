#!/usr/bin/env python

"""AppliesFilters.py

Enables appending generic field, operator, value filtering to an ndb query.

"""

from datetime import datetime

import endpoints
from google.appengine.ext import ndb

OPERATORS = {'EQ': '=', 'GT': '>', 'GTEQ': '>=', 'LT': '<', 'LTEQ': '<=',
             'NE': '!='}


class AppliesFilters(object):
    """Register a set of filters and then apply them to an ndb query."""

    def __init__(self, kind, field_types, fields):
        """Initialize possible filter types and fields"""
        self.kind = kind
        self.int_values = field_types.get('int', [])
        self.date_values = field_types.get('date', [])
        self.fields = fields

    def get_query(self, filters, order_by_field='name',
                  websafe_conference_key=None):
        """Return formatted query from the submitted filters."""
        if websafe_conference_key:
            query = self.kind.query(
                self.kind.websafeConferenceKey == websafe_conference_key)
        else:
            query = self.kind.query()

        inequality_filter, filters = self.format_filters(filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            query = query.order(getattr(self.kind, order_by_field))
        else:
            query = query.order(ndb.GenericProperty(inequality_filter))
            query = query.order(getattr(self.kind, order_by_field))

        for filtr in filters:
            if filtr["field"] in self.int_values:
                filtr["value"] = int(filtr["value"])
            if filtr["field"] in self.date_values:
                filtr["value"] = datetime.strptime(
                    filtr["value"], "%Y-%m-%d").date()
            formatted_query = ndb.query.FilterNode(filtr["field"],
                                                   filtr["operator"],
                                                   filtr["value"])
            query = query.filter(formatted_query)
        return query

    def format_filters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {field.name: getattr(f, field.name) for field in
                     f.all_fields()}

            try:
                filtr["field"] = self.fields[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException(
                    "Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used in previous
                # filters
                # disallow the filter if inequality was performed on a
                # different field before
                # track the field on which the inequality operation is performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException(
                        "Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return inequality_field, formatted_filters
