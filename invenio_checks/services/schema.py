# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Service schemas."""

from datetime import timezone

from marshmallow import EXCLUDE, Schema, fields
from marshmallow_utils.fields import SanitizedHTML, SanitizedUnicode, TZDateTime
from marshmallow_utils.permissions import FieldPermissionsMixin

from ..models import CheckRunStatus


class CheckConfigSchema(Schema, FieldPermissionsMixin):
    """Base schema for a check configuration."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = EXCLUDE

    id = fields.UUID(dump_only=True)

    created = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)
    updated = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)

    title = SanitizedUnicode(required=True)
    # Rule descriptions can contain HTML to link to a page with more details about the rule
    description = SanitizedHTML()

    active = fields.Boolean(load_default=True)


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
