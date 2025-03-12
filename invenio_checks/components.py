# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record service component."""

from flask import current_app
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_requests.proxies import current_requests_service
from invenio_search.engine import dsl

from .models import CheckConfig
from .proxies import current_checks_registry


class ChecksComponent(ServiceComponent):
    """Checks component."""

    @property
    def enabled(self):
        """Return if checks are enabled."""
        return current_app.config.get("CHECKS_ENABLED", False)

    def _run_checks(self, identity, data=None, record=None, errors=None, **kwargs):
        """Update handler."""
        errors = errors or []

        if not self.enabled:
            return

        communities = []
        if record.parent.review and (
            record.parent.review.status == "submitted"
            or record.parent.review.status == "created"
        ):
            # drafts can only be submitted to one community
            communities.append(record.parent.review.receiver.resolve().id)
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
                    communities.append(result.get("receiver", {}).get("community"))
            else:
                return

        all_checks = [
            (CheckConfig.query.filter(CheckConfig.community_id == c).all(), c)
            for c in communities
        ]

        for checks, community in all_checks:
            try:
                for check in checks:
                    check_cls = current_checks_registry.get(check.check_id)
                    res = check_cls().run(record, check.params, community)
                    if not res.sync:
                        continue
                    for error in res.errors:
                        errors.append(*error)
            except Exception as e:
                errors.append(
                    {
                        "message": f"Error running check {check.id}: {str(e)}",
                        "path": check.id,
                    }
                )

    update_draft = _run_checks
    create = _run_checks
