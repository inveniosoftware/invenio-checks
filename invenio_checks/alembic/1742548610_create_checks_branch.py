# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT

"""Create checks branch."""

# revision identifiers, used by Alembic.
revision = "1742548610"
down_revision = None
branch_labels = ("invenio_checks",)
depends_on = None


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
