# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Utilities."""

import functools

from marshmallow_utils.fields.babel import gettext_from_dict


def translate_field(field_value):
    """Translate a field that can be string or multilingual dict.

    Args:
        field_value: String or dict with language keys like {"en": "text", "sv": "text"}

    Returns:
        Translated string based on current locale
    """
    if not field_value:
        return ""

    if isinstance(field_value, str):
        return field_value

    if isinstance(field_value, dict):
        try:
            # Lazy imports to keep utils usable even when deps/context aren't ready
            # pylint: disable=import-outside-toplevel
            from flask import current_app
            from invenio_i18n.ext import current_i18n

            locale = getattr(current_i18n, "locale", "en") if current_i18n else "en"
            default_locale = (
                current_app.config.get("BABEL_DEFAULT_LOCALE", "en")
                if current_app
                else "en"
            )
            return gettext_from_dict(field_value, locale, default_locale)
        except (ImportError, AttributeError, RuntimeError, KeyError, TypeError):
            # fallback: current locale -> en -> any available language -> empty
            locale = getattr(current_i18n, "locale", "en") if current_i18n else "en"
            return (
                field_value.get(locale)
                or field_value.get("en")
                or next(
                    iter(field_value.values()), ""
                )  # Show any available translation rather than empty
            )

    # This shouldn't happen for rule text fields. Indicates a configuration error
    raise ValueError(
        f"Unsupported field type for translation: {type(field_value)} with value: {field_value}"
    )


class classproperty:
    """Decorator to define a class property."""

    def __init__(self, func) -> None:
        """Initialize the class property decorator."""
        functools.update_wrapper(self, func)

    def __get__(self, _, owner):
        """Get the class property value."""
        return self.__wrapped__(owner)
