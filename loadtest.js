import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 1000,        // 1000 virtual user
  duration: '30s',  // 30 sekund test
};

export default function () {
  const res = http.get('http://localhost:8000/location/location/detail/1');

  check(res, {
    'status is 200': (r) => r.status === 200,
  });
}