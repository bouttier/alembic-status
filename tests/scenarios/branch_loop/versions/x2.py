"""migration x2"""

from alembic import op

revision = 'x2'
down_revision = 'x1'
branch_labels = None
depends_on = ('y1',)


def upgrade():
    op.execute("CREATE TABLE x2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE x2")
