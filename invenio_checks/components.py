# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record service component."""

from datetime import datetime

from flask import current_app, g
from invenio_communities.proxies import current_communities
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.uow import ModelCommitOp
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

        community_ids = set()

        # Check draft review request
        if record.parent.review:
            # drafts can only be submitted to one community
            community = record.parent.review.receiver.resolve()
            community_ids.add(str(community.id))
            community_parent_id = community.get("parent", {}).get("id")
            if community_parent_id:
                community_ids.add(community_parent_id)

        # Check inclusion requests
        results = current_requests_service.search(
            identity,
            extra_filter=dsl.query.Bool(
                "must",
                must=[
                    dsl.Q("term", **{"type": "community-inclusion"}),
                    dsl.Q("term", **{"topic.record": record.pid.pid_value}),
                    dsl.Q("term", **{"is_open": True}),
                ],
            ),
        )
        for result in results:
            community_id = result.get("receiver", {}).get("community")
            if community_id:
                community_ids.add(community_id)
                # check if it is a subcommunity
                community = current_communities.service.read(
                    id_=community_id, identity=g.identity
                )
                community_parent_id = community.to_dict().get("parent", {}).get("id")
                if community_parent_id:
                    community_ids.add(community_parent_id)

        # Check already included communities
        for community in record.parent.communities:
            community_ids.add(str(community.id))
            community_parent_id = community.get("parent", {}).get("id")
            if community_parent_id:
                community_ids.add(community_parent_id)

        all_check_configs = CheckConfig.query.filter(
            CheckConfig.community_id.in_(community_ids)
        ).all()
        for check_config in all_check_configs:
            try:
                check_cls = current_checks_registry.get(check_config.check_id)
                start_time = datetime.utcnow()
                res = check_cls().run(record, check_config)
                if not res.sync:
                    continue

                check_errors = [
                    {
                        **error,
                        "context": {"community": check_config.community_id},
                    }
                    for error in res.errors
                ]
                errors.extend(check_errors)

                latest_check = (
                    CheckRun.query.filter(
                        CheckRun.config_id == check_config.id,
                        CheckRun.record_id == record.id,
                        CheckRun.is_draft.is_(True),
                    )
                    .order_by(CheckRun.start_time.desc())
                    .first()
                )

                # FIXME: We should use the service
                if not latest_check:
                    latest_check = CheckRun(
                        config_id=check_config.id,
                        record_id=record.id,
                        is_draft=record.is_draft,
                        revision_id=record.revision_id,
                        start_time=start_time,
                        end_time=datetime.utcnow(),
                        status=CheckRunStatus.COMPLETED,
                        state="",
                        result=res.to_dict(),
                    )
                else:
                    latest_check.is_draft = record.is_draft
                    latest_check.revision_id = record.revision_id
                    latest_check.start_time = start_time
                    latest_check.end_time = datetime.utcnow()
                    latest_check.result = res.to_dict()

                # Create/update the check run to the database
                self.uow.register(ModelCommitOp(latest_check))
            except Exception:
                current_app.logger.exception(
                    "Error running check on record",
                    extra={
                        "record_id": str(record.id),
                        "check_config_id": str(check_config.id),
                    },
                )

    update_draft = _run_checks
    create = _run_checks
