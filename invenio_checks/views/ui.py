# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
