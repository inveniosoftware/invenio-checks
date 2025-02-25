import itertools

from flask import current_app
from invenio_drafts_resources.services.records.components import ServiceComponent


class ChecksComponent(ServiceComponent):
    @property
    def enabled(self):
        return current_app.config.get("CHECKS_ENABLED", False)

    def update_draft(self, identity, draft=None, record=None, errors=None, **kwargs):
        """Update handler."""

        # 1. Check if checks are enabled
        if not self.enabled:
            return

        # 2. Check if it's in review and get all the communities (only in review for the first version)
        communities = []
        if draft.review.is_open:
            communities.append(draft.review.community)

        # 3. Get all checks for each community
        communities.extend(draft.parent.communities.entires)
        checks = itertools.chain([c.checks for c in communities])

        # 4. Run each check
        for check in checks:
            try:
                res = check.run(draft, record)
                if not res.sync:
                    continue
                # 5. For each error, append error to the error list
                for error in res.errors:
                    errors.append(res.error)
            except Exception:
                # log
                pass
