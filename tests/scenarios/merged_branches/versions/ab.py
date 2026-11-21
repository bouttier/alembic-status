"""migration ab"""

from alembic import op

revision = 'ab'
down_revision = ('a2', 'b2')
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE ab (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE ab")
