"""migration u1"""

from alembic import op

revision = 'u1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE u1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE u1")
