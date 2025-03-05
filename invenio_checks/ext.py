# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio checks application."""

from . import config
from .base import ChecksRegistry
from .services import (
    CheckConfigService,
    ChecksConfigServiceConfig,
)


class InvenioChecks(object):
    """Invenio-Checks extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.init_services(app)
        app.extensions["invenio-checks"] = self
        self.checks_registry = ChecksRegistry()
        self.checks_registry.load_from_entry_points(app, "invenio_checks.check_types")

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("CHECKS_"):
                app.config.setdefault(k, getattr(config, k))

    def service_configs(self, app):
        """Customized service configs."""

        class ServiceConfigs:
            checks_configs = ChecksConfigServiceConfig.build(app)

        return ServiceConfigs

    def init_services(self, app):
        """Initialize the service and resource for Requests."""
        service_configs = self.service_configs(app)

        self.checks_configs_service = CheckConfigService(
            config=service_configs.checks_configs,
        )
