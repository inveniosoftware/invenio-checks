# SPDX-FileCopyrightText: 2026 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Schemas for parameter parsing."""

from flask_resources import MultiDictSchema
from marshmallow import fields


class ChecksSearchRequestArgsSchema(MultiDictSchema):
    """Request URL query string arguments."""

    q = fields.String()
