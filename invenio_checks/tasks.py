# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Checks Tasks."""

from datetime import datetime, timezone

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from flask import current_app
from invenio_db import db
from invenio_records_resources.services.uow import UnitOfWork

from .models import CheckRun, CheckRunStatus


@shared_task(bind=True, max_retries=3)
def run_check_async(self, check_run_id):
    """Celery task to run a check asynchronously."""
    from .api import ChecksAPI

    try:
        check_run = CheckRun.query.filter_by(id=check_run_id).one_or_none()
        if not check_run:
            current_app.logger.error(
                "Check run not found",
                extra={"check_run_id": check_run_id},
            )
            return None

        config = check_run.config
        target_type = getattr(config.check_cls, "target_type", None)

        if target_type == "record":
            from invenio_rdm_records.proxies import (
                current_rdm_records_service as service,
            )

            if check_run.is_draft:
                target = service.draft_cls.get_record(check_run.record_id)
            else:
                target = service.record_cls.get_record(check_run.record_id)

        elif target_type == "community":
            from invenio_communities.proxies import (
                current_communities,
            )

            target = current_communities.service.record_cls.get_record(
                check_run.record_id
            )

        else:
            current_app.logger.error(
                "Invalid target_type for config",
                extra={"target_type": target_type},
            )
            return None

        if not config or not target:
            current_app.logger.error("Config or target not found")
            return None

        check_run.status = CheckRunStatus.RUNNING
        check_run.start_time = datetime.now(timezone.utc)
        db.session.commit()

        with UnitOfWork() as uow:
            # Run synchronously inside the worker.
            ChecksAPI.run_check(config, target, uow, sync=True)
            uow.commit()

        return str(check_run.id)

    except Exception as e:
        is_timeout = isinstance(e, SoftTimeLimitExceeded)
        error_message = (
            "Check run timed out after max retries" if is_timeout else str(e)
        )

        current_app.logger.exception(
            "Error running async check run" + (" (timed out)" if is_timeout else ""),
            extra={
                "check_run_id": check_run_id,
                "retry": self.request.retries,
            },
        )

        try:
            # Retry after 10s, 20s, then 30s.
            raise self.retry(
                exc=e,
                countdown=(self.request.retries + 1) * 10,
            )

        except MaxRetriesExceededError:
            try:
                check_run = CheckRun.query.filter_by(id=check_run_id).one_or_none()

                # Don't overwrite a run that may have completed meanwhile.
                if check_run and check_run.status in (
                    CheckRunStatus.PENDING,
                    CheckRunStatus.RUNNING,
                ):
                    check_run.status = CheckRunStatus.ERROR
                    check_run.end_time = datetime.now(timezone.utc)
                    check_run.state = {"error": error_message}
                    db.session.commit()

            except Exception:
                current_app.logger.exception(
                    "Failed to mark check run as ERROR",
                    extra={"check_run_id": check_run_id},
                )

            return None
