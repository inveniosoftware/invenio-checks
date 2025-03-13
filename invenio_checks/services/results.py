# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Checks service results."""

from collections.abc import Iterable, Sized

from flask_sqlalchemy.pagination import Pagination
from invenio_records_resources.services.records.results import RecordItem, RecordList


class Item(RecordItem):
    """Single item result."""

    @property
    def id(self):
        """Get the result id."""
        return str(self._record.id)


class List(RecordList):
    """List result."""

    @property
    def items(self):
        """Iterator over the items."""
        if isinstance(self._results, Pagination):
            return self._results.items
        elif isinstance(self._results, Iterable):
            return self._results
        return self._results

    @property
    def total(self):
        """Get total number of hits."""
        if hasattr(self._results, "hits"):
            return self._results.hits.total["value"]
        if isinstance(self._results, Pagination):
            return self._results.total
        elif isinstance(self._results, Sized):
            return len(self._results)
        else:
            return None

    # TODO: See if we need to override this
    @property
    def aggregations(self):
        """Get the search result aggregations."""
        try:
            return self._results.labelled_facets.to_dict()
        except AttributeError:
            return None

    @property
    def hits(self):
        """Iterator over the hits."""
        for hit in self.items:
            # Project the hit
            hit_dict = hit.dump()
            hit_record = AttrDict(hit_dict)
            projection = self._schema.dump(
                hit_record,
                context=dict(identity=self._identity, record=hit),
            )
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(self._identity, hit)
            if self._nested_links_item:
                for link in self._nested_links_item:
                    link.expand(self._identity, hit, projection)

            yield projection
