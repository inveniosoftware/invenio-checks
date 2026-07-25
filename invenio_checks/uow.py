# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Unit of work."""

from invenio_db.uow import Operation


class _CeleryTaskOp(Operation):
    """Dispatch a Celery task after the UoW commits."""

    def __init__(self, task, check_run):
        self._task = task
        self._check_run = check_run

    def on_commit(self, uow):
        """Dispatch the task after the DB transaction is committed."""
        self._task.delay(check_run_id=str(self._check_run.id))


class _ConvertDraftToRecordCheckRunOp(Operation):
    """Convert a draft check run to a record run in-place."""

    def __init__(self, draft_run, existing_record_run, record):
        self._draft_run = draft_run
        self._existing_record_run = existing_record_run
        self._record = record

    def on_register(self, uow):
        """Delete stale record run, then promote draft run to record run."""
        if self._existing_record_run:
            uow.session.delete(self._existing_record_run)
            uow.session.flush()
        self._draft_run.is_draft = False
        self._draft_run.revision_id = self._record.revision_id
        uow.session.add(self._draft_run)
