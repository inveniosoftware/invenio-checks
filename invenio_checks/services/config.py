# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Checks services config."""

from invenio_i18n import gettext as _
from invenio_records_resources.services.base import ServiceConfig
from invenio_records_resources.services.base.config import ConfiguratorMixin, FromConfig
from invenio_records_resources.services.records.config import (
    SearchOptions as SearchOptionsBase,
)
from sqlalchemy import asc, desc

from ..models import CheckConfig
from . import results
from .permissions import CheckConfigPermissionPolicy
from .schema import CheckConfigSchema


class CheckConfigSearchOptions(SearchOptionsBase):
    """Check config search options."""

    sort_default = "title"
    sort_direction_default = "asc"
    sort_direction_options = {
        "asc": dict(title=_("Ascending"), fn=asc),
        "desc": dict(title=_("Descending"), fn=desc),
    }
    sort_options = {"title": dict(title=_("Title"), fields=["title"])}

    pagination_options = {"default_results_per_page": 25}


class ChecksConfigServiceConfig(ServiceConfig, ConfiguratorMixin):
    """Checks config service configuration."""

    service_id = "checks-config"

    record_cls = CheckConfig
    search = CheckConfigSearchOptions
    schema = CheckConfigSchema

    permission_policy_cls = FromConfig(
        "CHECKS_PERMISSION_POLICY",
        default=CheckConfigPermissionPolicy,
    )

    result_item_cls = results.Item
    result_list_cls = results.List

    links_item = {}
