#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add nullable fields to check runs, target_type column to check config, and add unique constraint on config, record and draft."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "1784902219"
down_revision = "1777225247"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.alter_column("checks_run", "is_draft", nullable=True)
    op.alter_column("checks_run", "revision_id", nullable=True)

    op.add_column(
        "checks_config",
        sa.Column("target_type", sa.String(15), nullable=False, server_default=""),
    )
    op.execute(text("""UPDATE checks_config
                       SET target_type = 'record'
                       WHERE check_id = 'metadata'
                          or check_id = 'file_formats';"""))

    op.create_unique_constraint(
        "uq_checks_run_config_record_draft",
        "checks_run",
        ["config_id", "record_id", "is_draft"],
    )


def downgrade():
    """Downgrade database."""
    op.drop_constraint("uq_checks_run_config_record_draft", "checks_run")

    op.drop_column("checks_config", "target_type")

    op.execute("UPDATE checks_run SET is_draft = FALSE WHERE is_draft IS NULL")
    op.execute("UPDATE checks_run SET revision_id = 0 WHERE revision_id IS NULL")
    op.alter_column("checks_run", "is_draft", nullable=False)
    op.alter_column("checks_run", "revision_id", nullable=False)
    # ### end Alembic commands ###
