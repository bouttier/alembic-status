"""migration r2"""

from alembic import op

revision = 'r2'
down_revision = 'r1'
branch_labels = None
depends_on = ('p2',)


def upgrade():
    op.execute("CREATE TABLE r2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE r2")
