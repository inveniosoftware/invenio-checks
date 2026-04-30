#
# This file is part of Invenio.
# Copyright (C) 2016-2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add target_type record."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "9d47b33c7b74"
down_revision = "e8bd906e5da8"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column(
        "checks_config",
        sa.Column("target_type", sa.String(15), nullable=False, server_default=""),
    )
    op.execute(text("""UPDATE checks_config SET target_type = 'record' WHERE
                check_id = 'metadata' or check_id = 'file_formats';"""))


def downgrade():
    """Downgrade database."""
    op.drop_column("checks_config", "target_type")
    # ### end Alembic commands ###
