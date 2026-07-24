# SPDX-FileCopyrightText: 2025 CERN.
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


def get_check_target(check_run):
    """Get the target object for a check run."""

    target_type = getattr(check_run.config, "target_type", None)

    if target_type == "record":
        from invenio_rdm_records.proxies import current_rdm_records_service as service

        if check_run.is_draft:
            return service.draft_cls.get_record(check_run.record_id)

        return service.record_cls.get_record(check_run.record_id)

    if target_type == "community":
        from invenio_communities.proxies import current_communities

        return current_communities.service.record_cls.get_record(check_run.record_id)

    current_app.logger.error(
        "Invalid target_type for check config",
        extra={
            "target_type": target_type,
            "check_run_id": str(check_runconfig.check_id),
        },
    )

    return None


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


class classproperty:
    """Decorator to define a class property."""

    def __init__(self, func) -> None:
        """Initialize the class property decorator."""
        functools.update_wrapper(self, func)

    def __get__(self, _, owner):
        """Get the class property value."""
        return self.__wrapped__(owner)
