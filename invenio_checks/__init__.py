# SPDX-FileCopyrightText: 2025-2026 CERN.
# SPDX-FileCopyrightText: 2026 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Invenio module to automated curation checks on records."""

from .ext import InvenioChecks

__version__ = "8.2.0"

__all__ = ("__version__", "InvenioChecks")
