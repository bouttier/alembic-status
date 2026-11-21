"""migration c2"""

from alembic import op

revision = 'c2'
down_revision = 'c1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE c2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE c2")
