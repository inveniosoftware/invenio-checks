# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Tests for metadata expression classes."""

import pytest

from invenio_checks.metadata.expressions import (
    ComparisonExpression,
    FieldExpression,
    ListExpression,
    LogicalExpression,
)


class TestFieldExpression:
    """Tests for FieldExpression class."""

    def test_simple_field_access(self):
        """Test accessing simple fields."""
        record = {"title": "Test Record", "year": 2023}
        expr = FieldExpression("title")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "title"
        assert result.value == "Test Record"
        assert result.message is None

    def test_nested_field_access(self):
        """Test accessing nested fields using dot notation."""
        record = {"metadata": {"title": "Test Record", "year": 2023}}
        expr = FieldExpression("metadata.title")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "metadata.title"
        assert result.value == "Test Record"
        assert result.message is None

    def test_deeply_nested_fields(self):
        """Test accessing deeply nested fields."""
        record = {"a": {"b": {"c": {"d": "value"}}}}
        expr = FieldExpression("a.b.c.d")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "a.b.c.d"
        assert result.value == "value"
        assert result.message is None

    def test_list_index_access(self):
        """Test accessing list items by index."""
        record = {"authors": ["Smith", "Johnson", "Williams"]}
        expr = FieldExpression("authors.1")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "authors.1"
        assert result.value == "Johnson"
        assert result.message is None

    def test_nested_list_access(self):
        """Test accessing nested list items."""
        record = {"publications": [{"title": "Paper 1"}, {"title": "Paper 2"}]}
        expr = FieldExpression("publications.1.title")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "publications.1.title"
        assert result.value == "Paper 2"
        assert result.message is None

    def test_missing_field(self):
        """Test behavior when fields are missing."""
        record = {"title": "Test Record"}
        expr = FieldExpression("abstract")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "abstract"
        assert result.value is None
        assert result.message is not None
        assert "missing" in result.message.lower()

    def test_missing_nested_field(self):
        """Test behavior when nested fields are missing."""
        record = {"metadata": {"title": "Test Record"}}
        expr = FieldExpression("metadata.abstract")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "metadata.abstract"
        assert result.value is None
        assert result.message is not None
        assert "missing" in result.message.lower()

    def test_invalid_list_index(self):
        """Test behavior with invalid list index."""
        record = {"authors": ["Smith", "Johnson"]}
        expr = FieldExpression("authors.5")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "authors.5"
        assert result.value is None
        assert result.message is not None
        assert "missing" in result.message.lower()

    def test_invalid_path_type(self):
        """Test behavior when trying to access a property on a non-dict/list."""
        record = {"title": "Test Record"}
        expr = FieldExpression("title.something")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "title.something"
        assert result.value is None
        assert result.message is not None
        assert "missing" in result.message.lower()


class TestComparisonExpression:
    """Tests for ComparisonExpression class."""

    def test_equal_operator_success(self):
        """Test equality operator with success case."""
        record = {"type": "article"}
        expr = ComparisonExpression(FieldExpression("type"), "==", "article")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "type"
        assert result.value == "article"
        assert result.message is None

    def test_equal_operator_failure(self):
        """Test equality operator with failure case."""
        record = {"type": "book"}
        expr = ComparisonExpression(FieldExpression("type"), "==", "article")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "type"
        assert result.value == "book"
        assert result.message is not None
        assert "expected" in result.message.lower()
        assert "article" in result.message.lower()
        assert "book" in result.message.lower()

    def test_not_equal_operator_success(self):
        """Test inequality operator with success case."""
        record = {"type": "book"}
        expr = ComparisonExpression(FieldExpression("type"), "!=", "article")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "type"
        assert result.value == "book"
        assert result.message is None

    def test_not_equal_operator_failure(self):
        """Test inequality operator with failure case."""
        record = {"type": "article"}
        expr = ComparisonExpression(FieldExpression("type"), "!=", "article")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "type"
        assert result.value == "article"
        assert result.message is not None
        assert "not to be" in result.message.lower()
        assert "article" in result.message.lower()

    def test_contains_operator_with_list_success(self):
        """Test contains operator with list success case."""
        record = {"tags": ["open-access", "research", "science"]}
        expr = ComparisonExpression(FieldExpression("tags"), "~=", "research")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "tags"
        assert result.value == ["open-access", "research", "science"]
        assert result.message is None

    def test_contains_operator_with_list_failure(self):
        """Test contains operator with list failure case."""
        record = {"tags": ["open-access", "research", "science"]}
        expr = ComparisonExpression(FieldExpression("tags"), "~=", "education")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "tags"
        assert result.message is not None
        assert "contain" in result.message.lower()
        assert "education" in result.message.lower()

    def test_not_contains_operator_with_list_success(self):
        """Test not-contains operator with list success case."""
        record = {"tags": ["open-access", "research", "science"]}
        expr = ComparisonExpression(FieldExpression("tags"), "!~=", "education")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "tags"
        assert result.value == ["open-access", "research", "science"]
        assert result.message is None

    def test_not_contains_operator_with_list_failure(self):
        """Test not-contains operator with list failure case."""
        record = {"tags": ["open-access", "research", "science"]}
        expr = ComparisonExpression(FieldExpression("tags"), "!~=", "research")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "tags"
        assert result.message is not None
        assert "not to contain" in result.message.lower()
        assert "research" in result.message.lower()

    def test_contains_operator_with_string_success(self):
        """Test contains operator with string success case."""
        record = {"description": "This is an open-access publication"}
        expr = ComparisonExpression(FieldExpression("description"), "~=", "open-access")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "description"
        assert result.message is None

    def test_contains_operator_with_string_failure(self):
        """Test contains operator with string failure case."""
        record = {"description": "This is a publication"}
        expr = ComparisonExpression(FieldExpression("description"), "~=", "open-access")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "description"
        assert result.message is not None
        assert "contain" in result.message.lower()

    def test_not_contains_operator_with_string_success(self):
        """Test not-contains operator with string success case."""
        record = {"description": "This is a publication"}
        expr = ComparisonExpression(
            FieldExpression("description"), "!~=", "open-access"
        )
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "description"
        assert result.message is None

    def test_not_contains_operator_with_string_failure(self):
        """Test not-contains operator with string failure case."""
        record = {"description": "This is an open-access publication"}
        expr = ComparisonExpression(
            FieldExpression("description"), "!~=", "open-access"
        )
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "description"
        assert result.message is not None
        assert "not to contain" in result.message.lower()

    def test_contains_operator_with_invalid_type(self):
        """Test contains operator with invalid type."""
        record = {"count": 42}
        expr = ComparisonExpression(FieldExpression("count"), "~=", "2")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "count"
        assert result.message is not None
        assert "cannot check if" in result.message.lower()

    def test_not_contains_operator_with_invalid_type(self):
        """Test not-contains operator with invalid type."""
        record = {"count": 42}
        expr = ComparisonExpression(FieldExpression("count"), "!~=", "2")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "count"
        assert result.message is not None
        assert "cannot check if" in result.message.lower()

    def test_startswith_operator_success(self):
        """Test startswith operator with success case."""
        record = {"identifier": "10.1234/abcd"}
        expr = ComparisonExpression(FieldExpression("identifier"), "^=", "10.1234")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "identifier"
        assert result.message is None

    def test_startswith_operator_failure(self):
        """Test startswith operator with failure case."""
        record = {"identifier": "10.5678/abcd"}
        expr = ComparisonExpression(FieldExpression("identifier"), "^=", "10.1234")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "identifier"
        assert result.message is not None
        assert "start with" in result.message.lower()

    def test_not_startswith_operator_success(self):
        """Test not-startswith operator with success case."""
        record = {"identifier": "10.5678/abcd"}
        expr = ComparisonExpression(FieldExpression("identifier"), "!^=", "10.1234")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "identifier"
        assert result.message is None

    def test_not_startswith_operator_failure(self):
        """Test not-startswith operator with failure case."""
        record = {"identifier": "10.1234/abcd"}
        expr = ComparisonExpression(FieldExpression("identifier"), "!^=", "10.1234")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "identifier"
        assert result.message is not None
        assert "not to start with" in result.message.lower()

    def test_endswith_operator_success(self):
        """Test endswith operator with success case."""
        record = {"file_name": "document.pdf"}
        expr = ComparisonExpression(FieldExpression("file_name"), "$=", ".pdf")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "file_name"
        assert result.message is None

    def test_endswith_operator_failure(self):
        """Test endswith operator with failure case."""
        record = {"file_name": "document.doc"}
        expr = ComparisonExpression(FieldExpression("file_name"), "$=", ".pdf")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "file_name"
        assert result.message is not None
        assert "end with" in result.message.lower()

    def test_not_endswith_operator_success(self):
        """Test not-endswith operator with success case."""
        record = {"file_name": "document.doc"}
        expr = ComparisonExpression(FieldExpression("file_name"), "!$=", ".pdf")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "file_name"
        assert result.message is None

    def test_not_endswith_operator_failure(self):
        """Test not-endswith operator with failure case."""
        record = {"file_name": "document.pdf"}
        expr = ComparisonExpression(FieldExpression("file_name"), "!$=", ".pdf")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "file_name"
        assert result.message is not None
        assert "not to end with" in result.message.lower()

    def test_startswith_endswith_with_invalid_type(self):
        """Test startswith/endswith operators with invalid type."""
        record = {"count": 42}
        expr1 = ComparisonExpression(FieldExpression("count"), "^=", "4")
        expr2 = ComparisonExpression(FieldExpression("count"), "$=", "2")

        result1 = expr1.evaluate(record)
        result2 = expr2.evaluate(record)

        assert result1.success is False
        assert result2.success is False
        assert result1.message is not None
        assert result2.message is not None
        assert "cannot check if" in result1.message.lower()
        assert "cannot check if" in result2.message.lower()

    def test_not_startswith_endswith_with_invalid_type(self):
        """Test not-startswith/not-endswith operators with invalid type."""
        record = {"count": 42}
        expr1 = ComparisonExpression(FieldExpression("count"), "!^=", "4")
        expr2 = ComparisonExpression(FieldExpression("count"), "!$=", "2")

        result1 = expr1.evaluate(record)
        result2 = expr2.evaluate(record)

        assert result1.success is False
        assert result2.success is False
        assert result1.message is not None
        assert result2.message is not None
        assert "cannot check if" in result1.message.lower()
        assert "cannot check if" in result2.message.lower()

    def test_comparison_missing_field(self):
        """Test comparison when left-side field is missing."""
        record = {"title": "Test Record"}
        expr = ComparisonExpression(FieldExpression("abstract"), "==", "Abstract text")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "abstract"
        assert result.message is not None
        assert "missing" in result.message.lower()

    def test_invalid_operator(self):
        """Test with invalid operator."""
        record = {"title": "Test Record"}
        with pytest.raises(ValueError) as excinfo:
            ComparisonExpression(FieldExpression("title"), "<>", "Test Record")

        assert "Invalid operator" in str(excinfo.value)


class TestLogicalExpression:
    """Tests for LogicalExpression class."""

    def test_and_operator_all_true(self):
        """Test AND operator with all true expressions."""
        record = {"type": "article", "access": "open"}
        expr = LogicalExpression(
            "and",
            [
                ComparisonExpression(FieldExpression("type"), "==", "article"),
                ComparisonExpression(FieldExpression("access"), "==", "open"),
            ],
        )
        result = expr.evaluate(record)

        assert result.success is True

    def test_and_operator_one_false(self):
        """Test AND operator with one false expression."""
        record = {"type": "book", "access": "open"}
        expr = LogicalExpression(
            "and",
            [
                ComparisonExpression(FieldExpression("type"), "==", "article"),
                ComparisonExpression(FieldExpression("access"), "==", "open"),
            ],
        )
        result = expr.evaluate(record)

        assert result.success is False

    def test_and_operator_all_false(self):
        """Test AND operator with all false expressions."""
        record = {"type": "book", "access": "restricted"}
        expr = LogicalExpression(
            "and",
            [
                ComparisonExpression(FieldExpression("type"), "==", "article"),
                ComparisonExpression(FieldExpression("access"), "==", "open"),
            ],
        )
        result = expr.evaluate(record)

        assert result.success is False

    def test_or_operator_all_true(self):
        """Test OR operator with all true expressions."""
        record = {"type": "article", "license": "cc-by"}
        expr = LogicalExpression(
            "or",
            [
                ComparisonExpression(FieldExpression("type"), "==", "article"),
                ComparisonExpression(FieldExpression("license"), "==", "cc-by"),
            ],
        )
        result = expr.evaluate(record)

        assert result.success is True

    def test_or_operator_one_true(self):
        """Test OR operator with one true expression."""
        record = {"type": "book", "license": "cc-by"}
        expr = LogicalExpression(
            "or",
            [
                ComparisonExpression(FieldExpression("type"), "==", "article"),
                ComparisonExpression(FieldExpression("license"), "==", "cc-by"),
            ],
        )
        result = expr.evaluate(record)

        assert result.success is True

    def test_or_operator_all_false(self):
        """Test OR operator with all false expressions."""
        record = {"type": "book", "license": "proprietary"}
        expr = LogicalExpression(
            "or",
            [
                ComparisonExpression(FieldExpression("type"), "==", "article"),
                ComparisonExpression(FieldExpression("license"), "==", "cc-by"),
            ],
        )
        result = expr.evaluate(record)

        assert result.success is False

    def test_nested_logical_expressions(self):
        """Test complex nested logical expressions."""
        record = {
            "type": "article",
            "access": "open",
            "license": "cc-by",
            "reviewed": True,
        }

        # (type == article AND access == open) OR (license == cc-by AND reviewed == True)
        expr = LogicalExpression(
            "or",
            [
                LogicalExpression(
                    "and",
                    [
                        ComparisonExpression(FieldExpression("type"), "==", "article"),
                        ComparisonExpression(FieldExpression("access"), "==", "open"),
                    ],
                ),
                LogicalExpression(
                    "and",
                    [
                        ComparisonExpression(FieldExpression("license"), "==", "cc-by"),
                        ComparisonExpression(FieldExpression("reviewed"), "==", True),
                    ],
                ),
            ],
        )
        result = expr.evaluate(record)

        assert result.success is True

    def test_empty_expressions_list(self):
        """Test logical operators with empty expression lists."""
        record = {"type": "article"}

        and_expr = LogicalExpression("and", [])
        or_expr = LogicalExpression("or", [])

        and_result = and_expr.evaluate(record)
        or_result = or_expr.evaluate(record)

        assert and_result.success is True  # Empty AND is true
        assert or_result.success is False  # Empty OR is false

    def test_logical_expression_invalid_operator(self):
        """Test with invalid logical operator."""
        with pytest.raises(ValueError) as excinfo:
            LogicalExpression(
                "xor",
                [
                    ComparisonExpression(FieldExpression("type"), "==", "article"),
                ],
            )

        assert "Invalid operator" in str(excinfo.value)

    def test_logical_expression_error_message_propagation(self):
        """Test proper error message propagation in logical expressions."""
        record = {"type": "article"}
        expr = LogicalExpression(
            "and",
            [
                ComparisonExpression(FieldExpression("type"), "==", "article"),
                ComparisonExpression(FieldExpression("missing_field"), "==", "value"),
            ],
        )
        result = expr.evaluate(record)

        assert result.success is False


class TestListExpression:
    """Tests for ListExpression class."""

    def test_any_operator_with_match(self):
        """Test 'any' operator with matching predicate."""
        record = {
            "authors": [
                {"name": "Smith", "affiliation": "University A"},
                {"name": "Johnson", "affiliation": "University B"},
            ]
        }

        expr = ListExpression(
            "any",
            "authors",
            ComparisonExpression(FieldExpression("affiliation"), "==", "University B"),
        )
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "authors"

    def test_any_operator_without_match(self):
        """Test 'any' operator with no matching predicate."""
        record = {
            "authors": [
                {"name": "Smith", "affiliation": "University A"},
                {"name": "Johnson", "affiliation": "University B"},
            ]
        }

        expr = ListExpression(
            "any",
            "authors",
            ComparisonExpression(FieldExpression("affiliation"), "==", "University C"),
        )
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "authors"
        assert result.message is not None
        assert "no items" in result.message.lower()
        assert "match" in result.message.lower()

    def test_all_operator_with_all_matching(self):
        """Test 'all' operator with all items matching predicate."""
        record = {
            "files": [
                {"name": "doc1.pdf", "type": "pdf"},
                {"name": "doc2.pdf", "type": "pdf"},
            ]
        }

        expr = ListExpression(
            "all",
            "files",
            ComparisonExpression(FieldExpression("type"), "==", "pdf"),
        )
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "files"

    def test_all_operator_with_some_matching(self):
        """Test 'all' operator with some items matching predicate."""
        record = {
            "files": [
                {"name": "doc1.pdf", "type": "pdf"},
                {"name": "doc2.doc", "type": "doc"},
            ]
        }

        expr = ListExpression(
            "all",
            "files",
            ComparisonExpression(FieldExpression("type"), "==", "pdf"),
        )
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "files"
        assert result.message is not None
        assert "not all items" in result.message.lower()
        assert "match" in result.message.lower()

    def test_list_empty_list(self):
        """Test behavior with empty lists."""
        record = {"authors": []}

        any_expr = ListExpression(
            "any",
            "authors",
            ComparisonExpression(FieldExpression("affiliation"), "==", "University"),
        )
        all_expr = ListExpression(
            "all",
            "authors",
            ComparisonExpression(FieldExpression("affiliation"), "==", "University"),
        )

        any_result = any_expr.evaluate(record)
        all_result = all_expr.evaluate(record)

        assert any_result.success is False
        assert all_result.success is True
        assert any_result.message is not None
        assert "no items" in any_result.message.lower()

    def test_list_missing_list_field(self):
        """Test behavior when list field is missing."""
        record = {"title": "Test Record"}

        expr = ListExpression(
            "any",
            "authors",
            ComparisonExpression(FieldExpression("name"), "==", "Smith"),
        )
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "authors"
        assert result.message is not None
        assert "missing" in result.message.lower()

    def test_field_not_a_list(self):
        """Test behavior when field is not a list."""
        record = {"author": "Smith"}

        expr = ListExpression(
            "any",
            "author",
            ComparisonExpression(FieldExpression("name"), "==", "Smith"),
        )
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "author"
        assert result.message is not None
        assert "not a list" in result.message.lower()

    def test_nested_list_path(self):
        """Test behavior with nested list paths."""
        record = {
            "publication": {
                "contributors": [
                    {"name": "Smith", "role": "author"},
                    {"name": "Johnson", "role": "editor"},
                ]
            }
        }

        expr = ListExpression(
            "any",
            "publication.contributors",
            ComparisonExpression(FieldExpression("role"), "==", "editor"),
        )
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "publication.contributors"

    def test_list_invalid_operator(self):
        """Test with invalid list operator."""
        with pytest.raises(ValueError) as excinfo:
            ListExpression(
                "some",
                "authors",
                ComparisonExpression(FieldExpression("name"), "==", "Smith"),
            )

        assert "Invalid operator" in str(excinfo.value)

    def test_complex_nested_predicate(self):
        """Test list expression with complex nested predicate."""
        record = {
            "contributors": [
                {
                    "name": "Smith",
                    "role": "author",
                    "affiliations": ["Univ A", "Univ B"],
                },
                {"name": "Johnson", "role": "editor", "affiliations": ["Univ C"]},
            ]
        }

        # Any contributor who is an author AND has Univ B affiliation
        expr = ListExpression(
            "any",
            "contributors",
            LogicalExpression(
                "and",
                [
                    ComparisonExpression(FieldExpression("role"), "==", "author"),
                    ComparisonExpression(
                        FieldExpression("affiliations"), "~=", "Univ B"
                    ),
                ],
            ),
        )
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "contributors"
