# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT

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
