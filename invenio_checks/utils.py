# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
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
