"""migration q1"""

from alembic import op

revision = 'q1'
down_revision = None
branch_labels = ('reports',)
depends_on = ('p1',)


def upgrade():
    op.execute("CREATE TABLE q1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE q1")
