import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 50 },   // 50 VUs로 램프업
    { duration: '1m', target: 100 },   // 100 VUs 유지
    { duration: '30s', target: 0 },    // 램프다운
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],  // 95%가 5초 이내
    http_req_failed: ['rate<0.01'],     // 에러율 1% 미만
  },
};

export default function() {
  // DB 조회 API 호출 (DB 연결 풀 테스트)
  let res1 = http.get('http://localhost:8080/api/health');
  check(res1, {
    'health check status is 200': (r) => r.status === 200
  });

  // 외부 API 호출 시뮬레이션 (HTTP 연결 풀 테스트)
  // TODO: 실제 외부 API 엔드포인트로 교체
  // let res2 = http.get('http://localhost:8080/api/external/test');
  // check(res2, {
  //   'external API status is 200': (r) => r.status === 200
  // });

  sleep(1);
}
