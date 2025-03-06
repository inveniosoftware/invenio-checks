# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Service schemas."""

from datetime import timezone
from uuid import UUID

from marshmallow import EXCLUDE, Schema, ValidationError, fields, validates
from marshmallow_utils.fields import SanitizedUnicode, TZDateTime
from marshmallow_utils.permissions import FieldPermissionsMixin
from sqlalchemy.orm import validates

from ..models import CheckRunStatus, Severity
from ..proxies import current_checks_registry


class CheckConfigSchema(Schema, FieldPermissionsMixin):
    """Base schema for a check configuration."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = EXCLUDE

    id = fields.UUID(dump_only=True)
    community_id = fields.Str(required=True)
    check_id = fields.Str(required=True)
    params = fields.Dict(required=False, default={})
    severity = fields.Str(required=False, default=Severity.INFO.value)
    enabled = fields.Bool(required=False, default=True)

    @validates("community_id")
    def validate_community_id(self, value):
        """Validate that the community_id is a valid UUID."""
        try:
            UUID(value)
        except ValueError:
            raise ValidationError("Invalid UUID format for community_id.")

    @validates("check_id")
    def validate_check_id(self, value):
        """Validate that the check_id exists in the registry."""
        if not current_checks_registry.get(value):
            raise ValidationError(f"Check with id '{value}' not found.")

    @validates("severity")
    def validate_severity(self, value):
        """Validate that the severity is a valid enum value."""
        if value not in [s.value for s in Severity]:
            raise ValidationError(f"Invalid severity value: {value}.")


class CheckRunSchema(Schema, FieldPermissionsMixin):
    """Base schema for a check run."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = EXCLUDE

    id = fields.UUID(dump_only=True)

    created = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)
    updated = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)

    started_at = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)
    finished_at = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)

    status = fields.Enum(CheckRunStatus, dump_only=True)
    message = SanitizedUnicode(dump_only=True)
