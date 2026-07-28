# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT
"""Check implementations and registry."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from invenio_base.utils import entry_points
from invenio_communities.proxies import current_communities


@dataclass
class CheckResult:
    """Result of running a check."""

    id: str
    title: str
    description: str
    success: bool = True
    errors: List[Dict] = field(default_factory=list)

    def to_dict(self):
        """Convert the result to a dictionary."""
        return asdict(self)

    def add_errors(self, errors: List[Dict]):
        """Add error messages for the UI."""
        self.errors.extend(errors)


class Check:
    """Base Check class for all curation checks."""

    id: str
    """Unique identifier for the check."""

    title: str
    """Human-readable name."""

    description: str
    """Description of the check's purpose."""

    sync: bool
    """Whether the check should run synchronously"""

    allow_rerun: bool = False
    """Whether the check can be manually re-run by the user."""

    target_type: str
    """Type of item the check runs against (record, user, community, etc)."""

    def validate_config(self, config):
        """Validate the configuration for this check."""
        raise NotImplementedError()

    def run(self, record, config, **kwargs) -> tuple[CheckResult, dict[str, Any]]:
        """Run the check on a record with the given configuration."""
        raise NotImplementedError()

    def pending_result(self, params):
        """Return the initial result dict stored while the check is pending."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
        }

    @classmethod
    def can_rerun(cls, identity, record_id):
        """Check the permissions to rerun the check."""
        raise NotImplementedError()

    def should_rerun(self, record, config, previous_run, **kwargs):
        """Allows a Check class to define whether to rerun a check. True by default."""
        return True


class ChecksRegistry:
    """Registry for check classes."""

    def __init__(self):
        """Initialize the registry."""
        self._checks = {}

    def register(self, check_cls):
        """Register a check class."""
        if not issubclass(check_cls, Check):
            raise TypeError("Class must inherit from Check")

        check_id = check_cls.id
        if not check_id:
            raise ValueError("Check class must define an id")

        if check_id in self._checks:
            raise ValueError(f"Check with id '{check_id}' already registered")

        self._checks[check_id] = check_cls
        return check_cls

    def get(self, check_id):
        """Get a check class by id."""
        check_cls = self._checks.get(check_id)
        if not check_cls:
            raise ValueError(f"No check registered with id '{check_id}'")
        return check_cls

    def get_all(self):
        """Get all registered check classes."""
        return self._checks.copy()

    def load_from_entry_points(self, app, ep_name):
        """Load checks from entry points."""
        for ep in entry_points(group=ep_name):
            check_cls_or_func = ep.load()
            check_cls = check_cls_or_func

            self.register(check_cls)


class CheckTarget:
    """Base CheckTarget class for all curation check targers."""

    id: str
    """Unique identifier for the check target."""

    def resolve(self, check_run):
        """Get the target object for a check target."""
        raise NotImplementedError()


class CheckTargetsRegistry:
    """Registry for CheckTarget classes."""

    def __init__(self):
        """Initialize the registry."""
        self._targets = {}

    def register(self, check_target_cls):
        """Register a CheckTarget class."""
        if not issubclass(check_target_cls, CheckTarget):
            raise TypeError("Class must inherit from CheckTarget")

        check_target_id = check_target_cls.id
        if not check_target_id:
            raise ValueError("CheckTarget class must define an id")

        if check_target_id in self._targets:
            raise ValueError(
                f"CheckTarget with id '{check_target_id}' already registered"
            )

        self._targets[check_target_id] = check_target_cls
        return check_target_cls

    def get(self, check_target_id):
        """Get a check target class by id."""
        check_target_cls = self._targets.get(check_target_id)
        if not check_target_cls:
            raise ValueError(f"No CheckTarget registered with id '{check_target_id}'")
        return check_target_cls

    def get_all(self):
        """Get all registered CheckTarget classes."""
        return self._targets.copy()

    def load_from_entry_points(self, app, ep_name):
        """Load check targets from entry points."""
        for ep in entry_points(group=ep_name):
            check_target_cls = ep.load()
            self.register(check_target_cls)


class CommunityCheckTarget(CheckTarget):
    """CheckTarget class for communities."""

    id = "community"

    def resolve(self, check_run):
        """Get the target object for a community check target."""
        return current_communities.service.record_cls.get_record(check_run.record_id)
