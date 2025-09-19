import { apiFetch } from './api-client';

export async function listStations(params?: { region?: string; district?: string; search?: string }) {
  const query = new URLSearchParams();
  if (params?.region) query.set('region', params.region);
  if (params?.district) query.set('district', params.district);
  if (params?.search) query.set('search', params.search);
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return apiFetch(`/stations${suffix}`);
}

export async function listNearbyStations(params: { lat: number; lng: number; radius?: number }) {
  const query = new URLSearchParams({ lat: String(params.lat), lng: String(params.lng) });
  if (params.radius) query.set('radius', String(params.radius));
  return apiFetch(`/stations/nearby?${query.toString()}`);
}

export async function getStation(stationId: string) {
  return apiFetch(`/stations/${stationId}`);
}

export async function getStationRankings(stationId: string, period: string = 'all_time') {
  return apiFetch(`/stations/${stationId}/rankings?period=${period}`);
}

export async function getStationIncidents(stationId: string, days: number = 7) {
  return apiFetch(`/stations/${stationId}/incidents?days=${days}`);
}

export async function addFavoriteStation(stationId: string) {
  return apiFetch(`/stations/${stationId}/favorites`, { method: 'POST' });
}

export async function removeFavoriteStation(stationId: string) {
  return apiFetch(`/stations/${stationId}/favorites`, { method: 'DELETE' });
}
