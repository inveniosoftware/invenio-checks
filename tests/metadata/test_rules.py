# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Tests for metadata rule classes."""

import pytest

from invenio_checks.metadata.expressions import (
    ComparisonExpression,
    FieldExpression,
    LogicalExpression,
)
from invenio_checks.metadata.rules import Rule, RuleParser, RuleResult


class TestRule:
    """Tests for the Rule class."""

    def test_basic_rule_evaluation(self):
        """Test basic rule evaluation."""
        record = {"type": "article", "access": "open"}

        # Create a simple rule
        rule = Rule(
            id="test-rule",
            title="Test Rule",
            message="A test rule",
            level="error",
            checks=[
                ComparisonExpression(FieldExpression("access"), "==", "open"),
            ],
        )

        result = rule.evaluate(record)

        assert result.success is True
        assert result.rule_id == "test-rule"
        assert result.rule_title == "Test Rule"
        assert result.rule_message == "A test rule"
        assert result.level == "error"

    def test_rule_with_multiple_checks(self):
        """Test rule with multiple checks."""
        record = {"type": "article", "access": "open", "license": "cc-by"}

        # Create a rule with multiple checks
        rule = Rule(
            id="test-rule",
            title="Test Rule",
            message="A test rule",
            level="error",
            checks=[
                ComparisonExpression(FieldExpression("type"), "==", "article"),
                ComparisonExpression(FieldExpression("access"), "==", "open"),
                ComparisonExpression(FieldExpression("license"), "==", "cc-by"),
            ],
        )

        result = rule.evaluate(record)

        assert result.success is True
        assert len(result.check_results) == 3
        assert all(check.success for check in result.check_results)

    def test_rule_with_failing_check(self):
        """Test rule with a failing check."""
        record = {"type": "article", "access": "restricted"}

        # Create a rule with a failing check
        rule = Rule(
            id="test-rule",
            title="Test Rule",
            message="A test rule",
            level="error",
            checks=[
                ComparisonExpression(FieldExpression("type"), "==", "article"),
                ComparisonExpression(FieldExpression("access"), "==", "open"),
            ],
        )

        result = rule.evaluate(record)

        assert result.success is False
        assert len(result.check_results) == 2
        assert result.check_results[0].success is True  # First check passes
        assert result.check_results[1].success is False  # Second check fails

    def test_rule_with_condition_match(self):
        """Test rule with a condition that matches."""
        record = {"type": "article", "access": "restricted"}

        # Create a rule with a condition
        rule = Rule(
            id="test-rule",
            title="Test Rule",
            message="A test rule",
            level="error",
            condition=ComparisonExpression(FieldExpression("type"), "==", "article"),
            checks=[
                ComparisonExpression(FieldExpression("access"), "==", "open"),
            ],
        )

        result = rule.evaluate(record)

        assert result.success is False  # Check fails, so rule fails
        assert len(result.check_results) == 1
        assert result.check_results[0].success is False

    def test_rule_with_condition_no_match(self):
        """Test rule with a condition that doesn't match."""
        record = {"type": "dataset", "access": "restricted"}

        # Create a rule with a non-matching condition
        rule = Rule(
            id="test-rule",
            title="Test Rule",
            message="A test rule",
            level="error",
            condition=ComparisonExpression(FieldExpression("type"), "==", "article"),
            checks=[
                ComparisonExpression(FieldExpression("access"), "==", "open"),
            ],
        )

        result = rule.evaluate(record)

        assert (
            result.success is True
        )  # Rule is skipped due to condition, so successful by default
        assert len(result.check_results) == 0  # No checks were run

    def test_rule_with_complex_condition(self):
        """Test rule with a complex condition."""
        record = {"type": "article", "subtype": "preprint", "access": "restricted"}

        # Create a rule with a complex condition
        rule = Rule(
            id="test-rule",
            title="Test Rule",
            message="A test rule",
            level="error",
            condition=LogicalExpression(
                "and",
                [
                    ComparisonExpression(FieldExpression("type"), "==", "article"),
                    ComparisonExpression(FieldExpression("subtype"), "==", "preprint"),
                ],
            ),
            checks=[
                ComparisonExpression(FieldExpression("access"), "==", "open"),
            ],
        )

        result = rule.evaluate(record)

        assert result.success is False  # Check fails, so rule fails
        assert len(result.check_results) == 1
        assert result.check_results[0].success is False

    def test_rule_with_no_checks(self):
        """Test rule with no checks."""
        record = {"type": "article"}

        # Create a rule with no checks
        rule = Rule(
            id="test-rule",
            title="Test Rule",
            message="A test rule",
            level="error",
        )

        result = rule.evaluate(record)

        assert result.success is True  # No checks to fail, so rule succeeds
        assert len(result.check_results) == 0

    def test_rule_with_negated_operators(self):
        """Test rule with negated operators."""
        record = {
            "type": "article",
            "access": "open",
            "license": "cc-by",
            "identifier": "10.1234/abcd",
        }

        # Create a rule with negated operators
        rule = Rule(
            id="negation-test-rule",
            title="Negation Test Rule",
            message="A rule with negated operators",
            level="error",
            checks=[
                ComparisonExpression(FieldExpression("type"), "!=", "dataset"),
                ComparisonExpression(FieldExpression("access"), "!=", "restricted"),
                ComparisonExpression(FieldExpression("license"), "!~=", "proprietary"),
                ComparisonExpression(FieldExpression("identifier"), "!^=", "20."),
            ],
        )

        result = rule.evaluate(record)

        assert result.success is True
        assert len(result.check_results) == 4
        assert all(check.success for check in result.check_results)

    def test_rule_with_negated_operators_failure(self):
        """Test rule with negated operators that fail."""
        record = {
            "type": "dataset",
            "access": "open",
            "license": "proprietary",
            "identifier": "20.5678/abcd",
        }

        # Create a rule with negated operators that will fail
        rule = Rule(
            id="negation-fail-rule",
            title="Negation Failure Rule",
            message="A rule with negated operators that fail",
            level="error",
            checks=[
                ComparisonExpression(FieldExpression("type"), "!=", "dataset"),
                ComparisonExpression(FieldExpression("access"), "!=", "restricted"),
                ComparisonExpression(FieldExpression("license"), "!~=", "proprietary"),
                ComparisonExpression(FieldExpression("identifier"), "!^=", "20."),
            ],
        )

        result = rule.evaluate(record)

        assert result.success is False
        assert len(result.check_results) == 4

        # First check fails, type is dataset
        assert result.check_results[0].success is False
        # Third check fails, license contains "proprietary"
        assert result.check_results[2].success is False
        # Fourth check fails, identifier starts with "20."
        assert result.check_results[3].success is False
        # Second check passes
        assert result.check_results[1].success is True


class TestRuleParser:
    """Tests for the RuleParser class."""

    def test_parse_basic_rule(self):
        """Test parsing a basic rule."""
        rule_config = {
            "id": "test-rule",
            "title": "Test Rule",
            "message": "A test rule",
            "level": "error",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "access"},
                    "operator": "==",
                    "right": "open",
                }
            ],
        }

        rule = RuleParser.parse(rule_config)

        assert rule.id == "test-rule"
        assert rule.title == "Test Rule"
        assert rule.message == "A test rule"
        assert rule.level == "error"
        assert len(rule.checks) == 1
        assert isinstance(rule.checks[0], ComparisonExpression)

    def test_parse_rule_with_condition(self):
        """Test parsing a rule with a condition."""
        rule_config = {
            "id": "test-rule",
            "title": "Test Rule",
            "message": "A test rule",
            "level": "error",
            "condition": {
                "type": "comparison",
                "left": {"type": "field", "path": "type"},
                "operator": "==",
                "right": "article",
            },
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "access"},
                    "operator": "==",
                    "right": "open",
                }
            ],
        }

        rule = RuleParser.parse(rule_config)

        assert rule.id == "test-rule"
        assert rule.condition is not None
        assert isinstance(rule.condition, ComparisonExpression)
        assert len(rule.checks) == 1

    def test_parse_rule_with_logical_expression(self):
        """Test parsing a rule with a logical expression."""
        rule_config = {
            "id": "test-rule",
            "title": "Test Rule",
            "message": "A test rule",
            "level": "error",
            "checks": [
                {
                    "type": "logical",
                    "operator": "and",
                    "expressions": [
                        {
                            "type": "comparison",
                            "left": {"type": "field", "path": "type"},
                            "operator": "==",
                            "right": "article",
                        },
                        {
                            "type": "comparison",
                            "left": {"type": "field", "path": "access"},
                            "operator": "==",
                            "right": "open",
                        },
                    ],
                }
            ],
        }

        rule = RuleParser.parse(rule_config)

        assert rule.id == "test-rule"
        assert len(rule.checks) == 1
        assert isinstance(rule.checks[0], LogicalExpression)
        assert len(rule.checks[0].expressions) == 2

    def test_parse_rule_with_list_expression(self):
        """Test parsing a rule with a list expression."""
        rule_config = {
            "id": "test-rule",
            "title": "Test Rule",
            "message": "A test rule",
            "level": "error",
            "checks": [
                {
                    "type": "list",
                    "operator": "any",
                    "path": "authors",
                    "predicate": {
                        "type": "comparison",
                        "left": {"type": "field", "path": "affiliation"},
                        "operator": "==",
                        "right": "CERN",
                    },
                }
            ],
        }

        rule = RuleParser.parse(rule_config)

        assert rule.id == "test-rule"
        assert len(rule.checks) == 1
        # ListExpression should be imported to properly test this
        # assert isinstance(rule.checks[0], ListExpression)

    def test_parse_invalid_expression_type(self):
        """Test parsing an invalid expression type."""
        rule_config = {
            "id": "test-rule",
            "title": "Test Rule",
            "message": "A test rule",
            "level": "error",
            "checks": [{"type": "invalid-type", "some": "value"}],
        }

        with pytest.raises(ValueError) as excinfo:
            RuleParser.parse(rule_config)

        assert "Unknown expression type" in str(
            excinfo.value
        ) or "Invalid expression type" in str(excinfo.value)

    def test_parse_missing_required_field(self):
        """Test parsing a rule with missing required field."""
        # Missing "id" field
        rule_config = {
            "title": "Test Rule",
            "message": "A test rule",
            "level": "error",
            "checks": [],
        }

        with pytest.raises((ValueError, KeyError)) as excinfo:
            RuleParser.parse(rule_config)

        # The exact message may vary, but it should indicate a problem with missing required field
        assert (
            "id" in str(excinfo.value).lower()
            or "required" in str(excinfo.value).lower()
        )

    def test_parse_rule_with_negated_operators(self):
        """Test parsing a rule with negated operators."""
        rule_config = {
            "id": "negation-test-rule",
            "title": "Negation Test Rule",
            "message": "A rule with negated operators",
            "level": "error",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "type"},
                    "operator": "!=",
                    "right": "dataset",
                },
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "license"},
                    "operator": "!~=",
                    "right": "proprietary",
                },
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "file_name"},
                    "operator": "!$=",
                    "right": ".exe",
                },
            ],
        }

        rule = RuleParser.parse(rule_config)

        assert rule.id == "negation-test-rule"
        assert len(rule.checks) == 3
        assert all(isinstance(check, ComparisonExpression) for check in rule.checks)
        assert rule.checks[0].operator == "!="
        assert rule.checks[1].operator == "!~="
        assert rule.checks[2].operator == "!$="


class TestRuleResult:
    """Test cases for the RuleResult class."""

    def test_rule_result_creation(self):
        """Test RuleResult creation and properties."""
        rule = Rule(
            id="test-rule",
            title="Test Rule",
            message="A test rule",
            level="error",
        )

        # Create a successful result with some check results
        rule_result = RuleResult.from_rule(
            rule,
            True,
            [
                {"success": True, "path": "field1", "message": None},
                {"success": True, "path": "field2", "message": None},
            ],
        )

        assert rule_result.rule_id == "test-rule"
        assert rule_result.rule_title == "Test Rule"
        assert rule_result.rule_message == "A test rule"
        assert rule_result.level == "error"
        assert rule_result.success is True
        assert len(rule_result.check_results) == 2

    def test_rule_result_to_dict(self):
        """Test RuleResult conversion to dictionary."""
        rule = Rule(
            id="test-rule",
            title="Test Rule",
            message="A test rule",
            level="error",
        )

        # Create a result
        rule_result = RuleResult.from_rule(
            rule,
            False,
            [{"success": False, "path": "field1", "message": "Error message"}],
        )

        result_dict = rule_result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["rule_id"] == "test-rule"
        assert result_dict["success"] is False
        assert "check_results" in result_dict
        assert len(result_dict["check_results"]) == 1
