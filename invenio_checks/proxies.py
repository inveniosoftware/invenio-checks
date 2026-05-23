# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT
"""Checks proxies."""

from flask import current_app
from werkzeug.local import LocalProxy

current_checks_registry = LocalProxy(
    lambda: current_app.extensions["invenio-checks"].checks_registry
)
