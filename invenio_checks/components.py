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

from .api import CheckRunAPI
from .models import CheckConfig, CheckRun, CheckRunStatus
from .proxies import current_checks_registry


class ChecksComponent(ServiceComponent):
    """Checks component."""

    def read_draft(self, identity, draft=None, errors=None, **kwargs):
        community_ids = CheckRunAPI.get_community_ids(draft, identity)
        check_configs = CheckRunAPI.get_check_configs_from_communities(community_ids)
        for config in check_configs:
            check_run = (
                CheckRun.query.filter(
                    CheckRun.config_id == config.id,
                    CheckRun.record_id == draft.id,
                )
                .order_by(CheckRun.start_time.desc())
                .first()
            )
            if check_run:
                for error in check_run.result.get("errors", []):
                    field = error.get("field")
                    if not field:
                        continue

                    *parents, leaf = field.split(".")
                    current = errors

                    for key in parents:
                        current = current.setdefault(key, {})

                    current[leaf] = {
                        "context": {"community": str(config.community_id)},
                        "description": error.get("description", ""),
                        "message": error.get("messages", []),
                        "severity": error.get("severity", "error"),
                    }

    def update_draft(self, identity, data=None, record=None, errors=None, **kwargs):
        """Run checks on draft update."""
        CheckRunAPI.run_checks(identity, is_draft=True, record=record, errors=errors)
    
    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Run checks on draft create."""
        CheckRunAPI.run_checks(identity, is_draft=True, record=record, errors=errors)
    
    def publish(self, identity, draft=None, record=None):
        """Run checks on publish."""
        CheckRunAPI.delete_check_run(record_uuid=record.id, is_draft=False)
        CheckRunAPI.run_checks(identity, is_draft=False, record=record)

