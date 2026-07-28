# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-FileCopyrightText: 2025-2026 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Checks API."""

from datetime import datetime, timezone

from flask import current_app
from invenio_db.uow import ModelCommitOp
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_records_resources.services.uow import UnitOfWork
from sqlalchemy import or_

from .models import CheckConfig, CheckRun, CheckRunStatus
from .proxies import current_checks_registry, current_targets_registry
from .tasks import run_check_async
from .uow import AsyncRunTaskOp


class ChecksAPI:
    """API for managing checks."""

    @classmethod
    def get_runs(cls, record, is_draft=None, community_id=None):
        """Get all check runs for an object."""
        if is_draft is None and getattr(record, "is_draft", None) is not None:
            is_draft = record.is_draft

        query = CheckRun.query.filter_by(record_id=record.id, is_draft=is_draft)

        if community_id is not None:
            from invenio_communities.proxies import current_communities

            community = current_communities.service.record_cls.get_record(community_id)
            community_ids = [str(community.id)]
            if community.parent:
                community_ids.append(str(community.parent.id))
            configs = cls.get_configs(community_ids=community_ids)
            query = query.filter(CheckRun.config_id.in_([c.id for c in configs]))

        return query.all()

    @classmethod
    def get_configs(cls, community_ids, target_type=None):
        """Get all check configurations for a list of community IDs.

        Always include the global checks configs to the community checks.
        """
        conditions = [CheckConfig.community_id.is_(None)]

        if community_ids:
            conditions.append(CheckConfig.community_id.in_(community_ids))

        query = CheckConfig.query.filter(
            CheckConfig.enabled.is_(True), or_(*conditions)
        )

        if target_type is not None:
            query = query.filter(CheckConfig.target_type == target_type)

        return query.all()

    @classmethod
    def _create_or_update_check_run(
        cls,
        config,
        record,
        previous_run,
        is_draft: bool,
        status: CheckRunStatus,
        state,
        result=None,
        start_time=None,
        end_time=None,
    ):
        """Create or update check run if already exists."""
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
                result=result or {},
            )
        else:
            result_run = previous_run
            result_run.is_draft = is_draft
            result_run.revision_id = record.revision_id
            result_run.start_time = start_time
            result_run.end_time = end_time
            result_run.status = status
            result_run.state = state
            result_run.result = result or {}

        return result_run

    @classmethod
    def get_target(cls, check_run):
        """Get the target object for a check run."""
        target_type = getattr(check_run.config, "target_type", None)

        try:
            target_cls = current_targets_registry.get(target_type)
        except ValueError:
            current_app.logger.error(
                "Invalid target_type for check config",
                extra={
                    "target_type": target_type,
                    "check_run_id": str(check_run.config.check_id),
                },
            )
            raise

        target_instance = target_cls()
        return target_instance.resolve(check_run)

    @classmethod
    def run_check(cls, config, record, uow, is_draft=None, sync=False, **kwargs):
        """Run a check for a given configuration on a record or draft.

        If a check run already exists for the given configuration and record/draft, it
        updates the run with the new results. If no run exists, it will create it.
        If the operation fails, an error is logged and `None` is returned.
        """
        if is_draft is None and config.target_type == "record":
            is_draft = record.is_draft

        check_cls = current_checks_registry.get(config.check_id)
        if not check_cls:
            current_app.logger.warning(
                "Check class not found",
                extra={"check_id": config.check_id},
            )
            return None

        check_instance = check_cls()
        previous_run = CheckRun.query.filter_by(
            config_id=config.id,
            record_id=record.id,
            is_draft=is_draft,
        ).one_or_none()

        if previous_run and not check_instance.should_rerun(
            record, config, previous_run, **kwargs
        ):
            previous_run.revision_id = record.revision_id
            uow.register(ModelCommitOp(previous_run))
            return previous_run

        if getattr(check_cls, "sync", True) or sync:
            start_time = datetime.now(timezone.utc)
            res, state = check_instance.run(record, config, **kwargs)
            end_time = datetime.now(timezone.utc)

            result_run = cls._create_or_update_check_run(
                config,
                record,
                previous_run,
                is_draft,
                CheckRunStatus.COMPLETED,
                state=state,
                result=res.to_dict(),
                start_time=start_time,
                end_time=end_time,
            )
            uow.register(ModelCommitOp(result_run))
            return result_run

        result_run = cls._create_or_update_check_run(
            config,
            record,
            previous_run,
            is_draft,
            CheckRunStatus.PENDING,
            state=previous_run.state if previous_run else {},
            result=check_instance.pending_result(config.params),
        )
        uow.register(ModelCommitOp(result_run))
        uow.register(AsyncRunTaskOp(run_check_async, result_run))
        return result_run

    @classmethod
    def copy_record_run_to_draft(cls, config, draft, uow):
        """Copy a completed record-level run to a draft run."""
        record_run = CheckRun.query.filter_by(
            config_id=config.id,
            record_id=draft.id,
            is_draft=False,
        ).one_or_none()

        if record_run and record_run.status == CheckRunStatus.COMPLETED:
            draft_run = cls._create_or_update_check_run(
                config=config,
                record=draft,
                previous_run=None,
                is_draft=True,
                status=CheckRunStatus.COMPLETED,
                state=record_run.state or {},
                result=record_run.result or {},
                start_time=record_run.start_time,
                end_time=record_run.end_time,
            )
            uow.register(ModelCommitOp(draft_run))

    @classmethod
    def extract_run_errors(cls, runs):
        """Build errors list from a list of check runs."""
        errors = []
        for run in runs:
            if not run.result or not run.result.get("errors"):
                continue

            for error in run.result.get("errors", []):
                errors.append(
                    {
                        **error,
                        "context": {"community": str(run.config.community_id)},
                    }
                )

        return errors

    @classmethod
    def rerun_check(cls, check_run_id, identity):
        """Rerun an existing check."""
        check_run = CheckRun.query.get(check_run_id)

        if not check_run:
            current_app.logger.warning(
                "Cannot rerun check: check run not found",
                extra={"check_run_id": str(check_run_id)},
            )
            return None

        check_cls = current_checks_registry.get(check_run.config.check_id)
        if check_cls.can_rerun(identity, check_run.record_id) is False:
            current_app.logger.warning(
                "User does not have permission to rerun check",
                extra={
                    "check_run_id": str(check_run_id),
                    "record_id": str(check_run.record_id),
                    "identity": str(identity),
                },
            )
            raise PermissionDeniedError()
        target = cls.get_target(check_run)

        if not target:
            current_app.logger.warning(
                "Cannot rerun check: target not found",
                extra={
                    "check_run_id": str(check_run_id),
                    "record_id": str(check_run.record_id),
                    "target_type": check_run.config.target_type,
                },
            )
            return None

        if not getattr(check_cls, "allow_rerun", False):
            current_app.logger.warning(
                "Manual rerun is not allowed for check",
                extra={
                    "check_run_id": str(check_run_id),
                    "check_id": check_run.config.check_id,
                },
            )
            raise PermissionDeniedError()

        try:
            with UnitOfWork() as uow:
                result = cls.run_check(
                    check_run.config,
                    target,
                    uow,
                    is_draft=check_run.is_draft,
                )
                uow.commit()

            return result

        except Exception:
            current_app.logger.exception(
                "Failed to rerun check",
                extra={
                    "check_run_id": str(check_run_id),
                    "check_id": check_run.config.check_id,
                },
            )
            return None
