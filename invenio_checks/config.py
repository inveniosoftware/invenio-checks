# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT

"""Invenio checks config."""

from datetime import timedelta

CHECKS_ENABLED = False
CHECKS_SUBCOMMUNITY_ENABLED = False
"""Enable checks."""

CHECKS_RUN_STALE_AFTER = timedelta(seconds=900)
"""How long a PENDING or RUNNING check run may sit before it is failed."""
