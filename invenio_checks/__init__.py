# SPDX-FileCopyrightText: 2025-2026 CERN.
# SPDX-FileCopyrightText: 2026 Graz University of Technology.
# SPDX-FileCopyrightText: 2026 TU Wien.
# SPDX-License-Identifier: MIT

"""Invenio module to automated curation checks on records."""

from .ext import InvenioChecks

__version__ = "11.0.1"

__all__ = ("__version__", "InvenioChecks")
