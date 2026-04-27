# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Async check."""

from dataclasses import asdict, dataclass, field
from time import sleep

from invenio_checks.base import Check
from invenio_checks.models import CheckConfig, CheckRun


@dataclass
class CheckResult:
    """Result of a check."""

    id: str
    title: str
    errors: list[dict] = field(default_factory=list)

    def to_dict(self):
        """Convert the result to a dictionary."""
        return asdict(self)


class AsyncCheck(Check):
    """Example of an async check."""

    id = "async_check"
    title = "Async check"
    description = "Takes 50 seconds to execute."
    sort_order = 30
    sync = False
    target_type = "record"

    def run(self, record, config: CheckConfig):
        """Run the check against the record's files."""
        result = CheckResult(
            id=self.id,
            title=self.title,
        )
        sleep(50)

        return result
