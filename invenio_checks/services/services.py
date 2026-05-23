# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT

"""Checks services."""

from invenio_records_resources.services.records import RecordService


class BaseClass(RecordService):
    """Base service class for DB-backed services.

    NOTE: See https://github.com/inveniosoftware/invenio-records-resources/issues/583
    for future directions.
    TODO: This has to be addressed now, since we're at 4+ cases that need a DB service.
    """

    def rebuild_index(self, identity, uow=None):
        """Raise error since services are not backed by search indices."""
        raise NotImplementedError()


class CheckConfigService(RecordService):
    """Service for managing and check configurations."""

    def read(self, identity, id_, **kwargs):
        """Read a check configuration."""
        raise NotImplementedError()

    def search(self, identity, params=None, **kwargs):
        """Search for check configurations."""
        raise NotImplementedError()

    def create(self, identity, data, uow=None, **kwargs):
        """Create a check configuration."""
        raise NotImplementedError()

    def update(self, identity, id_, data, revision_id=None, uow=None, **kwargs):
        """Update a check configuration."""
        raise NotImplementedError()

    def delete(self, identity, id_, revision_id=None, uow=None, **kwargs):
        """Delete a check configuration."""
        raise NotImplementedError()
