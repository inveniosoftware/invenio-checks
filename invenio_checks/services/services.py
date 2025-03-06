# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Checks services."""

from uuid import UUID

from invenio_records_resources.services.base import LinksTemplate
from invenio_records_resources.services.base.utils import map_search_params
from invenio_records_resources.services.records import RecordService
from invenio_records_resources.services.uow import (
    ModelCommitOp,
    ModelDeleteOp,
    unit_of_work,
)
from marshmallow import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from ..models import CheckConfig, Severity
from .schema import CheckConfigSchema


class BaseClass(RecordService):
    """Base service class for DB-backed services.

    NOTE: See https://github.com/inveniosoftware/invenio-records-resources/issues/583
    for future directions.
    TODO: This has to be addressed now, since we're at 4+ cases that need a DB service.
    """

    def rebuild_index(self, identity, uow=None):
        """Raise error since services are not backed by search indices."""
        raise NotImplementedError()


def get_check_config(id_):
    """Get a check config by id."""
    check_config = CheckConfig.query.get(id_)
    if check_config == None:
        raise ValueError(f"Check configuration with id '{id_}' not found")
    return check_config


class CheckConfigService(RecordService):
    """Service for managing check configurations."""

    @unit_of_work()
    def create(self, identity, data, uow=None, **kwargs):
        """Create a check configuration."""
        self.require_permission(identity, "create")

        schema = CheckConfigSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            raise ValueError(f"Validation error: {e.messages}")

        try:
            check_config = CheckConfig(
                community_id=UUID(validated_data["community_id"]),
                check_id=validated_data["check_id"],
                params=validated_data.get("params", {}),
                severity=validated_data.get("severity", Severity.INFO.value),
                enabled=validated_data.get("enabled", True),
            )
            uow.register(ModelCommitOp(check_config))
            return check_config
        except Exception as e:
            raise ValueError(f"Failed to create check configuration: {str(e)}")

    def read(self, identity, id_, **kwargs):
        """Read a check configuration."""
        self.require_permission(identity, "read")
        check_config = get_check_config(id_)
        return check_config

    def search(self, identity, params=None, **kwargs):
        """Search for check configurations."""
        self.require_permission(identity, "search")

        if params is None:
            params = {}
        query = CheckConfig.query

        if "community_id" in params:
            query = query.filter_by(community_id=UUID(params["community_id"]))
        if "check_id" in params:
            query = query.filter_by(check_id=params["check_id"])
        if "enabled" in params:
            query = query.filter_by(enabled=params["enabled"])

        return query.all()

    @unit_of_work()
    def update(self, identity, id_, data, revision_id=None, uow=None, **kwargs):
        """Update a check configuration."""
        self.require_permission(identity, "update")

        schema = CheckConfigSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            raise ValueError(f"Validation error: {e.messages}")

        try:
            check_config = CheckConfig(
                community_id=UUID(validated_data["community_id"]),
                check_id=validated_data["check_id"],
                params=validated_data.get("params", {}),
                severity=validated_data.get("severity", Severity.INFO.value),
                enabled=validated_data.get("enabled", True),
            )
            uow.register(ModelCommitOp(check_config))
            return check_config
        except NoResultFound:
            raise ValueError(f"Check configuration with id '{id_}' not found")
        except Exception as e:
            raise ValueError(f"Failed to update check configuration: {str(e)}")

    @unit_of_work()
    def delete(self, identity, id_, revision_id=None, uow=None, **kwargs):
        """Delete a check configuration."""
        self.require_permission(identity, "delete")

        try:
            check_config = get_check_config(id_)
            uow.register(ModelDeleteOp(check_config))

            return True
        except NoResultFound:
            raise ValueError(f"Check configuration with id '{id_}' not found")
        except Exception as e:
            raise ValueError(f"Failed to delete check configuration: {str(e)}")
