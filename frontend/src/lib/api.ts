const DEFAULT_API_BASE_URL = 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '');

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  const headers = new Headers(options.headers);

  if (shouldSendCsrf(options.method)) {
    const csrf = readCsrfToken();
    if (csrf) {
      headers.set('X-CSRF-Token', csrf);
    }
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  let data: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    const message =
      typeof data === 'object' && data && 'detail' in data
        ? String((data as Record<string, unknown>).detail)
        : '요청을 처리할 수 없습니다.';
    throw new ApiError(message, response.status, data);
  }

  return data as T;
}

export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return sessionStorage.getItem('bodam_access_token');
}

export function buildPaymentHeaders(): HeadersInit {
  const token = getAccessToken();
  if (!token) {
    throw new Error('결제 API를 호출하려면 로그인 후 발급된 access_token이 필요합니다.');
  }
  return { Authorization: `Bearer ${token}` };
}

function shouldSendCsrf(method?: string): boolean {
  if (!method) {
    return false;
  }
  return !SAFE_METHODS.has(method.toUpperCase());
}

function readCsrfToken(): string {
  if (typeof document === 'undefined') {
    return '';
  }
  const match = document.cookie.match(/bodam_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}
