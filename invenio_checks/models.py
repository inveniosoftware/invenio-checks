# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database models."""

import enum
import uuid

from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import validates
from sqlalchemy_utils import Timestamp
from sqlalchemy_utils.types import ChoiceType, JSONType, UUIDType

from .proxies import current_checks_registry

JSON = (
    db.JSON()
    .with_variant(postgresql.JSONB(none_as_null=True), "postgresql")
    .with_variant(JSONType(), "sqlite")
    .with_variant(JSONType(), "mysql")
)


class Severity(enum.Enum):
    """Severity levels for checks."""

    INFO = "I"
    WARN = "W"
    FAIL = "F"


class CheckConfig(db.Model):
    """Configuration for a check in a community."""

    __tablename__ = "checks_config"

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    community_id = db.Column(
        UUIDType, db.ForeignKey(CommunityMetadata.id), nullable=False
    )
    check_id = db.Column(db.String(255), nullable=False)
    params = db.Column(JSON, nullable=False)
    severity = db.Column(
        ChoiceType(Severity, impl=db.CHAR(1)), nullable=False, default=Severity.INFO
    )
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    @validates("check_id")
    def validate_check_id(self, key, check_id):
        """Validate check_id."""
        if not current_checks_registry.get(check_id):
            raise ValueError(f"Check with id '{check_id}' not found")
        return check_id


class CheckRunStatus(enum.Enum):
    """Status of a check run."""

    PENDING = "P"
    RUNNING = "R"
    COMPLETED = "C"
    ERROR = "E"


class CheckRun(db.Model, Timestamp):
    """Check run state."""

    __tablename__ = "checks_run"

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    config_id = db.Column(UUIDType, db.ForeignKey(CheckConfig.id), nullable=False)
    record_id = db.Column(UUIDType, nullable=False)
    is_draft = db.Column(db.Boolean, nullable=False, default=False)
    revision_id = db.Column(db.Integer, nullable=False)

    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(ChoiceType(CheckRunStatus, impl=db.CHAR(1)), nullable=False)
    state = db.Column(JSON, nullable=False)
    result = db.Column(JSON, nullable=False)

    __table_args__ = (
        db.Index("idx_checks_run_config_id_record_id", config_id, record_id),
    )
