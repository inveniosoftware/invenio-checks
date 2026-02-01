# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
# Copyright (C) 2026 Graz University of Technology.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to automated curation checks on records."""

from .ext import InvenioChecks

__version__ = "4.0.0"

__all__ = ("__version__", "InvenioChecks")
