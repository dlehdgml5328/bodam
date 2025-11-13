const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.bodam.website';

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

let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

async function refreshAccessToken(): Promise<void> {
  const refreshUrl = `${apiBaseUrl}/auth/refresh`;

  const response = await fetch(refreshUrl, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    // Refresh token도 만료됨 - 로그인 페이지로 이동
    if (typeof window !== 'undefined') {
      localStorage.removeItem('isLoggedIn');
      localStorage.removeItem('loggedInEmail');
      localStorage.removeItem('loggedInName');
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
    }
    throw new Error('세션이 만료되었습니다. 다시 로그인해주세요.');
  }

  const data = await response.json();

  // 새 access token과 csrf token을 sessionStorage에 저장
  if (typeof window !== 'undefined' && data.access_token && data.csrf_token) {
    sessionStorage.setItem('bodam_access_token', data.access_token);
    sessionStorage.setItem('bodam_csrf_token', data.csrf_token);
  }
}

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

  let response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  // 401 Unauthorized - 토큰 만료 가능성
  if (response.status === 401 && !path.includes('/auth/')) {
    // 이미 refresh 중이면 기다림
    if (isRefreshing && refreshPromise) {
      await refreshPromise;
    } else {
      isRefreshing = true;
      refreshPromise = refreshAccessToken();

      try {
        await refreshPromise;
      } catch (error) {
        isRefreshing = false;
        refreshPromise = null;
        throw error;
      }

      isRefreshing = false;
      refreshPromise = null;
    }

    // 토큰 갱신 후 재시도
    const newCsrf = readCsrfToken();
    if (newCsrf && shouldSendCsrf(options.method)) {
      headers.set('X-CSRF-Token', newCsrf);
    }

    response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
    });
  }

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
