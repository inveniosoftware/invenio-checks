# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Tests for metadata expression classes."""

import pytest
from invenio_records.systemfields.relations.results import (
    RelationListResult,
    RelationResult,
)

from invenio_checks.contrib.metadata.expressions import (
    ComparisonExpression,
    FieldExpression,
    ListExpression,
    LogicalExpression,
)


# Minimal implementations of relation classes for testing
class SimpleRelationResult(RelationResult):
    """Minimal implementation of RelationResult for testing."""

    def __init__(self, value):
        self._value = value

    def __call__(self, *args, **kwargs):
        """Return the stored value when called."""
        return self._value


class SimpleRelationListResult(RelationListResult):
    """Minimal implementation of RelationListResult for testing."""

    def __init__(self, values):
        self._values = values

    def __call__(self, *args, **kwargs):
        """Return the stored values when called."""
        return self._values


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

    def test_attribute_access(self):
        """Test accessing object attributes."""

        class Person:
            def __init__(self):
                self.name = "John"
                self.age = 30

        record = {"author": Person()}
        expr = FieldExpression("author.name")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "author.name"
        assert result.value == "John"
        assert result.message is None

    def test_nested_attribute_access(self):
        """Test accessing nested object attributes."""

        class Address:
            def __init__(self):
                self.city = "New York"
                self.country = "USA"

        class Person:
            def __init__(self):
                self.name = "John"
                self.address = Address()

        record = {"author": Person()}
        expr = FieldExpression("author.address.city")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "author.address.city"
        assert result.value == "New York"
        assert result.message is None

    def test_mixed_dict_and_attribute_access(self):
        """Test mixed dictionary and attribute access."""

        class Person:
            def __init__(self):
                self.name = "John"
                self.details = {"age": 30, "occupation": "Researcher"}

        record = {"author": Person()}
        expr = FieldExpression("author.details.occupation")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "author.details.occupation"
        assert result.value == "Researcher"
        assert result.message is None

    def test_missing_attribute(self):
        """Test behavior when attributes are missing."""

        class Person:
            def __init__(self):
                self.name = "John"

        record = {"author": Person()}
        expr = FieldExpression("author.age")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "author.age"
        assert result.value is None
        assert result.message is not None
        assert "missing" in result.message.lower()

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

    def test_relation_result_access(self):
        """Test accessing RelationResult fields."""
        relation_result = SimpleRelationResult(
            {"id": "12345", "title": "Related Record"}
        )

        record = {"relations": relation_result}
        expr = FieldExpression("relations.title")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "relations.title"
        assert result.value == "Related Record"
        assert result.message is None

    def test_relation_list_result_access(self):
        """Test accessing RelationListResult fields."""
        relation_list_result = SimpleRelationListResult(
            [
                {"id": "1", "title": "First Related Record"},
                {"id": "2", "title": "Second Related Record"},
            ]
        )

        record = {"relations": relation_list_result}

        # Access the first relations item's title
        expr = FieldExpression("relations.0.title")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "relations.0.title"
        assert result.value == "First Related Record"
        assert result.message is None

    def test_nested_relation_results(self):
        """Test nested relation result access."""
        inner_relation = SimpleRelationResult({"value": "Inner Value"})
        outer_relation = SimpleRelationResult({"nested": inner_relation})

        record = {"relations": outer_relation}
        expr = FieldExpression("relations.nested.value")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "relations.nested.value"
        assert result.value == "Inner Value"
        assert result.message is None

    def test_relation_list_result_null_handling(self):
        """Test RelationListResult handling when it returns None."""
        relation_list_result = SimpleRelationListResult(None)

        record = {"relations": relation_list_result}
        expr = FieldExpression("relations.0")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "relations.0"
        assert result.value is None
        assert result.message is not None
        assert "missing" in result.message.lower()

    def test_generator_access(self):
        """Test accessing a generator field."""

        def generate_items():
            yield "item1"
            yield "item2"
            yield "item3"

        record = {"items": generate_items()}
        expr = FieldExpression("items.1")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "items.1"
        assert result.value == "item2"
        assert result.message is None

    def test_nested_generator_access(self):
        """Test accessing a nested generator field."""

        def generate_authors():
            yield {"name": "Smith", "id": 1}
            yield {"name": "Johnson", "id": 2}

        record = {"publication": {"authors": generate_authors()}}
        expr = FieldExpression("publication.authors.0.name")
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "publication.authors.0.name"
        assert result.value == "Smith"
        assert result.message is None

    def test_empty_generator(self):
        """Test behavior with empty generator."""

        def empty_gen():
            if False:  # Never yields
                yield None

        record = {"items": empty_gen()}
        expr = FieldExpression("items.0")
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "items.0"
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

    def test_in_operator_with_list_success(self):
        """Test in operator with list success case."""
        record = {"tag": "research"}
        expr = ComparisonExpression(
            FieldExpression("tag"), "in", ["open-access", "research", "science"]
        )
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "tag"
        assert result.value == "research"
        assert result.message is None

    def test_in_operator_with_list_failure(self):
        """Test in operator with list failure case."""
        record = {"tag": "education"}
        expr = ComparisonExpression(
            FieldExpression("tag"), "in", ["open-access", "research", "science"]
        )
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "tag"
        assert result.message is not None
        assert "in" in result.message.lower()
        assert "education" in result.message.lower()

    def test_not_in_operator_with_list_success(self):
        """Test not-in operator with list success case."""
        record = {"tag": "education"}
        expr = ComparisonExpression(
            FieldExpression("tag"), "not in", ["open-access", "research", "science"]
        )
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "tag"
        assert result.value == "education"
        assert result.message is None

    def test_not_in_operator_with_list_failure(self):
        """Test not-in operator with list failure case."""
        record = {"tag": "research"}
        expr = ComparisonExpression(
            FieldExpression("tag"), "not in", ["open-access", "research", "science"]
        )
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "tag"
        assert result.message is not None
        assert "to not be in" in result.message.lower()
        assert "research" in result.message.lower()

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
        with pytest.raises(ValueError) as excinfo:
            ComparisonExpression(FieldExpression("title"), "<>", "Test Record")

        assert "Invalid operator" in str(excinfo.value)

    def test_min_operator_text_success(self):
        """Test min operator with text field - success case."""
        record = {"title": "Hello World"}
        expr = ComparisonExpression(FieldExpression("title"), "min", 5)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "title"
        assert result.value == "Hello World"
        assert result.message is None

    def test_min_operator_text_failure(self):
        """Test min operator with text field - failure case."""
        record = {"title": "Hi"}
        expr = ComparisonExpression(FieldExpression("title"), "min", 5)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "title"
        assert result.value == "Hi"
        assert result.message is not None
        assert "expected" in result.message.lower() or "min" in result.message.lower()

    def test_min_operator_list_success(self):
        """Test min operator with list field - success case."""
        record = {"keywords": ["fieldA", "fieldB", "Williams"]}
        expr = ComparisonExpression(FieldExpression("keywords"), "min", 2)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "keywords"
        assert result.value == ["fieldA", "fieldB", "Williams"]
        assert result.message is None

    def test_min_operator_list_failure(self):
        """Test min operator with list field - failure case."""
        record = {"keywords": ["fieldA"]}
        expr = ComparisonExpression(FieldExpression("keywords"), "min", 2)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "keywords"
        assert result.value == ["fieldA"]
        assert result.message is not None

    def test_min_operator_number_success(self):
        """Test min operator with numeric field - success case."""
        record = {"year": 2025}
        expr = ComparisonExpression(FieldExpression("year"), "min", 2000)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "year"
        assert result.value == 2025
        assert result.message is None

    def test_min_operator_number_failure(self):
        """Test min operator with numeric field - failure case."""
        record = {"year": 1999}
        expr = ComparisonExpression(FieldExpression("year"), "min", 2000)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "year"
        assert result.value == 1999
        assert result.message is not None

    def test_min_operator_empty_string(self):
        """Test min operator with empty string."""
        record = {"title": ""}
        expr = ComparisonExpression(FieldExpression("title"), "min", 1)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "title"
        assert result.value == ""

    def test_min_operator_empty_list(self):
        """Test min operator with empty list."""
        record = {"authors": []}
        expr = ComparisonExpression(FieldExpression("authors"), "min", 1)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "authors"
        assert result.value == []

    def test_min_operator_invalid_type(self):
        """Test min operator with invalid type."""
        record = {"flag": True}
        expr = ComparisonExpression(FieldExpression("flag"), "min", 1)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "flag"
        assert result.message is not None
        assert "cannot check min" in result.message.lower()

    def test_min_operator_equal_value(self):
        """Test min operator with equal value (should pass)."""
        record = {"title": "Test"}
        expr = ComparisonExpression(FieldExpression("title"), "min", 4)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "title"

    # Tests for max operator
    def test_max_operator_text_success(self):
        """Test max operator with text field - success case."""
        record = {"title": "Hi"}
        expr = ComparisonExpression(FieldExpression("title"), "max", 10)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "title"
        assert result.value == "Hi"
        assert result.message is None

    def test_max_operator_text_failure(self):
        """Test max operator with text field - failure case."""
        record = {"title": "Hello World"}
        expr = ComparisonExpression(FieldExpression("title"), "max", 5)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "title"
        assert result.value == "Hello World"
        assert result.message is not None
        assert "expected" in result.message.lower() or "max" in result.message.lower()

    def test_max_operator_list_success(self):
        """Test max operator with list field - success case."""
        record = {"authors": ["Smith", "Johnson"]}
        expr = ComparisonExpression(FieldExpression("authors"), "max", 5)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "authors"
        assert result.value == ["Smith", "Johnson"]
        assert result.message is None

    def test_max_operator_list_failure(self):
        """Test max operator with list field - failure case."""
        record = {"authors": ["Smith", "Johnson", "Williams"]}
        expr = ComparisonExpression(FieldExpression("authors"), "max", 2)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "authors"
        assert result.value == ["Smith", "Johnson", "Williams"]
        assert result.message is not None

    def test_max_operator_number_success(self):
        """Test max operator with numeric field - success case."""
        record = {"year": 2000}
        expr = ComparisonExpression(FieldExpression("year"), "max", 2025)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "year"
        assert result.value == 2000
        assert result.message is None

    def test_max_operator_number_failure(self):
        """Test max operator with numeric field - failure case."""
        record = {"year": 2050}
        expr = ComparisonExpression(FieldExpression("year"), "max", 2025)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "year"
        assert result.value == 2050
        assert result.message is not None

    def test_max_operator_empty_string(self):
        """Test max operator with empty string."""
        record = {"title": ""}
        expr = ComparisonExpression(FieldExpression("title"), "max", 0)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "title"
        assert result.value == ""

    def test_max_operator_empty_list(self):
        """Test max operator with empty list."""
        record = {"authors": []}
        expr = ComparisonExpression(FieldExpression("authors"), "max", 0)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "authors"
        assert result.value == []

    def test_max_operator_invalid_type(self):
        """Test max operator with invalid type."""
        record = {"flag": True}
        expr = ComparisonExpression(FieldExpression("flag"), "max", 1)
        result = expr.evaluate(record)

        assert result.success is False
        assert result.path == "flag"
        assert result.message is not None
        assert "cannot check max" in result.message.lower()

    def test_max_operator_equal_value(self):
        """Test max operator with equal value (should pass)."""
        record = {"title": "Test"}
        expr = ComparisonExpression(FieldExpression("title"), "max", 4)
        result = expr.evaluate(record)

        assert result.success is True
        assert result.path == "title"

    def test_min_max_with_missing_field(self):
        """Test min/max operators when field is missing."""
        record = {"title": "Test Record"}
        min_expr = ComparisonExpression(FieldExpression("abstract"), "min", 10)
        max_expr = ComparisonExpression(FieldExpression("abstract"), "max", 100)

        min_result = min_expr.evaluate(record)
        max_result = max_expr.evaluate(record)

        assert min_result.success is False
        assert "missing" in min_result.message.lower()
        assert max_result.success is False
        assert "missing" in max_result.message.lower()


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

    def test_exists_operator_with_list(self):
        """Test behavior with list with at least one item."""
        record = {"authors": ["Grace Hopper"]}

        exists_expr = ListExpression(
            "exists",
            "authors",
        )

        result = exists_expr.evaluate(record)

        assert result.success is True
        assert result.message is None
        assert result.path == "authors"

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
        exists_expr = ListExpression(
            "exists",
            "authors",
        )

        any_result = any_expr.evaluate(record)
        all_result = all_expr.evaluate(record)
        exists_result = exists_expr.evaluate(record)

        assert any_result.success is False
        assert any_result.message is not None
        assert "no items" in any_result.message.lower()
        assert all_result.success is True
        assert exists_result.success is False
        assert exists_result.message is not None
        assert "no items" in exists_result.message.lower()

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
