# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Async check."""

from time import sleep

from invenio_checks.base import Check, CheckResult
from invenio_checks.models import CheckConfig


class AsyncCheck(Check):
    """Example of an async check."""

    id = "async_check"
    title = "Async check"
    description = "Takes 60 seconds to execute."
    sort_order = 30
    sync = False
    target_type = "record"

    def run(self, record, config: CheckConfig):
        """Run the check against the record's files."""
        sleep(60)

        return CheckResult(id=self.id, title=self.title, description=self.description)
