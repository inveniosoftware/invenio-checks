# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Checks proxies."""

from flask import current_app
from werkzeug.local import LocalProxy

current_checks_registry = LocalProxy(
    lambda: current_app.extensions["invenio-checks"].checks_registry
)
