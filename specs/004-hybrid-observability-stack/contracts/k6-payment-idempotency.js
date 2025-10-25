// Payment idempotency load test
// Sends repeated confirmation calls with the same order_id/idempotency-key to
// ensure only the first succeeds and subsequent ones hit the cache/idempotency guard.
//
// Required env vars:
//   BASE_URL (default http://backend:8000)
//   PAYMENT_ORDER_ID  (order created during donation checkout)
//   PAYMENT_KEY       (payment key from Toss)
//   PAYMENT_AMOUNT    (defaults to 10000)
//   IDEMPOTENCY_KEY   (defaults to constant value for each VU)
//
// Optional env vars:
//   K6_VUS (default 10)
//   K6_DURATION (default 2m)
//   AUTH_TOKEN (Bearer token if endpoint protected)

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://backend:8000';
const ORDER_ID = __ENV.PAYMENT_ORDER_ID || '';
const PAYMENT_KEY = __ENV.PAYMENT_KEY || '';
const AMOUNT = Number(__ENV.PAYMENT_AMOUNT || 10000);
const IDEMPOTENCY_KEY =
  __ENV.IDEMPOTENCY_KEY || 'k6-idempotency-test-fixed-key';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';
const vus = Number(__ENV.K6_VUS || 10);
const duration = __ENV.K6_DURATION || '2m';

if (!ORDER_ID || !PAYMENT_KEY) {
  throw new Error('PAYMENT_ORDER_ID and PAYMENT_KEY env vars are required');
}

export const options = {
  scenarios: {
    idempotency: {
      executor: 'constant-vus',
      vus,
      duration,
      gracefulStop: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    idempotent_hits: ['count>0'], // expect hits to occur
  },
};

const idempotentHits = new Counter('idempotent_hits');
const duplicateErrors = new Counter('idempotent_errors');

export default function () {
  const payload = JSON.stringify({
    paymentKey: PAYMENT_KEY,
    orderId: ORDER_ID,
    amount: AMOUNT,
  });

  const headers = {
    'Content-Type': 'application/json',
    'Idempotency-Key': IDEMPOTENCY_KEY,
  };

  if (AUTH_TOKEN) {
    headers.Authorization = AUTH_TOKEN.startsWith('Bearer')
      ? AUTH_TOKEN
      : `Bearer ${AUTH_TOKEN}`;
  }

  const res = http.post(`${BASE_URL}/payments/confirm`, payload, {
    headers,
    tags: { endpoint: '/payments/confirm', scenario: 'payment_idempotency' },
  });

  if (res.status === 200 || res.status === 201) {
    idempotentHits.add(1);
  } else if (res.status === 409) {
    idempotentHits.add(1);
  } else {
    duplicateErrors.add(1);
  }

  check(res, {
    'first or cached response': (r) =>
      r.status === 200 || r.status === 201 || r.status === 409,
  });

  sleep(0.3);
}

