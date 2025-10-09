-- Sample seed data for donation flows (development use only)
-- Run after applying migrations: psql $DATABASE_URL -f backend/scripts/seed_sample_donations.sql

BEGIN;

-- 1. Seed user
INSERT INTO users (id, email, password_hash, name, phone, role, tier, total_donated, created_at, updated_at, is_active)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'seed.donor@bodam.test',
    '$2b$12$KIX8G6N6i/K3PaY5E9OQhe1iKsFcEYJIyaKOA1NVuMcZp8K4D3OPG',
    'Seed Donor',
    '010-0000-0000',
    'donor',
    1,
    0,
    NOW(),
    NOW(),
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- 2. Seed fire station
INSERT INTO fire_stations (
    id, name, address, location, phone, station_code, region, district, status,
    total_received, donor_count, created_at, updated_at
) VALUES (
    '22222222-2222-2222-2222-222222222222',
    '서울강남소방서',
    '서울특별시 강남구 테헤란로 99',
    ST_SetSRID(ST_MakePoint(127.0276, 37.4979), 4326),
    '02-000-0000',
    'FS-001',
    '서울특별시',
    '강남구',
    'active',
    0,
    0,
    NOW(),
    NOW()
)
ON CONFLICT (station_code) DO NOTHING;

-- 3. Seed live status snapshot
INSERT INTO fire_station_statuses (id, station_id, status, priority, status_label, summary, updated_at)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    '22222222-2222-2222-2222-222222222222',
    'dispatching',
    'high',
    '출동 중',
    '화재 진압 출동',
    NOW()
)
ON CONFLICT (station_id) DO UPDATE
SET status = EXCLUDED.status,
    priority = EXCLUDED.priority,
    status_label = EXCLUDED.status_label,
    summary = EXCLUDED.summary,
    updated_at = NOW();

-- 4. One-time donation with single allocation
INSERT INTO donations (
    id, user_id, fire_station_id, group_id, mode, amount, currency, type, status,
    payment_method, toss_payment_key, toss_order_id, message, donor_display_name,
    is_anonymous, needs_receipt, is_group_anonymous, created_at, completed_at
) VALUES (
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    NULL,
    'single',
    30000,
    'KRW',
    'one_time',
    'completed',
    'card',
    'pay_4444',
    'bodam-4444',
    '응원합니다',
    'Seed Donor',
    FALSE,
    TRUE,
    FALSE,
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days'
)
ON CONFLICT (toss_order_id) DO NOTHING;

INSERT INTO donation_allocations (id, donation_id, fire_station_id, amount, allocation_type)
VALUES (
    '55555555-5555-5555-5555-555555555555',
    '44444444-4444-4444-4444-444444444444',
    '22222222-2222-2222-2222-222222222222',
    30000,
    'primary'
)
ON CONFLICT (id) DO NOTHING;

-- 5. Regular donation with subscription and split allocations
INSERT INTO donations (
    id, user_id, fire_station_id, group_id, mode, amount, currency, type, status,
    payment_method, toss_payment_key, toss_order_id, message, donor_display_name,
    is_anonymous, needs_receipt, is_group_anonymous, created_at
) VALUES (
    '66666666-6666-6666-6666-666666666666',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    NULL,
    'multiple',
    45000,
    'KRW',
    'recurring',
    'pending',
    NULL,
    NULL,
    'bodam-6666',
    '월간 커피 지원',
    'Seed Donor',
    FALSE,
    TRUE,
    FALSE,
    NOW()
)
ON CONFLICT (toss_order_id) DO NOTHING;

INSERT INTO donation_allocations (id, donation_id, fire_station_id, amount, allocation_type)
VALUES
    (
        '77777777-7777-7777-7777-777777777777',
        '66666666-6666-6666-6666-666666666666',
        '22222222-2222-2222-2222-222222222222',
        30000,
        'primary'
    ),
    (
        '88888888-8888-8888-8888-888888888888',
        '66666666-6666-6666-6666-666666666666',
        '22222222-2222-2222-2222-222222222222',
        15000,
        'split'
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO donation_subscriptions (
    id, user_id, origin_donation_id, status, cycle, amount, currency, next_billing_at,
    started_at, toss_customer_key, toss_billing_key
) VALUES (
    '99999999-9999-9999-9999-999999999999',
    '11111111-1111-1111-1111-111111111111',
    '66666666-6666-6666-6666-666666666666',
    'active',
    'monthly',
    45000,
    'KRW',
    NOW() + INTERVAL '30 days',
    NOW(),
    'customer_9999',
    'bill_9999'
)
ON CONFLICT (id) DO NOTHING;

UPDATE donations
SET subscription_id = '99999999-9999-9999-9999-999999999999'
WHERE id = '66666666-6666-6666-6666-666666666666';

COMMIT;
