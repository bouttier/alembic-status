"""migration a1"""

from alembic import op

revision = 'a1'
down_revision = None
branch_labels = ('alpha',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE a1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE a1")
