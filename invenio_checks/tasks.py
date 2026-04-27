# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Checks Tasks."""
from datetime import datetime, timezone
from time import sleep

from celery import shared_task
from flask import current_app
from invenio_db import db
from invenio_rdm_records.proxies import current_rdm_records_service as service
from invenio_records_resources.services.uow import UnitOfWork

from .models import CheckRun, CheckRunStatus


@shared_task(bind=True, max_retries=1)
def run_check_async(self, check_run_id):
    """Celery task to run a check asynchronously."""
    from .api import ChecksAPI

    try:
        check_run = CheckRun.query.filter_by(id=check_run_id).one_or_none()
        if not check_run:
            current_app.logger.error(
                "Check run not found",
                extra={
                    "check_run_id": check_run_id,
                },
            )
            return None

        config = check_run.config
        target_type = getattr(check_run.config.check_cls, "target_type", None)
        if target_type == "record":
            record = service.record_cls.get_record(check_run.record_id)
        else:
            current_app.logger.error(
                "Invalid target_type for config",
                extra={
                    "target_type": target_type,
                },
            )
            return None

        if not config or not record:
            current_app.logger.error("Config or record not found")
            return None

        sleep(10)
        check_run.status = CheckRunStatus.RUNNING
        check_run.start_time = datetime.now(timezone.utc)
        db.session.commit()

        with UnitOfWork() as uow:
            # as we are in the task, run the check synchronously
            ChecksAPI.run_check(config, record, uow, sync=True)
            uow.commit()

        return str(check_run.id)

    except Exception as e:
        current_app.logger.exception(
            "Error running async check run",
            extra={
                "check_run_id": check_run_id,
            },
        )
        try:
            check_run = CheckRun.query.filter_by(id=check_run_id).one_or_none()
            if check_run:
                check_run.status = CheckRunStatus.ERROR
                check_run.state = str(e)
                db.session.commit()
        except:
            pass
        raise self.retry(exc=e, countdown=30)
