#
# This file is part of Invenio.
# Copyright (C) 2016-2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""make checkrun fields nullable"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import JSONType

from invenio_checks.models import CheckRunStatus, Severity

# revision identifiers, used by Alembic.
revision = 'e8bd906e5da8'
down_revision = 'c39b06b59667'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.alter_column("checks_run", "is_draft", nullable=True)
    op.alter_column("checks_run", "revision_id", nullable=True)


def downgrade():
    """Downgrade database."""
    op.execute("UPDATE checks_run SET is_draft = FALSE WHERE is_draft IS NULL")
    op.execute("UPDATE checks_run SET revision_id = 0 WHERE revision_id IS NULL")
    op.alter_column("checks_run", "is_draft", nullable=False)
    op.alter_column("checks_run", "revision_id", nullable=False)
    # ### end Alembic commands ###
