import 'server-only';

import { cache } from 'react';

export type FireIncident = {
  id: string;
  title: string;
  location_address: string;
  latitude: number | null;
  longitude: number | null;
  occurred_at: string;
  status: 'dispatching' | 'suppressing' | 'contained' | 'resolved';
  severity: 'critical' | 'high' | 'medium' | 'low' | null;
  casualties_injured: number;
  casualties_dead: number;
  estimated_damage: number | null;
  source_url: string | null;
  created_at: string;
  updated_at: string;
};

export const getFireIncidents = cache(async (limit: number = 20): Promise<FireIncident[]> => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  try {
    const response = await fetch(`${apiBaseUrl}/api/incidents/?limit=${limit}`, {
      next: {
        revalidate: 30, // 30초마다 재검증
        tags: ['fire-incidents'],
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch fire incidents: ${response.status}`);
    }

    const data = await response.json();
    return data as FireIncident[];
  } catch (error) {
    console.error('[getFireIncidents] Failed to fetch data', error);
    return [];
  }
});

export const getActiveIncidents = cache(async (): Promise<FireIncident[]> => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  try {
    // 출동 중이거나 진압 중인 사고만 가져오기
    const response = await fetch(`${apiBaseUrl}/api/incidents/?limit=10`, {
      next: {
        revalidate: 30,
        tags: ['fire-incidents', 'active-incidents'],
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch active incidents: ${response.status}`);
    }

    const data = await response.json();
    const incidents = data as FireIncident[];

    // 진행 중인 사고만 필터링 (dispatching 또는 suppressing)
    return incidents.filter(
      (incident) => incident.status === 'dispatching' || incident.status === 'suppressing'
    );
  } catch (error) {
    console.error('[getActiveIncidents] Failed to fetch data', error);
    return [];
  }
});
