"""Add ErrorEvent and LoadTestRun tables

Revision ID: 009_observability
Revises: 008_fire_incidents_pipeline
Create Date: 2025-10-16 20:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector


revision = '009_observability'
down_revision = '008_fire_incidents_pipeline'
branch_labels = None
depends_on = None


def upgrade():
    # ErrorEvent 테이블 생성
    op.create_table(
        'error_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('level', sa.String(10), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('service', sa.String(50), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('method', sa.String(10), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('trace_id', sa.String(32), nullable=True),
        sa.Column('span_id', sa.String(16), nullable=True),
        sa.Column('context', JSONB, nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('resolution_status', sa.String(20), nullable=False, server_default='new'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(100), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.create_index('ix_error_events_timestamp', 'error_events', ['timestamp'])
    op.create_index('ix_error_events_level', 'error_events', ['level'])
    op.create_index('ix_error_events_service', 'error_events', ['service'])
    op.create_index('ix_error_events_trace_id', 'error_events', ['trace_id'])
    op.create_index('ix_error_events_resolution_status', 'error_events', ['resolution_status'])
    op.create_index('ix_error_events_timestamp_level', 'error_events', ['timestamp', 'level'])
    op.create_index('ix_error_events_service_timestamp', 'error_events', ['service', 'timestamp'])

    # LoadTestRun 테이블 생성
    op.create_table(
        'load_test_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('test_id', sa.String(100), nullable=False, unique=True),
        sa.Column('scenario_name', sa.String(100), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('target_vu', sa.Integer(), nullable=False),
        sa.Column('stages_config', JSONB, nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=True),
        sa.Column('failed_requests', sa.Integer(), nullable=True),
        sa.Column('requests_per_second', sa.Float(), nullable=True),
        sa.Column('latency_p50', sa.Float(), nullable=True),
        sa.Column('latency_p95', sa.Float(), nullable=True),
        sa.Column('latency_p99', sa.Float(), nullable=True),
        sa.Column('latency_avg', sa.Float(), nullable=True),
        sa.Column('latency_min', sa.Float(), nullable=True),
        sa.Column('latency_max', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('passed_thresholds', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('results_json', JSONB, nullable=True),
        sa.Column('executor', sa.String(100), nullable=True),
        sa.Column('tags', JSONB, nullable=True),
        sa.Column('prometheus_start', sa.Integer(), nullable=True),
        sa.Column('prometheus_end', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.create_index('ix_load_test_runs_test_id', 'load_test_runs', ['test_id'], unique=True)
    op.create_index('ix_load_test_runs_start_time', 'load_test_runs', ['start_time'])
    op.create_index('ix_load_test_runs_scenario_status', 'load_test_runs', ['scenario_name', 'status'])


def downgrade():
    op.drop_table('load_test_runs')
    op.drop_table('error_events')
