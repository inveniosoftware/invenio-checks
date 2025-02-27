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
        if record.review.is_open:
            communities.append(record.review.community)

        communities.extend(record.parent.communities.entries)
        checks = itertools.chain(*[c.checks for c in communities])

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
