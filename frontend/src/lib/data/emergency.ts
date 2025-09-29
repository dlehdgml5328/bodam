import 'server-only';

import { cache } from 'react';
import { revalidateTag } from 'next/cache';

export type EmergencyStation = {
  name: string;
  location: string;
  status: string;
  priority?: 'high' | 'medium' | 'low';
  time: string;
};

const FALLBACK_STATIONS: EmergencyStation[] = [
  {
    name: '서울중부소방서',
    location: '서울시 중구',
    status: '출동 중',
    priority: 'high',
    time: '3분 전',
  },
  {
    name: '부산해운대소방서',
    location: '부산시 해운대구',
    status: '진압 중',
    priority: 'high',
    time: '8분 전',
  },
  {
    name: '대구남부소방서',
    location: '대구시 남구',
    status: '출동 중',
    priority: 'medium',
    time: '12분 전',
  },
];

export const getEmergencyStations = cache(async (): Promise<EmergencyStation[]> => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!apiBaseUrl) {
    return FALLBACK_STATIONS;
  }

  try {
    const response = await fetch(`${apiBaseUrl}/emergency-stations`, {
      next: {
        revalidate: 60,
        tags: ['emergency-stations'],
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch emergency stations: ${response.status}`);
    }

    const data = await response.json();

    if (Array.isArray(data)) {
      return data as EmergencyStation[];
    }

    if (Array.isArray((data as { stations?: EmergencyStation[] }).stations)) {
      return (data as { stations: EmergencyStation[] }).stations;
    }

    return FALLBACK_STATIONS;
  } catch (error) {
    console.error('[getEmergencyStations] falling back to static data', error);
    return FALLBACK_STATIONS;
  }
});

export async function revalidateEmergencyStations() {
  revalidateTag('emergency-stations');
}
