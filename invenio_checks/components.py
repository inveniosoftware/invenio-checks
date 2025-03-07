# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record service component."""

import itertools

from flask import current_app
from invenio_drafts_resources.services.records.components import ServiceComponent

from .models import CheckConfig


class ChecksComponent(ServiceComponent):
    """Checks component."""

    @property
    def enabled(self):
        """Return if checks are enabled."""
        return current_app.config.get("CHECKS_ENABLED", False)

    def update_draft(self, identity, data=None, record=None, errors=None, **kwargs):
        """Update handler."""
        errors = errors or []

        if not self.enabled:
            return

        communities = []
        if record.parent.review and (
            record.parent.review.status == "submitted"
            or record.parent.review.status == "created"
        ):
            # TODO handle multiple requests
            communities.append(record.parent.review.receiver.resolve().id)
        else:
            return

        checks = itertools.chain(
            *[
                CheckConfig.query.filter(CheckConfig.community_id == c).all()
                for c in communities
            ]
        )

        for check in checks:
            try:
                res = check.run(data, record)
                if not res.sync:
                    continue
                for error in res.errors:
                    errors.append(error)
            except Exception as e:
                errors.append(
                    {
                        "message": f"Error running check {check.id}: {str(e)}",
                        "path": check.id,
                    }
                )
