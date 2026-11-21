"""migration c1"""

from alembic import op

revision = 'c1'
down_revision = None
branch_labels = ('gamma',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE c1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE c1")
