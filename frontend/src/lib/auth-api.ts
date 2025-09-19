import { apiFetch } from './api-client';

interface SignupPayload {
  email: string;
  password: string;
  name: string;
  phone?: string;
}

interface LoginPayload {
  email: string;
  password: string;
}

export async function signup(payload: SignupPayload) {
  return apiFetch<{ user_id: string; email: string; message: string }>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function login(payload: LoginPayload) {
  return apiFetch<{ user: Record<string, unknown>; access_token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function logout() {
  return apiFetch<{ message: string }>('/auth/logout', { method: 'POST' });
}

export async function refresh() {
  return apiFetch<{ access_token: string }>('/auth/refresh', { method: 'POST' });
}
