# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Checks Tasks."""

from datetime import datetime, timezone

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from flask import current_app
from invenio_db import db
from invenio_records_resources.services.uow import UnitOfWork
from sqlalchemy import and_, or_

from .models import CheckRun, CheckRunStatus


@shared_task(bind=True, max_retries=3, soft_time_limit=120, time_limit=180)
def run_check_async(self, check_run_id):
    """Celery task to run a check asynchronously."""
    from .api import ChecksAPI

    started = None
    try:
        # Set RUNNING before loading the record, so the record cannot be older than
        # this write. The status filter stops a retry from restarting a run that
        # already finished, and `start_time` tells run_check which attempt this is.
        started = datetime.now(timezone.utc)
        updated = (
            db.session.query(CheckRun)
            .filter(
                CheckRun.id == check_run_id,
                CheckRun.status.in_([CheckRunStatus.PENDING, CheckRunStatus.RUNNING]),
            )
            .update(
                {"status": CheckRunStatus.RUNNING, "start_time": started},
                synchronize_session=False,
            )
        )
        db.session.commit()
        if not updated:
            current_app.logger.info(
                "Check run already finished or gone, skipping",
                extra={"check_run_id": check_run_id},
            )
            return None

        check_run = CheckRun.query.filter_by(id=check_run_id).one_or_none()
        if not check_run:
            return None

        config = check_run.config
        target = ChecksAPI.get_target(check_run)

        if not config or not target:
            current_app.logger.error(
                "Config or target not found",
                extra={"check_run_id": check_run_id},
            )
            return None

        with UnitOfWork() as uow:
            # Run synchronously inside the worker.
            ChecksAPI.run_check(
                config,
                target,
                uow,
                sync=True,
                is_draft=check_run.is_draft,
                started=started,
            )
            uow.commit()

        return str(check_run_id)

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

        if self.request.retries < self.max_retries:
            # Retry after 10s, 20s, then 30s.
            raise self.retry(exc=e, countdown=(self.request.retries + 1) * 10)

        try:
            db.session.rollback()
            # Fail the run only while `start_time` is unchanged. Clearing `state`
            # makes the next save run the check again.
            if started is not None:
                db.session.query(CheckRun).filter(
                    CheckRun.id == check_run_id,
                    CheckRun.start_time == started,
                ).update(
                    {
                        "status": CheckRunStatus.ERROR,
                        "end_time": datetime.now(timezone.utc),
                        "state": {"error": error_message},
                    },
                    synchronize_session=False,
                )
                db.session.commit()

        except Exception:
            current_app.logger.exception(
                "Failed to mark check run as ERROR",
                extra={"check_run_id": check_run_id},
            )

        return None


@shared_task
def cleanup_stale_check_runs():
    """Fail check runs whose worker never came back."""
    now = datetime.now(timezone.utc)
    cutoff = now - current_app.config["CHECKS_RUN_STALE_AFTER"]
    stale = CheckRun.query.filter(
        or_(
            and_(
                CheckRun.status == CheckRunStatus.RUNNING,
                # The worker rewrites `start_time` when it starts, so a run that
                # waited in the queue is not failed the moment it begins.
                CheckRun.start_time < cutoff,
            ),
            and_(
                CheckRun.status == CheckRunStatus.PENDING,
                # No worker picked it up, so `updated` is when it was written.
                CheckRun.updated < cutoff,
            ),
        )
    ).update(
        {
            "status": CheckRunStatus.ERROR,
            "end_time": now,
            # Clear `state` like the error path above, so the next save runs the
            # check again.
            "state": {"error": "Check run did not finish"},
        },
        synchronize_session=False,
    )
    db.session.commit()

    if stale:
        current_app.logger.warning(
            "Failed stale check runs", extra={"check_run_count": stale}
        )
