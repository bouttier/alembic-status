"""migration b1"""

from alembic import op

revision = 'b1'
down_revision = None
branch_labels = ('beta',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE b1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE b1")
