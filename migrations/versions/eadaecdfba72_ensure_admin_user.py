"""ensure_admin_user

Revision ID: eadaecdfba72
Revises: 82c597454808
Create Date: 2025-02-15 03:35:47.191806

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel
from dundie.models.user import User  # NEW
from sqlmodel import Session  # NEW


# revision identifiers, used by Alembic.
revision = 'eadaecdfba72'
down_revision = '82c597454808'
branch_labels = None
depends_on = None


def upgrade() -> None:  # NEW
    bind = op.get_bind()
    session = Session(bind=bind)

    admin = User(
        name="Admin",
        username="admin",
        email="admin@dm.com",
        dept="management",
        currency="USD",
        password="admin",  # envvar/secrets - colocar password em settings
    )
    # if admin user already exists it will raise IntegrityError
    try:
        session.add(admin)
        session.commit()
    except sa.exc.IntegrityError:
        session.rollback()


def downgrade() -> None:
    pass
