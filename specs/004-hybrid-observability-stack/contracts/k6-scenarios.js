// K6 Load Testing Scenarios Contract
// Purpose: Define load test scenarios for 50-200-500 VU performance validation
// Reference: research.md Section 5 (K6 + Prometheus Integration)
// Success Criteria: spec.md - 200 concurrent users, p95 < 500ms

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

// Custom metrics for Prometheus
const errorRate = new Rate('errors');
const donationDuration = new Trend('donation_request_duration');
const rankingDuration = new Trend('ranking_request_duration');
const apiRequests = new Counter('api_requests_total');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://backend:8000';
const PROMETHEUS_PUSHGATEWAY = __ENV.PROMETHEUS_PUSHGATEWAY || 'http://prometheus-pushgateway:9091';

// Scenario 1: Baseline - 50 VU (Normal Traffic)
export const scenario_baseline = {
  executor: 'ramping-vus',
  startVUs: 0,
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 0 },    // Ramp down to 0
  ],
  gracefulRampDown: '30s',
  tags: { scenario: 'baseline' },
};

// Scenario 2: Target Load - 200 VU (Success Criteria)
export const scenario_target = {
  executor: 'ramping-vus',
  startVUs: 0,
  stages: [
    { duration: '3m', target: 200 },  // Ramp up to 200 users
    { duration: '10m', target: 200 }, // Stay at 200 users (success criteria)
    { duration: '3m', target: 0 },    // Ramp down to 0
  ],
  gracefulRampDown: '30s',
  tags: { scenario: 'target' },
};

// Scenario 3: Stress Test - 500 VU (Peak Traffic)
export const scenario_stress = {
  executor: 'ramping-vus',
  startVUs: 0,
  stages: [
    { duration: '5m', target: 500 },  // Ramp up to 500 users
    { duration: '10m', target: 500 }, // Stay at 500 users
    { duration: '5m', target: 0 },    // Ramp down to 0
  ],
  gracefulRampDown: '1m',
  tags: { scenario: 'stress' },
};

// Scenario 4: Spike Test - Sudden Traffic Surge
export const scenario_spike = {
  executor: 'ramping-vus',
  startVUs: 50,
  stages: [
    { duration: '1m', target: 50 },   // Normal load
    { duration: '30s', target: 300 }, // Sudden spike
    { duration: '3m', target: 300 },  // Maintain spike
    { duration: '30s', target: 50 },  // Back to normal
    { duration: '2m', target: 50 },   // Cool down
    { duration: '1m', target: 0 },    // Ramp down
  ],
  gracefulRampDown: '30s',
  tags: { scenario: 'spike' },
};

// Thresholds (Success Criteria from spec.md)
export const options = {
  scenarios: {
    // Select scenario via K6_SCENARIO env variable
    baseline: __ENV.K6_SCENARIO === 'baseline' ? scenario_baseline : null,
    target: __ENV.K6_SCENARIO === 'target' ? scenario_target : null,
    stress: __ENV.K6_SCENARIO === 'stress' ? scenario_stress : null,
    spike: __ENV.K6_SCENARIO === 'spike' ? scenario_spike : null,
  },
  thresholds: {
    // HTTP request duration - p95 < 500ms (from spec.md)
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],

    // HTTP request success rate > 99%
    'http_req_failed': ['rate<0.01'],

    // Custom metrics
    'errors': ['rate<0.01'],
    'donation_request_duration': ['p(95)<500'],
    'ranking_request_duration': ['p(95)<300'],
  },
  // Output to statsd for Prometheus scraping
  ext: {
    loadimpact: {
      projectID: 'bodam-loadtest',
      name: 'Hybrid Observability Load Test',
    },
  },
};

// Setup function - runs once before test
export function setup() {
  console.log(`Starting K6 load test: ${__ENV.K6_SCENARIO || 'all'}`);
  console.log(`Base URL: ${BASE_URL}`);

  // Health check
  const healthCheck = http.get(`${BASE_URL}/health`);
  check(healthCheck, {
    'health check passed': (r) => r.status === 200,
  });

  return {
    startTime: Date.now(),
  };
}

// Main test function
export default function(data) {
  // Realistic user behavior simulation
  group('User Journey - Donation Platform', function() {

    // 1. View donation ranking page (public)
    group('View Donation Ranking', function() {
      const rankingStart = Date.now();
      const rankingResponse = http.get(`${BASE_URL}/api/v1/donations/ranking`, {
        tags: { endpoint: 'ranking' },
      });

      const rankingDurationMs = Date.now() - rankingStart;
      rankingDuration.add(rankingDurationMs);
      apiRequests.add(1);

      const rankingSuccess = check(rankingResponse, {
        'ranking status is 200': (r) => r.status === 200,
        'ranking response time < 300ms': (r) => r.timings.duration < 300,
        'ranking has data': (r) => JSON.parse(r.body).length > 0,
      });

      if (!rankingSuccess) {
        errorRate.add(1);
      }
    });

    sleep(1); // User reads ranking

    // 2. Create donation (authenticated user)
    group('Create Donation', function() {
      const donationStart = Date.now();
      const donationPayload = JSON.stringify({
        amount: Math.floor(Math.random() * 50000) + 5000, // 5,000 ~ 55,000 KRW
        fire_station_id: Math.floor(Math.random() * 10) + 1,
        message: `K6 load test donation - VU ${__VU}`,
      });

      const donationResponse = http.post(`${BASE_URL}/api/v1/donations`, donationPayload, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${__ENV.TEST_TOKEN || 'test-token'}`,
        },
        tags: { endpoint: 'create_donation' },
      });

      const donationDurationMs = Date.now() - donationStart;
      donationDuration.add(donationDurationMs);
      apiRequests.add(1);

      const donationSuccess = check(donationResponse, {
        'donation status is 201': (r) => r.status === 201,
        'donation response time < 500ms': (r) => r.timings.duration < 500,
        'donation has id': (r) => JSON.parse(r.body).id !== undefined,
      });

      if (!donationSuccess) {
        errorRate.add(1);
      }
    });

    sleep(2); // User waits for confirmation

    // 3. View fire station details
    group('View Fire Station', function() {
      const stationId = Math.floor(Math.random() * 10) + 1;
      const stationResponse = http.get(`${BASE_URL}/api/v1/fire-stations/${stationId}`, {
        tags: { endpoint: 'fire_station' },
      });

      apiRequests.add(1);

      const stationSuccess = check(stationResponse, {
        'station status is 200': (r) => r.status === 200,
        'station response time < 200ms': (r) => r.timings.duration < 200,
      });

      if (!stationSuccess) {
        errorRate.add(1);
      }
    });

    sleep(1);
  });
}

// Teardown function - runs once after test
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Test completed in ${duration}s`);

  // Push final metrics to Prometheus Pushgateway
  const metricsPayload = `
# TYPE k6_test_duration_seconds gauge
k6_test_duration_seconds{scenario="${__ENV.K6_SCENARIO || 'unknown'}"} ${duration}
# TYPE k6_test_end_timestamp gauge
k6_test_end_timestamp{scenario="${__ENV.K6_SCENARIO || 'unknown'}"} ${Date.now() / 1000}
`;

  if (PROMETHEUS_PUSHGATEWAY) {
    http.post(
      `${PROMETHEUS_PUSHGATEWAY}/metrics/job/k6/instance/${__ENV.K6_SCENARIO || 'test'}`,
      metricsPayload,
      { headers: { 'Content-Type': 'text/plain' } }
    );
  }
}

// Custom summary handler
export function handleSummary(data) {
  const summary = {
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };

  // Save summary to JSON file for database insertion
  const jsonSummary = {
    test_id: `k6-${__ENV.K6_SCENARIO || 'test'}-${Date.now()}`,
    scenario_name: __ENV.K6_SCENARIO || 'unknown',
    target_vu: data.root_group.checks ? Object.keys(data.metrics.vus.values).length : 0,
    start_time: new Date(data.state.testRunDurationMs).toISOString(),
    end_time: new Date().toISOString(),
    latency_p50: data.metrics.http_req_duration.values['p(50)'],
    latency_p95: data.metrics.http_req_duration.values['p(95)'],
    latency_p99: data.metrics.http_req_duration.values['p(99)'],
    error_rate: data.metrics.http_req_failed ? data.metrics.http_req_failed.values.rate : 0,
    total_requests: data.metrics.http_reqs ? data.metrics.http_reqs.values.count : 0,
    requests_per_second: data.metrics.http_reqs ? data.metrics.http_reqs.values.rate : 0,
    status: data.metrics.http_req_duration.values['p(95)'] < 500 ? 'passed' : 'failed',
    results_json: data,
  };

  summary['/tmp/k6-summary.json'] = JSON.stringify(jsonSummary, null, 2);

  return summary;
}

// Example K6 Run Commands:
//
// Baseline (50 VU):
// K6_SCENARIO=baseline k6 run --out statsd k6-scenarios.js
//
// Target Load (200 VU - Success Criteria):
// K6_SCENARIO=target k6 run --out statsd k6-scenarios.js
//
// Stress Test (500 VU):
// K6_SCENARIO=stress k6 run --out statsd k6-scenarios.js
//
// Spike Test:
// K6_SCENARIO=spike k6 run --out statsd k6-scenarios.js
//
// With Prometheus statsd-exporter:
// k6 run --out statsd=http://statsd-exporter:8125 k6-scenarios.js
