# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Checks API."""

from datetime import datetime

from flask import current_app
from invenio_db.uow import ModelCommitOp

from .models import CheckConfig, CheckRun, CheckRunStatus
from .proxies import current_checks_registry


class ChecksAPI:
    """API for managing checks."""

    @classmethod
    def get_runs(cls, record, is_draft=None):
        """Get all check runs for a record or draft."""
        if is_draft is None:
            is_draft = record.is_draft
        return CheckRun.query.filter_by(record_id=record.id, is_draft=is_draft).all()

    @classmethod
    def get_configs(cls, community_ids):
        """Get all check configurations for a list of community IDs."""
        if not community_ids:
            return []

        return CheckConfig.query.filter(
            CheckConfig.community_id.in_(community_ids),
            CheckConfig.enabled.is_(True),
        ).all()

    @classmethod
    def run_check(cls, config, record, uow, is_draft=None):
        """Run a check for a given configuration on a record or draft.

        If a check run already exists for the given configuration and record/draft, it
        updates the run with the new results. If no run exists, it will create it.
        If the operation fails, an error is logged and `None` is returned.
        """
        if is_draft is None:
            is_draft = record.is_draft

        result_run = None
        try:
            check_cls = current_checks_registry.get(config.check_id)
            start_time = datetime.utcnow()
            res = check_cls().run(record, config)
            end_time = datetime.utcnow()

            # Fetch the previous run
            previous_run = CheckRun.query.filter_by(
                config_id=config.id,
                record_id=record.id,
                is_draft=is_draft,
            ).one_or_none()

            if not previous_run:
                result_run = CheckRun(
                    config_id=config.id,
                    record_id=record.id,
                    is_draft=is_draft,
                    revision_id=record.revision_id,
                    start_time=start_time,
                    end_time=end_time,
                    status=CheckRunStatus.COMPLETED,
                    state="",
                    result=res.to_dict(),
                )
            else:
                result_run = previous_run
                result_run.is_draft = is_draft
                result_run.revision_id = record.revision_id
                result_run.start_time = start_time
                result_run.end_time = end_time
                result_run.result = res.to_dict()

            uow.register(ModelCommitOp(result_run))
        except Exception:
            current_app.logger.exception(
                "Error running check on record",
                extra={
                    "record_id": str(record.id),
                    "check_config_id": str(config.id),
                },
            )

        return result_run
