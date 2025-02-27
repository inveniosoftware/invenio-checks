# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from flask import Flask

from invenio_checks import InvenioChecks


def test_version():
    """Test version import."""
    from invenio_checks import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioChecks(app)
    assert "invenio-checks" in app.extensions

    app = Flask("testapp")
    ext = InvenioChecks()
    assert "invenio-checks" not in app.extensions
    ext.init_app(app)
    assert "invenio-checks" in app.extensions
