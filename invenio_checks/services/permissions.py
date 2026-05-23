# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT

"""Checks permissions."""

from invenio_administration.generators import Administration
from invenio_records_permissions.generators import SystemProcess
from invenio_records_permissions.policies import BasePermissionPolicy


class CheckConfigPermissionPolicy(BasePermissionPolicy):
    """Access control configuration for check configurations."""

    can_search = [Administration(), SystemProcess()]
    can_create = [Administration(), SystemProcess()]
    can_read = [Administration(), SystemProcess()]
    can_update = [Administration(), SystemProcess()]
    can_delete = [Administration(), SystemProcess()]


class CheckRunPermissionPolicy(BasePermissionPolicy):
    """Access control configuration for check runs."""

    can_search = [Administration(), SystemProcess()]
    can_create = [Administration(), SystemProcess()]
    can_read = [Administration(), SystemProcess()]
    can_update = [Administration(), SystemProcess()]
    can_delete = [Administration(), SystemProcess()]
    can_stop = [Administration(), SystemProcess()]
