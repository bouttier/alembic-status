"""migration p1"""

from alembic import op

revision = 'p1'
down_revision = None
branch_labels = ('primary',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE p1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE p1")
