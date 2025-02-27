# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Check implementations and registry."""

from datetime import datetime

import importlib_metadata
from flask import current_app
from invenio_db import db
from sqlalchemy.orm.exc import NoResultFound

from .models import CheckConfig, CheckRun, CheckRunStatus


class Check:
    """Base Check class for all curation checks."""

    id = None  # Unique identifier for the check
    name = None  # Human-readable name
    description = None  # Description of the check's purpose

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
            if callable(check_cls_or_func):
                check_cls = check_cls_or_func(app)
            else:
                check_cls = check_cls_or_func

            self.register(check_cls)


class ChecksService:
    """Service for managing and running checks."""

    @property
    def enabled(self):
        """Check if checks are enabled."""
        return current_app.config.get("CHECKS_ENABLED", False)

    def get_check(self, check_id):
        """Get a check by ID."""
        return registry.get(check_id)

    def get_all_checks(self):
        """Get all registered checks."""
        return registry.get_all()

    def get_config(self, config_id):
        """Get a check configuration by ID."""
        try:
            return CheckConfig.query.filter_by(id=config_id).one()
        except NoResultFound:
            raise ValueError(f"No check configuration found with id {config_id}")

    def get_community_configs(self, community_id):
        """Get all check configurations for a community."""
        return CheckConfig.query.filter_by(community_id=community_id).all()

    def create_config(
        self, community_id, check_id, params, severity="error", enabled=True
    ):
        """Create a new check configuration."""
        # Validate the check exists
        check_cls = self.get_check(check_id)

        # Validate the configuration
        try:
            check = check_cls()
            check.validate_config(params)
        except Exception as e:
            raise ValueError(f"Invalid configuration for check {check_id}: {str(e)}")

        # Create the config
        config = CheckConfig(
            community_id=community_id,
            check_id=check_id,
            params=params,
            severity=severity,
            enabled=enabled,
        )

        db.session.add(config)
        db.session.commit()

        return config

    def update_config(self, config_id, params=None, severity=None, enabled=None):
        """Update a check configuration."""
        config = self.get_config(config_id)

        # Update params if provided
        if params is not None:
            # Validate the new params
            check_cls = self.get_check(config.check_id)
            try:
                check = check_cls()
                check.validate_config(params)
                config.params = params
            except Exception as e:
                raise ValueError(f"Invalid configuration: {str(e)}")

        # Update severity if provided
        if severity is not None:
            config.severity = severity

        # Update enabled if provided
        if enabled is not None:
            config.enabled = enabled

        db.session.commit()

        return config

    def delete_config(self, config_id):
        """Delete a check configuration."""
        config = self.get_config(config_id)
        db.session.delete(config)
        db.session.commit()

    def run_check(
        self, record, config_id=None, community_id=None, check_id=None, params=None
    ):
        """Run a check on a record."""
        if not self.enabled:
            raise RuntimeError("Checks are not enabled")

        # Get the configuration
        if config_id:
            config = self.get_config(config_id)
            check_id = config.check_id
            params = config.params
            use_existing_config = True
        elif check_id and params:
            # Use provided check_id and params
            config = None
            use_existing_config = False
        else:
            raise ValueError(
                "Either config_id or both check_id and params must be provided"
            )

        # Get the check class
        check_cls = self.get_check(check_id)
        check = check_cls()

        # Create a run record
        run = CheckRun(
            config_id=config.id if config else None,
            record_id=record.id,
            is_draft=record.is_draft if hasattr(record, "is_draft") else False,
            revision_id=record.revision_id if hasattr(record, "revision_id") else 0,
            status=CheckRunStatus.PENDING,
            state={},
            result={},
        )

        db.session.add(run)
        db.session.commit()

        try:
            # Update status to in progress
            run.status = CheckRunStatus.IN_PROGRESS
            db.session.commit()

            # Run the check
            result = check.run(record, params)

            # Update the run record
            run.status = CheckRunStatus.COMPLETED
            run.result = result.to_dict()
            db.session.commit()

            return run

        except Exception as e:
            # Update the run record with the error
            run.status = CheckRunStatus.ERROR
            run.result = {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            db.session.commit()

            return run

    def get_record_runs(self, record_id, revision_id=None):
        """Get all check runs for a record."""
        query = CheckRun.query.filter_by(record_id=record_id)

        if revision_id is not None:
            query = query.filter_by(revision_id=revision_id)

        return query.all()
