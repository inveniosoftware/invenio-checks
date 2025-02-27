# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Metadata check rules."""

from .expressions import (
    ComparisonExpression,
    FieldExpression,
    ListExpression,
    LogicalExpression,
)


class Rule:
    """Class representing a metadata validation rule."""

    def __init__(self, id, title, description, level, condition=None, checks=None):
        """Initialize the rule."""
        self.id = id
        self.title = title
        self.description = description
        self.level = level
        self.condition = condition
        self.checks = checks or []

    def evaluate(self, record):
        """Evaluate the rule against a record."""
        # If there's a condition, evaluate it first
        if self.condition:
            condition_result = self.condition.evaluate(record)
            if not condition_result.success:
                # Condition failed, rule doesn't apply
                return RuleResult(self, True, [])

        # Evaluate all checks
        check_results = [check.evaluate(record) for check in self.checks]

        # Create the rule result
        return RuleResult(self, all(r.success for r in check_results), check_results)


class RuleResult:
    """Class representing the result of evaluating a rule."""

    def __init__(self, rule, success, check_results):
        """Initialize the rule result."""
        self.rule_id = rule.id
        self.rule_title = rule.title
        self.rule_description = rule.description
        self.level = rule.level
        self.success = success
        self.check_results = check_results

    def to_dict(self):
        """Convert the result to a dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_title": self.rule_title,
            "rule_description": self.rule_description,
            "level": self.level,
            "success": self.success,
            "check_results": self.check_results,
        }


class ExpressionParser:
    """Parser for expression configuration."""

    @classmethod
    def parse(cls, config):
        """Parse an expression configuration into an Expression object."""
        expr_type = config.get("type")

        if expr_type == "field":
            return FieldExpression(config["path"])

        elif expr_type == "comparison":
            left = cls.parse(config["left"])
            operator = config["operator"]
            right = config["right"]
            return ComparisonExpression(left, operator, right)

        elif expr_type == "logical":
            operator = config["operator"]
            expressions = [cls.parse(e) for e in config["expressions"]]
            return LogicalExpression(operator, expressions)

        elif expr_type == "list":
            operator = config["operator"]
            list_path = config["list_path"]
            predicate = cls.parse(config["predicate"])
            return ListExpression(operator, list_path, predicate)

        raise ValueError(f"Unknown expression type: {expr_type}")


class RuleParser:
    """Parser for rule configuration."""

    @classmethod
    def parse(cls, config):
        """Parse a rule configuration into a Rule object."""
        # Validate required fields
        if "id" not in config:
            raise ValueError("Rule configuration missing required field: 'id'")

        rule_id = config.get("id")
        title = config.get("title", "Unnamed rule")
        description = config.get("description", "")
        level = config.get("level", "info")

        # Parse condition if present
        condition = None
        if "condition" in config:
            condition = ExpressionParser.parse(config["condition"])

        # Parse checks
        checks = []
        for check_config in config.get("checks", []):
            check = ExpressionParser.parse(check_config)
            checks.append(check)

        return Rule(rule_id, title, description, level, condition, checks)
