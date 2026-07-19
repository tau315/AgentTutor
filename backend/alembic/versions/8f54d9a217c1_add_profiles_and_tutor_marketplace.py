"""add profiles and tutor marketplace

Revision ID: 8f54d9a217c1
Revises: d27a7714c6cb
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "8f54d9a217c1"
down_revision: str | Sequence[str] | None = "d27a7714c6cb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=100)))
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "student_profiles",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("grade_level", sa.String(length=50)),
        sa.Column("learning_goals", sa.Text()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "tutor_profiles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("bio", sa.Text()),
        sa.Column("hourly_rate", sa.Numeric(10, 2)),
        sa.Column("rating", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "tutor_subjects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tutor_profile_id", sa.String(), nullable=False),
        sa.Column("subject", sa.String(length=100), nullable=False),
        sa.Column("expertise", sa.String(length=150)),
        sa.ForeignKeyConstraint(
            ["tutor_profile_id"], ["tutor_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tutor_profile_id", "subject", name="uq_tutor_subject"),
    )
    op.create_index("ix_tutor_subjects_subject", "tutor_subjects", ["subject"])
    op.create_index("ix_tutor_subjects_expertise", "tutor_subjects", ["expertise"])

    # Existing accounts receive the same empty profile new signups now receive.
    op.execute(
        "INSERT INTO student_profiles (user_id) "
        "SELECT id FROM users WHERE role = 'student'"
    )
    op.execute(
        "INSERT INTO tutor_profiles (id, user_id, rating, is_active) "
        "SELECT md5(random()::text || clock_timestamp()::text), id, 0, false "
        "FROM users WHERE role = 'tutor'"
    )


def downgrade() -> None:
    op.drop_index("ix_tutor_subjects_expertise", table_name="tutor_subjects")
    op.drop_index("ix_tutor_subjects_subject", table_name="tutor_subjects")
    op.drop_table("tutor_subjects")
    op.drop_table("tutor_profiles")
    op.drop_table("student_profiles")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_column("users", "is_active")
    op.drop_column("users", "display_name")
