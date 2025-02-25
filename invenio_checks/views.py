# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio checks views."""

from flask import Blueprint
from invenio_i18n import gettext as _

blueprint = Blueprint(
    "invenio_checks",
    __name__,
    template_folder="templates",
    static_folder="static",
)
