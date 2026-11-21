"""migration f1"""

from alembic import op

revision = 'f1'
down_revision = None
branch_labels = ('feature',)
depends_on = ('m1',)


def upgrade():
    op.execute("CREATE TABLE f1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE f1")
