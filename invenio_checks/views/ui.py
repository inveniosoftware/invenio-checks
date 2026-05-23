# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT

"""Checks UI views."""

from flask import Blueprint


#
# Registration
#
def create_ui_blueprint(app):
    """Register blueprint routes on app."""
    blueprint = Blueprint(
        "invenio_checks",
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    return blueprint
