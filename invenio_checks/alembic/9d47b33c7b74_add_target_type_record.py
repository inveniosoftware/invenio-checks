#
# This file is part of Invenio.
# Copyright (C) 2016-2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add target_type record"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import JSONType

from invenio_checks.models import CheckRunStatus, Severity

# revision identifiers, used by Alembic.
revision = '9d47b33c7b74'
down_revision = 'e8bd906e5da8'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.execute("""
        UPDATE checks_config
        SET params = params || '{"target_type": "record"}'::jsonb
        WHERE params->>'target_type' IS NULL
    """)
    op.alter_column("checks_run", "revision_id", nullable=True)


def downgrade():
    """Downgrade database."""
    op.execute("""
        UPDATE checks_config
        SET params = params - 'target_type'
    """)
    # ### end Alembic commands ###
