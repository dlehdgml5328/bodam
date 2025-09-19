import { apiFetch } from './api-client';

export interface CreateDonationPayload {
  fire_station_id: string;
  amount: number;
  type: 'one_time' | 'recurring';
  frequency?: 'monthly' | 'yearly';
  message?: string;
  is_anonymous?: boolean;
}

export async function listDonations() {
  return apiFetch('/donations');
}

export async function createDonation(payload: CreateDonationPayload) {
  return apiFetch('/donations', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getDonation(donationId: string) {
  return apiFetch(`/donations/${donationId}`);
}

export async function downloadReceipt(donationId: string) {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'}/donations/${donationId}/receipt`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('영수증을 다운로드할 수 없습니다');
  }
  return response.blob();
}

export async function requestRefund(donationId: string, reason: string) {
  return apiFetch(`/donations/${donationId}/refund`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function listSubscriptions() {
  return apiFetch('/subscriptions');
}

export async function cancelSubscription(subscriptionId: string) {
  return apiFetch(`/subscriptions/${subscriptionId}/cancel`, { method: 'POST' });
}
