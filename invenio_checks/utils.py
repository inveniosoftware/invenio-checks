# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT
"""Utilities."""

import functools


class classproperty:
    """Decorator to define a class property."""

    def __init__(self, func) -> None:
        """Initialize the class property decorator."""
        functools.update_wrapper(self, func)

    def __get__(self, _, owner):
        """Get the class property value."""
        return self.__wrapped__(owner)
