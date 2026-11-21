"""migration e1"""

from alembic import op

revision = 'e1'
down_revision = None
branch_labels = ('epsilon',)
depends_on = ('d1',)


def upgrade():
    op.execute("CREATE TABLE e1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE e1")
