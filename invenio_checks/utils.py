# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Utilities."""

import functools

from flask import current_app, g
from invenio_communities.proxies import current_communities
from invenio_rdm_records.requests import CommunityInclusion, CommunitySubmission
from sqlalchemy import case


class classproperty:
    """Decorator to define a class property."""

    def __init__(self, func) -> None:
        """Initialize the class property decorator."""
        functools.update_wrapper(self, func)

    def __get__(self, _, owner):
        """Get the class property value."""
        return self.__wrapped__(owner)


def resolve_checks(record_uuid, request, community=None):
    """Resolve the checks for this draft/record related to the community and the request."""

    # Early exit if checks are not enabled.
    enabled = current_app.config.get("CHECKS_ENABLED", False)

    if not enabled:
        return None

    # Early exit if not draft submission nor record inclusion
    request_type = request["type"]
    is_draft_submission = request_type == CommunitySubmission.type_id
    is_record_inclusion = request_type == CommunityInclusion.type_id

    if not is_draft_submission and not is_record_inclusion:
        return None

    # Early exit if there is no record UUID (for instance for some closed requests)
    if not record_uuid:
        return None

    # Resolve the target community from the request if the community was not passed as an argument
    if not community:
        community_uuid = request["receiver"]["community"]
        community = current_communities.service.read(
            id_=community_uuid, identity=g.identity
        )

    # Collect the community UUID and the potential parent community UUID
    communities = []
    community_parent_id = community.to_dict().get("parent", {}).get("id")
    if community_parent_id:
        # Add the parent community first for later ordering of check configs
        communities.append(community_parent_id)
    communities.append(community.id)

    # Early exit if no check config found for the communities
    from invenio_checks.models import CheckConfig, CheckRun

    check_configs = (
        CheckConfig.query.filter(CheckConfig.community_id.in_(communities))
        .order_by(
            # Order by the communities (parent first if any) and then by check IDs for deterministic ordering
            case((CheckConfig.community_id == communities[0], 0), else_=1),
            CheckConfig.check_id,
        )
        .all()
    )

    if not check_configs:
        return None

    # Find check runs for the given check configs
    check_config_ids = [check_config.id for check_config in check_configs]
    checks = CheckRun.query.filter(
        CheckRun.config_id.in_(check_config_ids),
        CheckRun.record_id == record_uuid,
    ).all()
    # For a given record, there is one check run corresponding to one check config
    # Order the check runs by the same order as the check configs for deterministic ordering
    checks = sorted(checks, key=lambda check: check_config_ids.index(check.config_id))

    return checks
