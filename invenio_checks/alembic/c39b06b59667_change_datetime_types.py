#
# This file is part of Invenio.
# Copyright (C) 2025 CERN.
# Copyright (C) 2026 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Alter datetime columns to utc aware datetime columns."""

from invenio_db.utils import (
    update_table_columns_column_type_to_datetime,
    update_table_columns_column_type_to_utc_datetime,
)

# revision identifiers, used by Alembic.
revision = ""
down_revision = "1742549302"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    for table_name in ["checks_config", "checks_run"]:
        update_table_columns_column_type_to_utc_datetime(table_name, "created")
        update_table_columns_column_type_to_utc_datetime(table_name, "updated")
    update_table_columns_column_type_to_utc_datetime("checks_run", "start_time")
    update_table_columns_column_type_to_utc_datetime("checks_run", "end_time")


def downgrade():
    """Downgrade database."""
    for table_name in ["checks_config", "checks_run"]:
        update_table_columns_column_type_to_datetime(table_name, "created")
        update_table_columns_column_type_to_datetime(table_name, "updated")
    update_table_columns_column_type_to_datetime("checks_run", "start_time")
    update_table_columns_column_type_to_datetime("checks_run", "end_time")
