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
  // 서버 사이드에서는 API_BASE_URL, 클라이언트에서는 NEXT_PUBLIC_API_BASE_URL 사용
  const apiBaseUrl = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

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
  // 서버 사이드에서는 API_BASE_URL, 클라이언트에서는 NEXT_PUBLIC_API_BASE_URL 사용
  const apiBaseUrl = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  try {
    // 출동 중(dispatching)과 진압 중(suppressing) 사고를 각각 가져와서 합치기
    const [dispatchingResponse, suppressingResponse] = await Promise.all([
      fetch(`${apiBaseUrl}/api/incidents/?status=dispatching&limit=50`, {
        next: {
          revalidate: 30,
          tags: ['fire-incidents', 'active-incidents'],
        },
      }),
      fetch(`${apiBaseUrl}/api/incidents/?status=suppressing&limit=50`, {
        next: {
          revalidate: 30,
          tags: ['fire-incidents', 'active-incidents'],
        },
      }),
    ]);

    if (!dispatchingResponse.ok || !suppressingResponse.ok) {
      throw new Error(`Failed to fetch active incidents`);
    }

    const [dispatchingData, suppressingData] = await Promise.all([
      dispatchingResponse.json(),
      suppressingResponse.json(),
    ]);

    // 두 결과를 합쳐서 반환
    return [...dispatchingData, ...suppressingData] as FireIncident[];
  } catch (error) {
    console.error('[getActiveIncidents] Failed to fetch data', error);
    return [];
  }
});
