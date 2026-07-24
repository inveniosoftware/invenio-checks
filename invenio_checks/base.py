# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT
"""Check implementations and registry."""

from dataclasses import asdict, dataclass, field
from typing import Dict, List

from invenio_base.utils import entry_points


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

    def run(self, record, config):
        """Run the check on a record with the given configuration."""
        raise NotImplementedError()


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

    def pending_result(self, params):
        """Return the initial result dict stored while the check is pending."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
        }
