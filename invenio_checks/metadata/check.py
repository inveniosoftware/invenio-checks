# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Metadata check implementation."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List

from ..base import Check
from .rules import RuleParser, RuleResult


@dataclass
class CheckResult:
    """Result of running a check."""

    check_id: str
    success: bool = True
    rule_results: List[RuleResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sync: bool = True  # Default to synchronous
    errors: List[Dict] = field(default_factory=list)

    def add_rule_result(self, rule_result: RuleResult):
        """Add a rule result and update the overall success."""
        self.rule_results.append(rule_result)
        if not rule_result.success and rule_result.level == "failure":
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
    title = "Metadata Validation"
    description = "Validates record metadata against configured rules."

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

    def run(self, record, config):
        """Run the metadata check on a record with the given configuration."""
        # Create a check result
        result = CheckResult(self.id)

        # Parse the rules from the configuration
        rules = []
        for rule_config in config.get("rules", []):
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
                "field": check.path,
                "messages": [rule_result.rule_message],
                "description": rule_result.rule_description,
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
        title = config.get("title", "Unnamed check")
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
        result = CheckResult(self.id)

        # Evaluate each rule
        for rule in self.rules:
            try:
                rule_result = rule.evaluate(record)
                result.add_rule_result(rule_result)
            except Exception:
                pass

        return result
