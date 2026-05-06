# SPDX-FileCopyrightText: 2025-2026 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-FileCopyrightText: 2025-2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT
"""Metadata check implementation."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

from invenio_i18n import gettext as _
from invenio_i18n import lazy_gettext as _l

from invenio_checks.base import Check, CheckResult
from invenio_checks.models import CheckConfig
from invenio_checks.utils import translate_field

from .rules import RuleParser, RuleResult


@dataclass
class MetadataCheckResult(CheckResult):
    """Result of running a check."""

    rule_results: List[RuleResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_rule_result(self, rule_result: RuleResult):
        """Add a rule result and update the overall success."""
        self.rule_results.append(rule_result)
        if rule_result.success and rule_result.level == "failure":
            self.success = False

    def add_errors(self, errors: List[Dict]):
        """Add error messages for the UI."""
        self.errors.extend(errors)

    def to_dict(self):
        """Convert the result to a dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


class MetadataCheck(Check):
    """Check for validating record metadata against configured rules."""

    id = "metadata"
    title = _l("Metadata validation")
    description = _l("Validates record metadata against configured rules.")
    sort_order = 10
    sync = True

    def validate_config(self, config):
        """Validate the configuration for this metadata check."""
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        rules = config.get("rules")
        if not rules or not isinstance(rules, list):
            raise ValueError("Configuration must contain a 'rules' list")

        # Try to parse each rule to validate it
        for rule_config in rules:
            try:
                RuleParser.parse(rule_config)
            except (KeyError, ValueError) as e:
                raise ValueError(f"Invalid rule configuration: {str(e)}")

        return True

    def run(self, record, config: CheckConfig):
        """Run the metadata check on a record with the given configuration."""
        # Create a check result
        result = MetadataCheckResult(
            self.id, title=self.title, description=self.description
        )

        # Parse the rules from the configuration
        rules = []
        for rule_config in config.params.get("rules", []):
            try:
                rule = RuleParser.parse(rule_config)
                rules.append(rule)
            except Exception:
                # Skip this rule
                continue

        # If we have no valid rules, return early
        if not rules:
            return result

        # Evaluate each rule
        for rule in rules:
            try:
                rule_result = rule.evaluate(record)
                errors = self.to_service_errors(rule_result)
                result.add_rule_result(rule_result)
                result.add_errors(errors)
            except Exception:
                pass

        return result

    def to_service_errors(self, rule_result: RuleResult) -> List[Dict]:
        """Create error messages for the UI."""
        if rule_result.success:
            return []

        output = [
            {
                "field": rule_result.error_path or check.path,
                "messages": [translate_field(rule_result.rule_message)],
                "description": translate_field(rule_result.rule_description),
                "severity": rule_result.level,
            }
            for check in rule_result.check_results
        ]

        return output


class MetadataCheckConfig:
    """Configuration for a metadata check."""

    def __init__(self, id, title, description, rules=None):
        """Initialize the check configuration."""
        self.id = id
        self.title = title
        self.description = description
        self.rules = rules or []

    @classmethod
    def from_dict(cls, config):
        """Create a check configuration from a dictionary."""
        check_id = config.get("id")
        title = config.get("title", _("Unnamed check"))
        description = config.get("description", "")

        # Parse rules
        rules = []
        for rule_config in config.get("rules", []):
            rule = RuleParser.parse(rule_config)
            rules.append(rule)

        return cls(check_id, title, description, rules)

    def evaluate(self, record):
        """Evaluate the check against a record."""
        # Create a check result
        result = MetadataCheckResult(
            self.id, title=self.title, description=self.description
        )

        # Evaluate each rule
        for rule in self.rules:
            try:
                rule_result = rule.evaluate(record)
                result.add_rule_result(rule_result)
            except Exception:
                pass

        return result
