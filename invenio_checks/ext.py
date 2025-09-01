# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio checks application."""

from . import config
from .base import ChecksRegistry
from .utils import translate_field


class InvenioChecks(object):
    """Invenio-Checks extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["invenio-checks"] = self
        self.checks_registry = ChecksRegistry()
        self.checks_registry.load_from_entry_points(app, "invenio_checks.check_types")
        # Register Jinja filters
        app.jinja_env.filters["translate_field"] = translate_field

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("CHECKS_"):
                app.config.setdefault(k, getattr(config, k))
