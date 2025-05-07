# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Metadata check expression engine."""

from dataclasses import dataclass, field
from types import GeneratorType
from typing import Optional

from invenio_records.systemfields.relations.results import (
    RelationResult,
)


@dataclass
class ExpressionResult:
    """Represents the result of evaluating an expression."""

    success: bool
    path: Optional[str] = field(default=None)
    value: Optional[str] = field(default=None)
    message: Optional[str] = field(default=None)


class Expression:
    """Base class for all rule expressions."""

    def evaluate(self, record):
        """Evaluate the expression against a record."""
        raise NotImplementedError()


class FieldExpression(Expression):
    """Expression for accessing a field in the record."""

    # Error message templates
    FIELD_MISSING = "Field {path} is required but missing"

    def __init__(self, field_path):
        """Initialize the expression."""
        self.field_path = field_path

    def evaluate(self, record):
        """Access the field from the record."""
        try:
            value = self._get_nested_field(record, self.field_path)
            return ExpressionResult(True, self.field_path, value)
        except (KeyError, IndexError, TypeError):
            return ExpressionResult(
                False,
                self.field_path,
                None,
                self.FIELD_MISSING.format(path=self.field_path),
            )

    def _get_nested_field(self, obj, path):
        """Get a nested field from an object using dot notation."""
        parts = path.split(".")
        for part in parts:
            if isinstance(obj, RelationResult):
                obj = obj()
            if isinstance(obj, GeneratorType):
                obj = list(obj)

            if isinstance(obj, dict):
                if part not in obj:
                    raise KeyError(f"Key '{part}' not found")
                obj = obj[part]
            elif hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, list):
                if not part.isdigit():
                    raise KeyError(f"Invalid list index: {part}")
                idx = int(part)
                if idx >= len(obj):
                    raise IndexError(f"List index out of range: {idx}")
                obj = obj[idx]
            else:
                raise TypeError(f"Cannot access '{part}' on {type(obj)}")
        return obj


class ComparisonExpression(Expression):
    """Expression for comparing values."""

    # Error message templates
    NOT_EQUAL = "Expected {path} to be {expected}, but got {actual}"
    EQUAL = "Expected {path} not to be {unexpected}, but got {actual}"
    NOT_CONTAINS = "Expected {path} to contain {expected}, but got {actual}"
    CONTAINS = "Expected {path} not to contain {unexpected}, but got {actual}"
    NOT_IN = "Expected {expected} in {path}, but got {actual}"
    IN = "Expected {unexpected} to not be in {path}, but got {actual}"

    VALID_OPERATORS = [
        "==",
        "!=",
        "~=",
        "!~=",
        "^=",
        "!^=",
        "$=",
        "!$=",
        "in",
        "not in",
    ]

    def __init__(self, left, operator, right):
        """Initialize the comparison."""
        self.left = left

        if operator not in self.VALID_OPERATORS:
            raise ValueError(
                f"Invalid operator: {operator}. Valid operators are {self.VALID_OPERATORS}"
            )
        self.operator = operator

        self.right = right

    def evaluate(self, record):
        """Evaluate the comparison."""
        # Evaluate the left expression
        left_result = self.left.evaluate(record)
        if not left_result.success:
            return left_result

        # Get the path from the left expression
        path = left_result.path
        left_value = left_result.value

        # Perform the comparison
        if self.operator == "==":
            success = left_value == self.right
            message = (
                None
                if success
                else self.NOT_EQUAL.format(
                    path=path, expected=self.right, actual=left_value
                )
            )
        elif self.operator == "!=":
            success = left_value != self.right
            message = (
                None
                if success
                else self.EQUAL.format(
                    path=path, unexpected=self.right, actual=left_value
                )
            )
        elif self.operator == "~=":
            if isinstance(left_value, (list, dict, str)):
                success = self.right in left_value
                message = (
                    None
                    if success
                    else self.NOT_CONTAINS.format(
                        path=path, expected=self.right, actual=left_value
                    )
                )
            else:
                success = False
                message = f"Cannot check if {type(left_value)} contains a value"
        elif self.operator == "!~=":
            if isinstance(left_value, (list, dict, str)):
                success = self.right not in left_value
                message = (
                    None
                    if success
                    else self.CONTAINS.format(
                        path=path, unexpected=self.right, actual=left_value
                    )
                )
            else:
                success = False
                message = f"Cannot check if {type(left_value)} does not contain a value"
        elif self.operator == "in":
            if isinstance(self.right, (list, dict, str)):
                success = left_value in self.right
                message = (
                    None
                    if success
                    else self.NOT_IN.format(
                        path=path, expected=self.right, actual=left_value
                    )
                )
            else:
                success = False
                message = f"Cannot check if {type(self.right)} contains a value"
        elif self.operator == "not in":
            if isinstance(self.right, (list, dict, str)):
                success = left_value not in self.right
                message = (
                    None
                    if success
                    else self.IN.format(
                        path=path, unexpected=self.right, actual=left_value
                    )
                )
            else:
                success = False
                message = f"Cannot check if {type(self.right)} does not contain a value"
        # Implement other operators as needed
        elif self.operator == "^=":
            if isinstance(left_value, str):
                success = left_value.startswith(self.right)
                message = (
                    None if success else f"Expected {path} to start with {self.right}"
                )
            else:
                success = False
                message = f"Cannot check if {type(left_value)} starts with a value"
        elif self.operator == "!^=":
            if isinstance(left_value, str):
                success = not left_value.startswith(self.right)
                message = (
                    None
                    if success
                    else f"Expected {path} not to start with {self.right}"
                )
            else:
                success = False
                message = (
                    f"Cannot check if {type(left_value)} doesn't start with a value"
                )
        elif self.operator == "$=":
            if isinstance(left_value, str):
                success = left_value.endswith(self.right)
                message = (
                    None if success else f"Expected {path} to end with {self.right}"
                )
            else:
                success = False
                message = f"Cannot check if {type(left_value)} ends with a value"
        elif self.operator == "!$=":
            if isinstance(left_value, str):
                success = not left_value.endswith(self.right)
                message = (
                    None if success else f"Expected {path} not to end with {self.right}"
                )
            else:
                success = False
                message = f"Cannot check if {type(left_value)} doesn't end with a value"
        else:
            success = False
            message = f"Unknown operator: {self.operator}"

        return ExpressionResult(success, path, left_value, message)


class LogicalExpression(Expression):
    """Expression for logical operations (AND, OR)."""

    VALID_OPERATORS = ["and", "or"]

    def __init__(self, operator, expressions):
        """Initialize the logical expression."""
        if operator not in self.VALID_OPERATORS:
            raise ValueError(
                f"Invalid operator: {operator}. Valid operators are {self.VALID_OPERATORS}"
            )
        self.operator = operator
        self.expressions = expressions

    def evaluate(self, record):
        """Evaluate the logical expression."""
        # NOTE: We're not short-circuiting the evaluation so that we can return
        # all failed expressions in the result
        results = [expr.evaluate(record) for expr in self.expressions]

        if self.operator == "and":
            # For AND, success is True only if all expressions succeed
            failures = [r for r in results if not r.success]
            if failures:
                # FIXME: Return all results (requires some refactoring on results)
                return ExpressionResult(False)
            return ExpressionResult(True)
        elif self.operator == "or":
            # For OR, success is True if any expression succeeds
            successes = [r for r in results if r.success]
            if successes:
                # FIXME: Return all results
                return ExpressionResult(True)

            return ExpressionResult(False)
        return ExpressionResult(
            False, message=f"Unknown logical operator: {self.operator}"
        )


class ListExpression(Expression):
    """Expression for handling list fields."""

    # Error message templates
    LIST_MISSING = "List field {path} is missing"
    NOT_A_LIST = "Field {path} is not a list"
    NO_ITEMS = "No items in list {path}"
    NO_ITEMS_MATCH = "No items in {path} match the required criteria"
    NOT_ALL_ITEMS_MATCH = "Not all items in {path} match the required criteria"

    VALID_OPERATORS = ["any", "all", "exists"]

    def __init__(self, operator, path, predicate=None):
        """Initialize the list expression."""
        if operator not in self.VALID_OPERATORS:
            raise ValueError(
                f"Invalid operator: {operator}. Valid operators are {self.VALID_OPERATORS}"
            )
        self.operator = operator
        self.path = path
        if operator != "exists":
            self.predicate = predicate

    def evaluate(self, record):
        """Evaluate the list expression."""
        try:
            list_value = self._get_nested_field(record, self.path)
        except (KeyError, IndexError, TypeError):
            return ExpressionResult(
                False,
                self.path,
                None,
                self.LIST_MISSING.format(path=self.path),
            )

        if not isinstance(list_value, list):
            return ExpressionResult(
                False,
                self.path,
                list_value,
                self.NOT_A_LIST.format(path=self.path),
            )

        if not list_value:
            # Empty list
            if self.operator == "any":
                return ExpressionResult(
                    False,
                    self.path,
                    list_value,
                    self.NO_ITEMS_MATCH.format(path=self.path),
                )
            elif self.operator == "exists":
                return ExpressionResult(
                    False,
                    self.path,
                    list_value,
                    self.NO_ITEMS.format(path=self.path),
                )
            else:  # all
                return ExpressionResult(True, self.path, list_value)

        if self.operator == "exists":
            if len(list_value) > 0:
                return ExpressionResult(True, self.path, list_value)
            else:
                return ExpressionResult(
                    False,
                    self.path,
                    list_value,
                    self.NO_ITEMS.format(path=self.path),
                )

        # Evaluate the predicate against each item
        results = [self.predicate.evaluate(item) for item in list_value]

        if self.operator == "any":
            success = any(r.success for r in results)
            if not success:
                return ExpressionResult(
                    False,
                    self.path,
                    list_value,
                    self.NO_ITEMS_MATCH.format(path=self.path),
                )
        elif self.operator == "all":
            success = all(r.success for r in results)
            if not success:
                return ExpressionResult(
                    False,
                    self.path,
                    list_value,
                    self.NOT_ALL_ITEMS_MATCH.format(path=self.path),
                )

        return ExpressionResult(success, self.path, list_value)

    def _get_nested_field(self, obj, path):
        """Get a nested field from an object using dot notation."""
        parts = path.split(".")
        for part in parts:
            if isinstance(obj, dict):
                if part not in obj:
                    raise KeyError(f"Key '{part}' not found")
                obj = obj[part]
            elif isinstance(obj, list):
                if not part.isdigit():
                    raise KeyError(f"Invalid list index: {part}")
                idx = int(part)
                if idx >= len(obj):
                    raise IndexError(f"List index out of range: {idx}")
                obj = obj[idx]
            else:
                raise TypeError(f"Cannot access '{part}' on {type(obj)}")
        return obj
