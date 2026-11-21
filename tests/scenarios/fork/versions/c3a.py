"""migration c3a"""

from alembic import op

revision = 'c3a'
down_revision = 'c2'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE c3a (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE c3a")
