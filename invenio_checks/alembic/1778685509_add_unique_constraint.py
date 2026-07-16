#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add unique constraint on config, record and draft."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1778685509"
down_revision = "1777225247"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_unique_constraint(
        "uq_checks_run_config_record_draft",
        "checks_run",
        ["config_id", "record_id", "is_draft"],
    )


def downgrade():
    """Downgrade database."""
    op.drop_constraint("uq_checks_run_config_record_draft", "checks_run")
    # ### end Alembic commands ###
