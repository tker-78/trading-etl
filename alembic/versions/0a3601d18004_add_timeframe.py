"""add_timeframe

Revision ID: 0a3601d18004
Revises: e2444ebd2a06
Create Date: 2026-03-13 22:32:07.695257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a3601d18004'
down_revision: Union[str, Sequence[str], None] = 'e2444ebd2a06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
