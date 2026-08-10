# SPDX-FileCopyrightText: 2025-2026 CERN.
# SPDX-FileCopyrightText: 2025-2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT
"""Utilities."""

import functools

from flask import current_app, has_app_context
from invenio_i18n import LazyString
from invenio_i18n.ext import current_i18n
from marshmallow_utils.fields.babel import gettext_from_dict


def _get_locale_settings():
    """Get locale settings when an app context is available."""
    locale = "en"
    default_locale = "en"

    if has_app_context():
        locale = str(getattr(current_i18n, "locale", locale) or locale)
        default_locale = str(
            current_app.config.get("BABEL_DEFAULT_LOCALE", default_locale)
        )

    return locale, default_locale


def translate_field(field_value):
    """Translate a field that can be string or multilingual dict.

    Args:
        field_value: String or dict with language keys like {"en": "text", "sv": "text"}

    Returns:
        Translated string based on current locale
    """
    if not field_value:
        return ""

    if isinstance(field_value, (str, LazyString)):
        return str(field_value)

    if isinstance(field_value, dict):
        locale, default_locale = _get_locale_settings()
        try:
            # Fallback handled by gettext_from_dict:
            # current locale -> language match -> default locale/en -> any available language
            return gettext_from_dict(field_value, locale, default_locale)
        except (AttributeError, TypeError, ValueError) as e:
            raise ValueError(
                f"Invalid multilingual translation field: {field_value}"
            ) from e

    # This shouldn't happen for rule text fields. Indicates a configuration error
    raise ValueError(
        f"Unsupported field type for translation: {type(field_value)} with value: {field_value}"
    )


def aggregate_checks_severity(checks, check_class_id):
    """Aggregate the worst severity across a set of checks.

    Allows handling cases with more than one run per check_id, displaying only one icon.
    """
    severity = "success"
    for check in checks:
        if check.config.check_cls.id != check_class_id:
            continue
        if check.status.value in ("P", "R"):
            return "running"
        check_severity = (
            check.config.severity.error_value
            if check.status.value == "E"
            else check.overall_severity
        )
        if check_severity == "error":
            severity = "error"
        elif check_severity == "warning" and severity != "error":
            severity = "warning"
        elif check_severity == "info" and severity == "success":
            severity = "info"
    return severity


def get_visible_checks(checks, receiver_community_id):
    """Return (checks, check_classes) with only visible checks."""
    classes_with_visible_checks = set()
    visible_checks = []
    for check in checks:
        check_class = check.config.check_cls

        receiver_community_matches_config = (
            str(check.config.community_id) == receiver_community_id
        )
        if (
            not check_class.hide_parent_checks
            or receiver_community_matches_config
            or check.config.community_id is None  # global checks
        ):
            classes_with_visible_checks.add(check_class)
            visible_checks.append(check)
    return visible_checks, classes_with_visible_checks


class classproperty:
    """Decorator to define a class property."""

    def __init__(self, func) -> None:
        """Initialize the class property decorator."""
        functools.update_wrapper(self, func)

    def __get__(self, _, owner):
        """Get the class property value."""
        return self.__wrapped__(owner)
