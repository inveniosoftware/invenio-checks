# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record service component."""

from datetime import datetime, timezone

from flask import current_app
from invenio_db import db
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_requests.proxies import current_requests_service
from invenio_search.engine import dsl

from .models import CheckConfig, CheckRun, CheckRunStatus
from .proxies import current_checks_registry


class ChecksComponent(ServiceComponent):
    """Checks component."""

    @property
    def enabled(self):
        """Return if checks are enabled."""
        return current_app.config.get("CHECKS_ENABLED", False)

    def _run_checks(self, identity, data=None, record=None, errors=None, **kwargs):
        """Handler to run checks."""
        if not self.enabled:
            return

        communities = set()
        if record.parent.review and (
            record.parent.review.status == "submitted"
            or record.parent.review.status == "created"
        ):
            # drafts can only be submitted to one community
            community = record.parent.review.receiver.resolve()
            community_id = str(community.id)  # from UUID
            communities.add(community_id)
            community_parent_id = community.get("parent", {}).get("id")
            if community_parent_id:
                communities.add(community_parent_id)
        else:
            results = current_requests_service.search(
                identity,
                extra_filter=dsl.query.Bool(
                    "must",
                    must=[
                        dsl.Q("term", **{"topic.record": record.pid.pid_value}),
                        dsl.Q("term", **{"is_open": True}),
                    ],
                ),
            )

            if results.total > 0:
                for result in results:
                    communities.add(result.get("receiver", {}).get("community"))
                    # check if it is a subcommunity
            else:
                return

        all_checks = CheckConfig.query.filter(
            CheckConfig.community_id.in_(communities)
        ).all()

        for check in all_checks:
            try:
                check_cls = current_checks_registry.get(check.check_id)
                start_time = datetime.now(timezone.utc)
                res = check_cls().run(record, check.params)
                if not res.sync:
                    continue

                check_errors = [
                    {
                        **error,
                        "context": {
                            "community": check.community_id,
                        },
                    }
                    for error in res.errors
                ]
                errors.extend(check_errors)

                latest_check = (
                    CheckRun.query.filter(
                        CheckRun.config_id == check.id,
                        CheckRun.record_id == record.id,
                        CheckRun.is_draft.is_(True),
                    )
                    .order_by(CheckRun.start_time.desc())
                    .first()
                )

                # FIXME: We should use service
                if not latest_check:
                    new_check_run = CheckRun(
                        config_id=check.id,
                        record_id=record.id,
                        is_draft=record.is_draft,
                        revision_id=record.revision_id,
                        start_time=start_time,
                        end_time=datetime.now(timezone.utc),
                        status=CheckRunStatus.COMPLETED,
                        state="",
                        result=res.to_dict(),
                    )

                    db.session.add(new_check_run)
                else:
                    latest_check.is_draft = record.is_draft
                    latest_check.revision_id = record.revision_id
                    latest_check.start_time = start_time
                    latest_check.end_time = datetime.now(timezone.utc)
                    latest_check.start_time = start_time
                    latest_check.result = res.to_dict()

                self.uow.register(ParentRecordCommitOp(record))
            except Exception as e:
                errors.append(
                    {
                        "message": f"Error running check {check.id}: {str(e)}",
                        "path": check.id,
                    }
                )

    update_draft = _run_checks
    create = _run_checks
