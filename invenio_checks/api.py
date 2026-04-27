# -*- coding: utf-8 -*-
#
# Copyright (C) 2025-2026 CERN.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Checks API."""

from datetime import datetime, timezone

from flask import current_app
from invenio_db import db
from invenio_db.uow import ModelCommitOp

from .models import CheckConfig, CheckRun, CheckRunStatus
from .proxies import current_checks_registry
from .tasks import run_check_async


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
    def _create_or_update_check_run(
        cls,
        config,
        record,
        is_draft: bool,
        status: CheckRunStatus,
        state={},
        result={},
        start_time=None,
        end_time=None,
    ):
        """Create or update check run if already exists."""
        previous_run = CheckRun.query.filter_by(
            config_id=config.id,
            record_id=record.id,
            is_draft=is_draft,
        ).one_or_none()

        if not previous_run:
            result_run = CheckRun(
                config=config,
                record_id=record.id,
                is_draft=is_draft,
                revision_id=record.revision_id,
                start_time=start_time,
                end_time=end_time,
                status=status,
                state=state,
                result=result,
            )
        else:
            result_run = previous_run
            result_run.is_draft = is_draft
            result_run.revision_id = record.revision_id
            result_run.start_time = start_time
            result_run.end_time = end_time
            result_run.status = status
            result_run.state = state
            result_run.result = result

        return result_run

    @classmethod
    def run_check(cls, config, record, uow, is_draft=None, sync=False):
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
            if not check_cls:
                raise ValueError(
                    f"Check class not found for check_id: {config.check_id}"
                )

            should_run_sync = getattr(check_cls, "sync", True)
            check_instance = check_cls()

            if should_run_sync or sync:
                start_time = datetime.now(timezone.utc)
                res = check_instance.run(record, config)
                end_time = datetime.now(timezone.utc)

                result_run = cls._create_or_update_check_run(
                    config,
                    record,
                    is_draft,
                    CheckRunStatus.COMPLETED,
                    result=res.to_dict(),
                    start_time=start_time,
                    end_time=end_time,
                )

                uow.register(ModelCommitOp(result_run))
            else:
                result_run = cls._create_or_update_check_run(
                    config,
                    record,
                    is_draft,
                    CheckRunStatus.PENDING,
                )

                uow.register(ModelCommitOp(result_run))
                db.session.commit()

                run_check_async.delay(
                    check_run_id=str(result_run.id),
                )
        except Exception as e:
            current_app.logger.exception(
                "Error running check on record",
                extra={
                    "record_id": str(record.id),
                    "check_config_id": str(config.id),
                },
            )
            if not result_run:
                return

            try:
                result_run.status = CheckRunStatus.ERROR
                result_run.state = {"error": str(e)}
                db.session.commit()
            except:
                current_app.logger.exception(
                    "Failed to mark check run as ERROR",
                    extra={"check_run_id": getattr(result_run, "id", None)},
                )

        return result_run
