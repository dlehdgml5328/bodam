import { useMemo } from 'react';

export interface StationCoordinate {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  donationStatus?: string;
}

interface StationMapProps {
  stations: StationCoordinate[];
  onSelect?: (stationId: string) => void;
}

export function StationMap({ stations, onSelect }: StationMapProps) {
  const stationList = useMemo(
    () =>
      stations.map((station) => (
        <button
          key={station.id}
          type="button"
          onClick={() => onSelect?.(station.id)}
          className="flex w-full flex-col items-start gap-1 rounded border border-slate-200 bg-white p-4 text-left transition hover:border-primary"
        >
          <span className="font-medium text-slate-900">{station.name}</span>
          <span className="text-xs text-slate-500">
            {station.latitude.toFixed(4)}, {station.longitude.toFixed(4)}
          </span>
          {station.donationStatus ? (
            <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">
              {station.donationStatus}
            </span>
          ) : null}
        </button>
      )),
    [stations, onSelect]
  );

  return (
    <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
      <div className="relative h-80 rounded-lg bg-gradient-to-br from-slate-200 via-slate-100 to-slate-200">
        <div className="absolute inset-4 rounded-lg border border-dashed border-slate-400 bg-white/70 p-4">
          <p className="text-sm text-slate-500">
            지도 렌더링은 Naver Maps SDK 통합 시 구현됩니다.
          </p>
        </div>
      </div>
      <div className="flex flex-col gap-2 overflow-y-auto">{stationList}</div>
    </div>
  );
}
