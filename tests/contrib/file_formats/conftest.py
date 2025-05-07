# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Tests for the file formats check."""

import json

import pytest

EXAMPLE_KNOWN_FILES_DATA = {
    "portable_document_format": {
        "name": "Portable Document Format",
        "extensions": ["pdf"],
        "classifiers": ["open", "long_term"],
    },
    "step_file_iso_10303_21": {
        "name": "STEP File (ISO 10303-21)",
        "extensions": ["stp", "step"],
        "classifiers": ["open", "long_term"],
    },
    "stl_stereolithography_format": {
        "name": "STL Stereolithography Format",
        "extensions": ["stl"],
        "classifiers": ["open", "long_term"],
    },
}


@pytest.fixture(scope="session")
def known_files_path(tmp_path_factory):
    """Fixture for a known files file."""
    known_files_file = tmp_path_factory.mktemp("known_files") / "known_files.json"
    known_files_file.write_text(json.dumps(EXAMPLE_KNOWN_FILES_DATA))
    return known_files_file


@pytest.fixture(scope="module")
def app_config(app_config, known_files_path):
    """Application config override."""
    app_config["THEME_FRONTPAGE"] = False
    app_config["CHECKS_FILE_FORMATS_KNOWN_FORMATS_PATH"] = str(known_files_path)
    return app_config
