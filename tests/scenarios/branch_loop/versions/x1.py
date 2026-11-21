"""migration x1"""

from alembic import op

revision = 'x1'
down_revision = None
branch_labels = ('xx',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE x1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE x1")
