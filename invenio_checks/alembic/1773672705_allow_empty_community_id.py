#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Allow empty community id."""

import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "1773672705"
down_revision = "c39b06b59667"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.alter_column(
        "checks_config",
        "community_id",
        existing_type=sqlalchemy_utils.types.uuid.UUIDType(),
        nullable=True,
    )


def downgrade():
    """Downgrade database."""
    op.alter_column(
        "checks_config",
        "community_id",
        existing_type=sqlalchemy_utils.types.uuid.UUIDType(),
        nullable=False,
    )
