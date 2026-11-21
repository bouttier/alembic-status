"""migration r1"""

from alembic import op

revision = 'r1'
down_revision = None
branch_labels = ('audit',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE r1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE r1")
