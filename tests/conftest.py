# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import json
import os

import pytest
from invenio_app.factory import create_app as _create_app


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_app


@pytest.fixture(scope="session")
def example_rules_config():
    """Load example rules configuration."""
    example_file_path = os.path.join(
        os.path.dirname(__file__), "example_multilingual.json"
    )
    with open(example_file_path, "r", encoding="utf-8") as f:
        return json.load(f)
