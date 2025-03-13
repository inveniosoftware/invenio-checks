# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Check implementations and registry."""

import importlib_metadata


class Check:
    """Base Check class for all curation checks."""

    id: str
    """Unique identifier for the check."""

    title: str
    """Human-readable name."""

    description: str
    """Description of the check's purpose."""

    def validate_config(self, config):
        """Validate the configuration for this check."""
        raise NotImplementedError()

    def run(self, record, config):
        """Run the check on a record with the given configuration."""
        raise NotImplementedError()


class ChecksRegistry:
    """Registry for check classes."""

    def __init__(self):
        """Initialize the registry."""
        self._checks = {}

    def register(self, check_cls):
        """Register a check class."""
        if not issubclass(check_cls, Check):
            raise TypeError("Class must inherit from Check")

        check_id = check_cls.id
        if not check_id:
            raise ValueError("Check class must define an id")

        if check_id in self._checks:
            raise ValueError(f"Check with id '{check_id}' already registered")

        self._checks[check_id] = check_cls
        return check_cls

    def get(self, check_id):
        """Get a check class by id."""
        check_cls = self._checks.get(check_id)
        if not check_cls:
            raise ValueError(f"No check registered with id '{check_id}'")
        return check_cls

    def get_all(self):
        """Get all registered check classes."""
        return self._checks.copy()

    def load_from_entry_points(self, app, ep_name):
        """Load checks from entry points."""
        for ep in set(importlib_metadata.entry_points(group=ep_name)):
            check_cls_or_func = ep.load()
            check_cls = check_cls_or_func

            self.register(check_cls)
