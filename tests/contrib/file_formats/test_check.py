# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Tests for the file formats check."""

from dataclasses import dataclass

import pytest

from invenio_checks.contrib.file_formats import FileFormatsCheck
from invenio_checks.models import CheckConfig, Severity


@dataclass
class MockFile:
    key: str


@dataclass
class MockRecord:
    files: dict[str, MockFile]


@pytest.fixture
def record_with_files():
    """Fixture for a record with files."""
    return MockRecord(
        files={
            "file1.dwg": MockFile(key="file1.dwg"),
            "file2.pdf": MockFile(key="file2.pdf"),
        }
    )


def test_default_file_format_check(app, record_with_files):
    """Test the file format check."""
    check = FileFormatsCheck()
    check_config = CheckConfig(
        check_id="file_formats",
        params={},  # default params for this test
        severity=Severity.INFO,
        enabled=True,
    )

    result = check.run(record_with_files, check_config)
    assert result.errors == [
        {
            "field": "files.entries.file1.dwg",
            "messages": [".dwg is not a known open or scientific file format."],
            "description": "Using closed or proprietary formats hinders reusability and preservation of published files.",
            "severity": "info",
        }
    ]
