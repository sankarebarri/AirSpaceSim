"""Initial production baseline (squashed, PostgreSQL-verified).

Replaces the pre-release SQLite-era revision chain (decision Q5: the API was
never deployed, so history restarts from one clean baseline covering users,
auth sessions, learning progress, scenarios, runs, run commands, and run
checkpoints). All future migration history is preserved from this revision.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260718_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=True),
        sa.Column(
            "preferred_language",
            sa.String(length=8),
            nullable=False,
            server_default="en",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_auth_sessions_token_hash"),
        "auth_sessions",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False
    )

    op.create_table(
        "learning_progress",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("concept_id", sa.String(length=80), nullable=False),
        sa.Column("stage_key", sa.String(length=120), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="completed"
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "user_id", "concept_id", "stage_key", name="uq_progress_user_concept_stage"
        ),
    )
    op.create_index(
        op.f("ix_learning_progress_user_id"),
        "learning_progress",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("airspace_payload", sa.JSON(), nullable=False),
        sa.Column("aircraft_payload", sa.JSON(), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_scenarios_slug"), "scenarios", ["slug"], unique=True)
    op.create_index(
        op.f("ix_scenarios_session_id"), "scenarios", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_scenarios_user_id"), "scenarios", ["user_id"], unique=False
    )

    op.create_table(
        "runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "scenario_id",
            sa.String(length=36),
            sa.ForeignKey("scenarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="draft"
        ),
        sa.Column("sim_rate", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_runs_session_id"), "runs", ["session_id"], unique=False)
    op.create_index(op.f("ix_runs_user_id"), "runs", ["user_id"], unique=False)
    op.create_index(op.f("ix_runs_scenario_id"), "runs", ["scenario_id"], unique=False)

    op.create_table(
        "run_commands",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("command_type", sa.String(length=64), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="accepted"
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_run_commands_run_id"), "run_commands", ["run_id"], unique=False
    )

    op.create_table(
        "run_checkpoints",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("checkpoint_type", sa.String(length=32), nullable=False),
        sa.Column("runtime_status", sa.String(length=32), nullable=False),
        sa.Column("sim_rate", sa.Float(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_run_checkpoints_run_id"), "run_checkpoints", ["run_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("run_checkpoints")
    op.drop_table("run_commands")
    op.drop_table("runs")
    op.drop_table("scenarios")
    op.drop_table("learning_progress")
    op.drop_table("auth_sessions")
    op.drop_table("users")
