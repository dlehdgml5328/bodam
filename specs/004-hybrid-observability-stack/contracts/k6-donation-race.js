// Donation race load test
// Goal: hammer /api/v1/donations with identical payloads to surface duplicate inserts / deadlocks
// Usage example:
//   BASE_URL=http://backend:8000 \
//   TEST_TOKEN="Bearer <jwt>" \
//   DONATION_FIRE_STATION_ID=f2c3be6f-.... \
//   DONATION_AMOUNT=10000 \
//   K6_VUS=100 \
//   K6_DURATION=3m \
//   docker run --rm -it \
//     -e BASE_URL -e TEST_TOKEN -e DONATION_FIRE_STATION_ID -e DONATION_AMOUNT \
//     -e K6_VUS -e K6_DURATION \
//     -v "${PWD}/specs/004-hybrid-observability-stack/contracts/k6-donation-race.js:/scripts/test.js:ro" \
//     --network container:bodam-backend grafana/k6 run /scripts/test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://backend:8000';
const TOKEN = __ENV.TEST_TOKEN || '';
const FIRE_STATION_ID = __ENV.DONATION_FIRE_STATION_ID || '';
const DONATION_AMOUNT = Number(__ENV.DONATION_AMOUNT || 10000);
const DONATION_MESSAGE =
  __ENV.DONATION_MESSAGE || 'k6 donation race test - expect dedupe';

if (!TOKEN) {
  throw new Error('TEST_TOKEN is required (Bearer <jwt>)');
}
if (!FIRE_STATION_ID) {
  throw new Error('DONATION_FIRE_STATION_ID is required');
}

const vus = Number(__ENV.K6_VUS || 50);
const duration = __ENV.K6_DURATION || '2m';

export const options = {
  scenarios: {
    race: {
      executor: 'constant-vus',
      vus,
      duration,
      gracefulStop: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'], // allow a few conflicts
    http_req_duration: ['p(95)<300'],
    duplicate_conflicts: ['count<=0'], // ensure counter is exposed
  },
};

const duplicateConflicts = new Counter('duplicate_conflicts');
const requestFailures = new Rate('donation_failures');

export default function () {
  const payload = JSON.stringify({
    mode: 'single',
    fire_station_id: FIRE_STATION_ID,
    amount: DONATION_AMOUNT,
    message: DONATION_MESSAGE
  });

  const res = http.post(`${BASE_URL}/donations`, payload, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: TOKEN.startsWith('Bearer') ? TOKEN : `Bearer ${TOKEN}`,
    },
    tags: { endpoint: '/donations', scenario: 'donation_race' },
  });

  const ok = check(res, {
    'status is 201 or 409': (r) => r.status === 201 || r.status === 409,
  });

  if (!ok) {
    requestFailures.add(1);
  }

  if (res.status === 409) {
    duplicateConflicts.add(1);
  }

  // short pause to let async locks resolve
  sleep(0.2);
}

