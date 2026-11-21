"""migration l2"""

from alembic import op

revision = 'l2'
down_revision = 'l1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE l2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE l2")
