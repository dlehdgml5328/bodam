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

export const getEmergencyStations = cache(async (): Promise<EmergencyStation[]> => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!apiBaseUrl) {
    console.warn('[getEmergencyStations] No API base URL configured');
    return [];
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

    return [];
  } catch (error) {
    console.error('[getEmergencyStations] Failed to fetch data', error);
    return [];
  }
});

export async function revalidateEmergencyStations() {
  revalidateTag('emergency-stations');
}
