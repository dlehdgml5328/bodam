'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { apiRequest } from '@/lib/api';

type StationLocation = {
  lat: number | null;
  lng: number | null;
};

type FireStationSummary = {
  id: string;
  name: string;
  address: string;
  phone: string;
  region: string;
  district: string;
  status: 'active' | 'closed' | 'merged';
  total_received: string | number;
  donor_count: number;
  location: StationLocation;
};

type StationsResponse = {
  stations: FireStationSummary[];
  total: number;
  page: number;
  limit: number;
};

type EmergencyIncident = {
  id: string;
  title: string;
  started_at: string | null;
};

type EmergencyStation = {
  station: FireStationSummary;
  status: 'dispatching' | 'suppressing' | 'standby' | 'maintenance';
  status_label: string;
  priority: 'high' | 'medium' | 'low';
  summary: string | null;
  updated_at: string;
  active_incidents: EmergencyIncident[];
};

type EmergencyStationsResponse = {
  as_of: string;
  stations: EmergencyStation[];
};

type StatusFilter = EmergencyStation['status'] | 'all';

type StatusCountMap = {
  dispatching: number;
  suppressing: number;
  standby: number;
  maintenance: number;
};

type RegionSummary = StatusCountMap & {
  region: string;
  total: number;
};

type NearbyStationsResponse = {
  stations: Array<{
    station: FireStationSummary;
    distance: number;
  }>;
};

const STATUS_LABELS: Record<StatusFilter, string> = {
  all: '전체',
  dispatching: '출동 중',
  suppressing: '진압 중',
  standby: '대기 중',
  maintenance: '점검 중',
};

const STATUS_BADGE_CLASS: Record<StatusFilter, string> = {
  all: 'bg-gray-100 text-gray-800',
  dispatching: 'bg-orange-100 text-orange-800',
  suppressing: 'bg-red-100 text-red-800',
  standby: 'bg-green-100 text-green-800',
  maintenance: 'bg-gray-100 text-gray-800',
};

const numberFormatter = new Intl.NumberFormat('ko-KR');

function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) {
    return '-';
  }
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }
  const diff = Date.now() - date.getTime();
  if (diff < 60_000) {
    return '방금 전';
  }
  if (diff < 3_600_000) {
    return `${Math.floor(diff / 60_000)}분 전`;
  }
  if (diff < 86_400_000) {
    return `${Math.floor(diff / 3_600_000)}시간 전`;
  }
  return date.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function RegionsPage() {
  const router = useRouter();

  const [stations, setStations] = useState<FireStationSummary[]>([]);
  const [stationsLoading, setStationsLoading] = useState(true);
  const [stationsError, setStationsError] = useState<string | null>(null);
  const [emergencyStations, setEmergencyStations] = useState<EmergencyStation[]>([]);
  const [emergencyLoading, setEmergencyLoading] = useState(true);
  const [emergencyError, setEmergencyError] = useState<string | null>(null);

  const [selectedRegion, setSelectedRegion] = useState('전국');
  const [selectedStatus, setSelectedStatus] = useState<StatusFilter>('all');
  const [showRegionDetail, setShowRegionDetail] = useState(false);
  const [selectedRegionData, setSelectedRegionData] = useState<RegionSummary | null>(null);

  const [showMultipleDonationModal, setShowMultipleDonationModal] = useState(false);
  const [donationType, setDonationType] = useState<'split' | 'each'>('split');
  const [selectedFireStations, setSelectedFireStations] = useState<string[]>([]);
  const [tempSelectedStations, setTempSelectedStations] = useState<string[]>([]);
  const [multiSearch, setMultiSearch] = useState('');
  const [showRegionModal, setShowRegionModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [nearbyError, setNearbyError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadStations() {
      setStationsLoading(true);
      setStationsError(null);
      try {
        const limit = 200;
        const first = await apiRequest<StationsResponse>(`/stations?limit=${limit}&page=1`);
        if (!active) {
          return;
        }
        let items = [...first.stations];
        let page = 2;
        while (items.length < first.total) {
          const next = await apiRequest<StationsResponse>(`/stations?limit=${limit}&page=${page}`);
          if (!active) {
            return;
          }
          if (next.stations.length === 0) {
            break;
          }
          items = [...items, ...next.stations];
          page += 1;
        }
        setStations(items);
      } catch (error) {
        if (!active) {
          return;
        }
        setStations([]);
        setStationsError('소방서 정보를 불러오지 못했습니다.');
        console.error('[RegionsPage] failed to load stations', error);
      } finally {
        if (active) {
          setStationsLoading(false);
        }
      }
    }

    async function loadEmergencyStations() {
      setEmergencyLoading(true);
      setEmergencyError(null);
      try {
        const response = await apiRequest<EmergencyStationsResponse>('/emergency-stations?limit=200');
        if (!active) {
          return;
        }
        setEmergencyStations(response.stations ?? []);
      } catch (error) {
        if (!active) {
          return;
        }
        setEmergencyStations([]);
        setEmergencyError('긴급 출동 정보를 불러오지 못했습니다.');
        console.error('[RegionsPage] failed to load emergency stations', error);
      } finally {
        if (active) {
          setEmergencyLoading(false);
        }
      }
    }

    loadStations();
    loadEmergencyStations();

    return () => {
      active = false;
    };
  }, []);

  const regions = useMemo(() => {
    const unique = new Set(stations.map((station) => station.region));
    const sorted = Array.from(unique).sort((a, b) => a.localeCompare(b, 'ko-KR'));
    return ['전국', ...sorted];
  }, [stations]);

  useEffect(() => {
    if (selectedRegion !== '전국' && !regions.includes(selectedRegion)) {
      setSelectedRegion('전국');
    }
  }, [regions, selectedRegion]);

  const emergencyStatusMap = useMemo(() => {
    const map = new Map<string, EmergencyStation>();
    emergencyStations.forEach((item) => {
      map.set(item.station.id, item);
    });
    return map;
  }, [emergencyStations]);

  const emergencyCounts = useMemo<StatusCountMap>(() => {
    const counts: StatusCountMap = {
      dispatching: 0,
      suppressing: 0,
      standby: 0,
      maintenance: 0,
    };
    emergencyStations.forEach((item) => {
      counts[item.status] += 1;
    });
    return counts;
  }, [emergencyStations]);

  const totalStats = useMemo(
    () => ({
      totalStations: stations.length,
      dispatching: emergencyCounts.dispatching,
      suppressing: emergencyCounts.suppressing,
      standby: emergencyCounts.standby,
      maintenance: emergencyCounts.maintenance,
    }),
    [stations.length, emergencyCounts],
  );

  const regionSummaries = useMemo<RegionSummary[]>(() => {
    const summaryMap = new Map<string, RegionSummary>();
    stations.forEach((station) => {
      const current =
        summaryMap.get(station.region) ??
        {
          region: station.region,
          total: 0,
          dispatching: 0,
          suppressing: 0,
          standby: 0,
          maintenance: 0,
        };
      current.total += 1;
      const emergency = emergencyStatusMap.get(station.id);
      if (emergency) {
        current[emergency.status] += 1;
      }
      summaryMap.set(station.region, current);
    });
    return Array.from(summaryMap.values()).sort((a, b) =>
      a.region.localeCompare(b.region, 'ko-KR'),
    );
  }, [stations, emergencyStatusMap]);

  const regionDetailMap = useMemo(() => {
    const detail: Record<
      string,
      Array<{
        id: string;
        name: string;
        district: string;
        status: StatusFilter;
        statusLabel: string;
        updatedAt: string | null;
      }>
    > = {};
    stations.forEach((station) => {
      const emergency = emergencyStatusMap.get(station.id);
      const entry = detail[station.region] ?? [];
      entry.push({
        id: station.id,
        name: station.name,
        district: station.district,
        status: emergency?.status ?? 'standby',
        statusLabel:
          emergency?.status_label ?? (station.status === 'active' ? '대기 중' : '정보 없음'),
        updatedAt: emergency?.updated_at ?? null,
      });
      detail[station.region] = entry;
    });
    Object.values(detail).forEach((list) => {
      list.sort((a, b) => a.name.localeCompare(b.name, 'ko-KR'));
    });
    return detail;
  }, [stations, emergencyStatusMap]);

  const emergencyIncidents = useMemo(
    () =>
      [...emergencyStations]
        .sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
        )
        .map((item) => ({
          id: item.station.id,
          region: item.station.region,
          station: item.station.name,
          location: item.station.address,
          status: item.status,
          statusLabel: item.status_label,
          updatedAt: item.updated_at,
        })),
    [emergencyStations],
  );

  const monthlyStats = useMemo(() => {
    const counts = new Map<string, number>();
    emergencyStations.forEach((item) => {
      const updated = new Date(item.updated_at);
      if (Number.isNaN(updated.getTime())) {
        return;
      }
      const key = `${updated.getFullYear()}-${String(updated.getMonth() + 1).padStart(2, '0')}`;
      counts.set(key, (counts.get(key) ?? 0) + 1);
    });
    return Array.from(counts.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([key, incidents]) => {
        const [year, month] = key.split('-');
        return {
          month: `${year}년 ${month}월`,
          incidents,
        };
      });
  }, [emergencyStations]);

  const stationsForSelection = useMemo(() => {
    let list = [...stations];
    if (multiSearch) {
      const keyword = multiSearch.trim().toLowerCase();
      list = list.filter(
        (station) =>
          station.name.toLowerCase().includes(keyword) ||
          station.region.toLowerCase().includes(keyword) ||
          station.district.toLowerCase().includes(keyword),
      );
    }
    return list.sort((a, b) => a.name.localeCompare(b.name, 'ko-KR'));
  }, [stations, multiSearch]);

  const allSelected = useMemo(() => {
    if (stationsForSelection.length === 0) {
      return false;
    }
    return stationsForSelection.every((station) => tempSelectedStations.includes(station.name));
  }, [stationsForSelection, tempSelectedStations]);

  const handleRegionFilterChange = useCallback((value: string) => {
    setSelectedRegion(value);
  }, []);

  const handleStatusFilterChange = useCallback((value: StatusFilter) => {
    setSelectedStatus(value);
  }, []);

  const handleRegionClick = useCallback((summary: RegionSummary) => {
    setSelectedRegionData(summary);
    setShowRegionDetail(true);
  }, []);

  const handleDonateClick = useCallback(
    (stationName: string) => {
      router.push(`/donations?station=${encodeURIComponent(stationName)}`);
    },
    [router],
  );

  const handleMultipleDonationClick = useCallback(() => {
    setTempSelectedStations(selectedFireStations);
    setMultiSearch('');
    setShowMultipleDonationModal(true);
  }, [selectedFireStations]);

  const handleTempStationToggle = useCallback((stationName: string) => {
    setTempSelectedStations((prev) => {
      if (prev.includes(stationName)) {
        return prev.filter((name) => name !== stationName);
      }
      return [...prev, stationName];
    });
  }, []);

  const handleSelectAllStations = useCallback(() => {
    if (allSelected) {
      setTempSelectedStations([]);
    } else {
      setTempSelectedStations(stationsForSelection.map((station) => station.name));
    }
  }, [allSelected, stationsForSelection]);

  const handleSelectRegionStations = useCallback(
    (region: string) => {
      const regionStations = regionDetailMap[region]?.map((station) => station.name) ?? [];
      if (regionStations.length === 0) {
        return;
      }
      setTempSelectedStations((prev) => [
        ...new Set([...prev, ...regionStations]),
      ]);
      setShowRegionModal(false);
    },
    [regionDetailMap],
  );

  const handleConfirmMultipleDonation = useCallback(() => {
    if (tempSelectedStations.length === 0) {
      alert('최소 1개 이상의 소방서를 선택해주세요.');
      return;
    }
    setSelectedFireStations(tempSelectedStations);
    const stationsParam = encodeURIComponent(tempSelectedStations.join(','));
    router.push(`/donations?stations=${stationsParam}&type=${donationType}`);
    setShowMultipleDonationModal(false);
  }, [donationType, router, tempSelectedStations]);

  const handleLocationSelect = useCallback(() => {
    if (!navigator.geolocation) {
      alert('위치 서비스를 지원하지 않는 브라우저입니다.');
      return;
    }
    setShowLocationModal(true);
    setLocationLoading(true);
    setNearbyError(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const response = await apiRequest<NearbyStationsResponse>(
            `/stations/nearby?lat=${latitude}&lng=${longitude}&radius=5000&limit=10`,
          );
          const nearbyNames =
            response.stations?.map((item) => item.station.name) ?? [];
          if (nearbyNames.length === 0) {
            setNearbyError('주변에 등록된 소방서를 찾지 못했습니다.');
          } else {
            setTempSelectedStations((prev) => [
              ...new Set([...prev, ...nearbyNames]),
            ]);
          }
        } catch (error) {
          console.error('[RegionsPage] failed to fetch nearby stations', error);
          setNearbyError('주변 소방서를 불러오지 못했습니다.');
        } finally {
          setLocationLoading(false);
        }
      },
      (error) => {
        console.error('[RegionsPage] failed to get location', error);
        setNearbyError('위치 정보를 가져올 수 없습니다. 권한을 확인해주세요.');
        setLocationLoading(false);
      },
    );
  }, []);

  const selectedRegionSummary = useMemo(() => {
    if (selectedRegion === '전국') {
      return null;
    }
    return regionSummaries.find((item) => item.region === selectedRegion) ?? null;
  }, [regionSummaries, selectedRegion]);

  const displayedStats = selectedRegionSummary
    ? {
        totalStations: selectedRegionSummary.total,
        dispatching: selectedRegionSummary.dispatching,
        suppressing: selectedRegionSummary.suppressing,
        standby: selectedRegionSummary.standby,
        maintenance: selectedRegionSummary.maintenance,
      }
    : totalStats;

  const filteredIncidents = useMemo(
    () =>
      emergencyIncidents.filter((incident) => {
        if (selectedRegion !== '전국' && incident.region !== selectedRegion) {
          return false;
        }
        if (selectedStatus !== 'all' && incident.status !== selectedStatus) {
          return false;
        }
        return true;
      }),
    [emergencyIncidents, selectedRegion, selectedStatus],
  );

  return (
    <div className="bg-gray-50">
      <section className="py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h1 className="mb-2 text-3xl font-bold text-gray-900">전국 소방서 현황</h1>
            <p className="text-lg text-gray-600">실시간 소방서 운영 현황과 출동 상황을 확인하세요.</p>
          </div>

          <div className="mb-8 flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">지역</span>
              <select
                value={selectedRegion}
                onChange={(event) => handleRegionFilterChange(event.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                {regions.map((region) => (
                  <option key={region} value={region}>
                    {region}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">상태</span>
              <select
                value={selectedStatus}
                onChange={(event) => handleStatusFilterChange(event.target.value as StatusFilter)}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                {(['all', 'dispatching', 'suppressing', 'standby', 'maintenance'] as StatusFilter[]).map((status) => (
                  <option key={status} value={status}>
                    {STATUS_LABELS[status]}
                  </option>
                ))}
              </select>
            </div>
            <div className="ml-auto">
              <Button
                onClick={handleMultipleDonationClick}
                className="bg-red-600 text-white hover:bg-red-700"
              >
                <i className="ri-heart-line mr-2" />
                여러 소방서에 기부하기
              </Button>
            </div>
          </div>

          {(stationsError || emergencyError) && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {stationsError && <div>{stationsError}</div>}
              {emergencyError && <div>{emergencyError}</div>}
            </div>
          )}

          <div className="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-gray-900">
                {stationsLoading ? '—' : formatNumber(displayedStats.totalStations)}
              </div>
              <div className="text-sm text-gray-600">총 소방서</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-orange-600">
                {emergencyLoading ? '—' : formatNumber(displayedStats.dispatching)}
              </div>
              <div className="text-sm text-gray-600">출동 중</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-red-600">
                {emergencyLoading ? '—' : formatNumber(displayedStats.suppressing)}
              </div>
              <div className="text-sm text-gray-600">진압 중</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-green-600">
                {emergencyLoading ? '—' : formatNumber(displayedStats.standby)}
              </div>
              <div className="text-sm text-gray-600">대기 중</div>
            </Card>
          </div>

          <Card className="mb-8">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900">실시간 출동 현황</h3>
              <div className="flex items-center space-x-2">
                <div className="h-3 w-3 animate-pulse rounded-full bg-red-500" />
                <span className="text-sm font-medium text-red-600">실시간 업데이트</span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">지역</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">소방서</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">주소</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">상태</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">업데이트</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIncidents.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-sm text-gray-500">
                        표시할 출동 정보가 없습니다.
                      </td>
                    </tr>
                  )}
                  {filteredIncidents.map((incident) => (
                    <tr key={incident.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{incident.region}</td>
                      <td className="px-4 py-3 text-gray-700">{incident.station}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{incident.location}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${STATUS_BADGE_CLASS[incident.status]}`}
                        >
                          {incident.statusLabel}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-gray-500">
                        {formatRelativeTime(incident.updatedAt)}
                      </td>
                    </tr>
                  ))}
                </tbody>
          </table>
        </div>
      </Card>

          <Card className="mb-8">
            <h3 className="mb-4 text-lg font-bold text-gray-900">월별 출동 현황</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">구분</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">출동 건수</th>
                  </tr>
                </thead>
                <tbody>
                  {monthlyStats.length === 0 && (
                    <tr>
                      <td colSpan={2} className="px-4 py-6 text-center text-sm text-gray-500">
                        아직 집계된 출동 정보가 없습니다.
                      </td>
                    </tr>
                  )}
                  {monthlyStats.map((stat) => (
                    <tr key={stat.month} className="border-b border-gray-100">
                      <td className="px-4 py-3 font-medium text-gray-900">{stat.month}</td>
                      <td className="px-4 py-3 text-right text-sm text-gray-700">
                        {formatNumber(stat.incidents)}건
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card>
            <h3 className="mb-4 text-lg font-bold text-gray-900">지역별 소방서 현황</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">지역</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">총 소방서</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">출동 중</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">진압 중</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">대기 중</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">점검 중</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">액션</th>
                  </tr>
                </thead>
                <tbody>
                  {regionSummaries.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-4 py-6 text-center text-sm text-gray-500">
                        지역별 집계 정보가 없습니다.
                      </td>
                    </tr>
                  )}
                  {regionSummaries.map((region) => (
                    <tr key={region.region} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{region.region}</td>
                      <td className="px-4 py-3 text-center text-sm text-gray-700">{formatNumber(region.total)}</td>
                      <td className="px-4 py-3 text-center text-sm text-orange-600">{formatNumber(region.dispatching)}</td>
                      <td className="px-4 py-3 text-center text-sm text-red-600">{formatNumber(region.suppressing)}</td>
                      <td className="px-4 py-3 text-center text-sm text-green-600">{formatNumber(region.standby)}</td>
                      <td className="px-4 py-3 text-center text-sm text-gray-600">{formatNumber(region.maintenance)}</td>
                      <td className="px-4 py-3 text-center">
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs"
                          onClick={() => handleRegionClick(region)}
                        >
                          현황 보기
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </section>

      {showRegionDetail && selectedRegionData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-xl bg-white p-8 shadow-2xl">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">
                  {selectedRegionData.region} 소방서 현황
                </h3>
                <p className="mt-1 text-sm text-gray-600">
                  총 {formatNumber(selectedRegionData.total)}개 소방서 • 출동 중 {formatNumber(selectedRegionData.dispatching)}개 • 진압 중 {formatNumber(selectedRegionData.suppressing)}개 • 대기 중 {formatNumber(selectedRegionData.standby)}개 • 점검 중 {formatNumber(selectedRegionData.maintenance)}개
                </p>
              </div>
              <button
                onClick={() => setShowRegionDetail(false)}
                className="text-gray-400 transition-colors duration-200 hover:text-gray-600"
              >
                <i className="ri-close-line text-2xl" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200 bg-gray-50">
                    <th className="px-4 py-4 text-left text-sm font-semibold text-gray-900">소방서명</th>
                    <th className="px-4 py-4 text-left text-sm font-semibold text-gray-900">지역</th>
                    <th className="px-4 py-4 text-left text-sm font-semibold text-gray-900">현재 상태</th>
                    <th className="px-4 py-4 text-left text-sm font-semibold text-gray-900">업데이트</th>
                    <th className="px-4 py-4 text-center text-sm font-semibold text-gray-900">지원하기</th>
                  </tr>
                </thead>
                <tbody>
                  {(regionDetailMap[selectedRegionData.region] ?? []).map((station) => (
                    <tr key={station.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-4 font-medium text-gray-900">{station.name}</td>
                      <td className="px-4 py-4 text-sm text-gray-600">{station.district}</td>
                      <td className="px-4 py-4">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${STATUS_BADGE_CLASS[station.status]}`}
                        >
                          {station.statusLabel}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">
                        {formatRelativeTime(station.updatedAt)}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <Button size="sm" variant="outline" onClick={() => handleDonateClick(station.name)}>
                          기부하기
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {showMultipleDonationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-xl bg-white p-8 shadow-2xl">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">여러 소방서에 기부하기</h3>
                <p className="mt-1 text-sm text-gray-600">기부할 소방서를 선택하고 기부 방식을 정해주세요.</p>
              </div>
              <button
                onClick={() => setShowMultipleDonationModal(false)}
                className="text-gray-400 transition-colors duration-200 hover:text-gray-600"
              >
                <i className="ri-close-line text-2xl" />
              </button>
            </div>

            <div className="mb-6 rounded-lg bg-blue-50 p-4">
              <h4 className="mb-3 font-medium text-blue-900">기부 방식 선택</h4>
              <div className="space-y-3">
                <label className="flex cursor-pointer items-start space-x-3">
                  <input
                    type="radio"
                    name="donationType"
                    value="split"
                    checked={donationType === 'split'}
                    onChange={(event) => setDonationType(event.target.value as 'split' | 'each')}
                    className="mt-0.5 h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <span className="font-medium text-blue-900">분할 기부</span>
                    <p className="text-sm text-blue-700">선택한 금액을 소방서 수로 나누어 기부합니다.</p>
                  </div>
                </label>
                <label className="flex cursor-pointer items-start space-x-3">
                  <input
                    type="radio"
                    name="donationType"
                    value="each"
                    checked={donationType === 'each'}
                    onChange={(event) => setDonationType(event.target.value as 'split' | 'each')}
                    className="mt-0.5 h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <span className="font-medium text-blue-900">각각 기부</span>
                    <p className="text-sm text-blue-700">선택한 모든 소방서에 동일 금액을 기부합니다.</p>
                  </div>
                </label>
              </div>
            </div>

            <div className="mb-6 flex flex-wrap items-center gap-3">
              <Button
                variant="outline"
                className="flex items-center"
                onClick={handleSelectAllStations}
              >
                <i className="ri-checkbox-multiple-line mr-2" />
                {allSelected ? '전체 해제' : '전체 선택'}
              </Button>
              <Button
                variant="outline"
                className="flex items-center"
                onClick={() => setShowRegionModal(true)}
              >
                <i className="ri-map-pin-line mr-2" />
                지역별 선택
              </Button>
              <Button
                variant="outline"
                className="flex items-center"
                onClick={handleLocationSelect}
              >
                <i className="ri-compass-3-line mr-2" />
                내 주변에서 찾기
              </Button>
              <div className="ml-auto">
                <input
                  type="search"
                  value={multiSearch}
                  onChange={(event) => setMultiSearch(event.target.value)}
                  placeholder="소방서명 또는 지역 검색"
                  className="w-64 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {tempSelectedStations.length > 0 && (
              <div className="mb-4 rounded-lg border border-blue-100 bg-blue-50 p-3">
                <div className="mb-2 text-sm font-medium text-blue-800">
                  선택된 소방서 ({tempSelectedStations.length}개)
                </div>
                <div className="flex flex-wrap gap-2">
                  {tempSelectedStations.map((station) => (
                    <span key={station} className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800">
                      {station}
                      <button
                        onClick={() => handleTempStationToggle(station)}
                        className="ml-1 text-blue-600 hover:text-blue-800"
                      >
                        <i className="ri-close-line text-sm" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="overflow-hidden rounded-lg border border-gray-200">
              <div className="max-h-96 overflow-y-auto">
                <table className="w-full">
                  <thead className="sticky top-0 bg-gray-50">
                    <tr>
                      <th className="w-12 px-4 py-3">
                        <input
                          type="checkbox"
                          checked={allSelected && stationsForSelection.length > 0}
                          onChange={handleSelectAllStations}
                          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">소방서명</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">지역</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {stationsForSelection.map((station) => {
                      const isSelected = tempSelectedStations.includes(station.name);
                      return (
                        <tr
                          key={station.id}
                          className={`cursor-pointer transition-colors duration-200 hover:bg-gray-50 ${
                            isSelected ? 'bg-blue-50' : ''
                          }`}
                          onClick={() => handleTempStationToggle(station.name)}
                        >
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleTempStationToggle(station.name)}
                              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                          </td>
                          <td className="px-4 py-3 font-medium text-gray-900">{station.name}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {station.region} {station.district}
                          </td>
                        </tr>
                      );
                    })}
                    {stationsForSelection.length === 0 && (
                      <tr>
                        <td colSpan={3} className="px-4 py-6 text-center text-sm text-gray-500">
                          조건에 맞는 소방서를 찾을 수 없습니다.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <Button variant="outline" onClick={() => setShowMultipleDonationModal(false)}>
                취소
              </Button>
              <Button onClick={handleConfirmMultipleDonation}>선택한 소방서로 진행</Button>
            </div>
          </div>
        </div>
      )}

      {showRegionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h4 className="text-lg font-semibold text-gray-900">지역 선택</h4>
              <button
                onClick={() => setShowRegionModal(false)}
                className="text-gray-400 transition-colors duration-200 hover:text-gray-600"
              >
                <i className="ri-close-line text-xl" />
              </button>
            </div>
            <div className="grid gap-2">
              {regions
                .filter((region) => region !== '전국')
                .map((region) => (
                  <button
                    key={region}
                    onClick={() => handleSelectRegionStations(region)}
                    className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-700 transition-colors duration-200 hover:border-blue-400 hover:text-blue-600"
                  >
                    {region}
                  </button>
                ))}
            </div>
          </div>
        </div>
      )}

      {showLocationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl">
            <div className="mb-2 text-lg font-semibold text-gray-900">내 주변 소방서 찾기</div>
            <p className="mb-4 text-sm text-gray-600">
              현재 위치를 기반으로 주변 소방서를 조회합니다.
            </p>
            {locationLoading ? (
              <div className="flex items-center space-x-2 text-sm text-gray-700">
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500" />
                <span>주변 소방서를 검색 중입니다...</span>
              </div>
            ) : nearbyError ? (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {nearbyError}
              </div>
            ) : (
              <div className="mb-4 text-sm text-green-700">
                주변 소방서가 선택 목록에 추가되었습니다.
              </div>
            )}
            <div className="mt-6 flex justify-end">
              <Button variant="outline" onClick={() => setShowLocationModal(false)}>
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
