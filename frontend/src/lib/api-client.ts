const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface ApiRequestOptions extends RequestInit {
  method?: HttpMethod;
  retry?: boolean;
}

export async function apiFetch<TResponse>(path: string, options: ApiRequestOptions = {}): Promise<TResponse> {
  const { retry = false, headers, ...rest } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    ...rest,
  });

  if (!response.ok) {
    if (response.status === 401 && !retry) {
      await refreshToken();
      return apiFetch<TResponse>(path, { ...options, retry: true });
    }

    const detail = await safeParse(response);
    throw new Error(detail?.message ?? 'API 요청에 실패했습니다');
  }

  return (await safeParse(response)) as TResponse;
}

async function refreshToken() {
  try {
    await fetch(`${API_BASE_URL}/auth/refresh`, { method: 'POST', credentials: 'include' });
  } catch (error) {
    console.error('Failed to refresh token', error);
  }
}

async function safeParse(response: Response) {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}
