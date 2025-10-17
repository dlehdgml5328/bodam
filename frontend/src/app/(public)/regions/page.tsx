'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { apiRequest } from '@/lib/api';

type FireIncident = {
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

type StatusFilter = 'all' | 'dispatching' | 'suppressing' | 'contained' | 'resolved';

const STATUS_LABELS: Record<StatusFilter, string> = {
  all: '전체',
  dispatching: '출동 중',
  suppressing: '진압 중',
  contained: '진압 완료',
  resolved: '귀소 완료',
};

const STATUS_BADGE_CLASS: Record<StatusFilter, string> = {
  all: 'bg-gray-100 text-gray-800',
  dispatching: 'bg-orange-100 text-orange-800',
  suppressing: 'bg-red-100 text-red-800',
  contained: 'bg-blue-100 text-blue-800',
  resolved: 'bg-green-100 text-green-800',
};

const numberFormatter = new Intl.NumberFormat('ko-KR');

function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

function formatExactTime(isoString: string | null | undefined): string {
  if (!isoString) {
    return '-';
  }
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: 'Asia/Seoul',
  });
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

// 지역 추출 함수 (location_address에서 시/도 추출)
function extractRegion(address: string): string {
  const match = address.match(/^(서울특별시|부산광역시|대구광역시|인천광역시|광주광역시|대전광역시|울산광역시|세종특별자치시|경기도|강원도|충청북도|충청남도|전라북도|전라남도|경상북도|경상남도|제주특별자치도)/);
  if (match) {
    return match[1].replace('특별시', '').replace('광역시', '').replace('특별자치시', '').replace('특별자치도', '').replace('도', '');
  }
  return '기타';
}

export default function RegionsPage() {
  const router = useRouter();

  const [incidents, setIncidents] = useState<FireIncident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedRegion, setSelectedRegion] = useState('전국');
  const [selectedStatus, setSelectedStatus] = useState<StatusFilter>('all');

  useEffect(() => {
    let active = true;

    async function loadIncidents() {
      setLoading(true);
      setError(null);
      try {
        const data = await apiRequest<FireIncident[]>('/api/incidents/?limit=200');
        if (!active) {
          return;
        }
        setIncidents(data);
      } catch (err) {
        if (!active) {
          return;
        }
        setIncidents([]);
        setError('화재 사고 정보를 불러오지 못했습니다.');
        console.error('[RegionsPage] failed to load incidents', err);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadIncidents();

    return () => {
      active = false;
    };
  }, []);

  // 지역 목록 추출
  const regions = useMemo(() => {
    const unique = new Set(incidents.map((incident) => extractRegion(incident.location_address)));
    const sorted = Array.from(unique).sort((a, b) => a.localeCompare(b, 'ko-KR'));
    return ['전국', ...sorted];
  }, [incidents]);

  // 상태별 카운트
  const statusCounts = useMemo(() => {
    const counts = {
      total: incidents.length,
      dispatching: 0,
      suppressing: 0,
      contained: 0,
      resolved: 0,
    };
    incidents.forEach((incident) => {
      counts[incident.status] += 1;
    });
    return counts;
  }, [incidents]);

  // 지역별 통계
  const regionSummaries = useMemo(() => {
    const summaryMap = new Map<string, any>();
    incidents.forEach((incident) => {
      const region = extractRegion(incident.location_address);
      const current = summaryMap.get(region) || {
        region,
        total: 0,
        dispatching: 0,
        suppressing: 0,
        contained: 0,
        resolved: 0,
      };
      current.total += 1;
      current[incident.status] += 1;
      summaryMap.set(region, current);
    });
    return Array.from(summaryMap.values()).sort((a, b) =>
      a.region.localeCompare(b.region, 'ko-KR'),
    );
  }, [incidents]);

  // 필터링된 사고 목록
  const filteredIncidents = useMemo(
    () =>
      incidents.filter((incident) => {
        const region = extractRegion(incident.location_address);
        if (selectedRegion !== '전국' && region !== selectedRegion) {
          return false;
        }
        if (selectedStatus !== 'all' && incident.status !== selectedStatus) {
          return false;
        }
        return true;
      }),
    [incidents, selectedRegion, selectedStatus],
  );

  const selectedRegionSummary = useMemo(() => {
    if (selectedRegion === '전국') {
      return null;
    }
    return regionSummaries.find((item) => item.region === selectedRegion) || null;
  }, [regionSummaries, selectedRegion]);

  const displayedStats = selectedRegionSummary
    ? {
        total: selectedRegionSummary.total,
        dispatching: selectedRegionSummary.dispatching,
        suppressing: selectedRegionSummary.suppressing,
        contained: selectedRegionSummary.contained,
        resolved: selectedRegionSummary.resolved,
      }
    : statusCounts;

  return (
    <div className="bg-gray-50">
      <section className="py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h1 className="mb-2 text-3xl font-bold text-gray-900">전국 화재 사고 현황</h1>
            <p className="text-lg text-gray-600">실시간 화재 사고 발생 현황과 출동 상황을 확인하세요.</p>
          </div>

          <div className="mb-8 flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">지역</span>
              <select
                value={selectedRegion}
                onChange={(event) => setSelectedRegion(event.target.value)}
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
                onChange={(event) => setSelectedStatus(event.target.value as StatusFilter)}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                {(['all', 'dispatching', 'suppressing', 'contained', 'resolved'] as StatusFilter[]).map((status) => (
                  <option key={status} value={status}>
                    {STATUS_LABELS[status]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-5">
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-gray-900">
                {loading ? '—' : formatNumber(displayedStats.total)}
              </div>
              <div className="text-sm text-gray-600">총 사고</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-orange-600">
                {loading ? '—' : formatNumber(displayedStats.dispatching)}
              </div>
              <div className="text-sm text-gray-600">출동 중</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-red-600">
                {loading ? '—' : formatNumber(displayedStats.suppressing)}
              </div>
              <div className="text-sm text-gray-600">진압 중</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-blue-600">
                {loading ? '—' : formatNumber(displayedStats.contained)}
              </div>
              <div className="text-sm text-gray-600">진압 완료</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-green-600">
                {loading ? '—' : formatNumber(displayedStats.resolved)}
              </div>
              <div className="text-sm text-gray-600">귀소 완료</div>
            </Card>
          </div>

          <Card className="mb-8">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900">실시간 화재 사고 현황</h3>
              <div className="flex items-center space-x-2">
                <div className="h-3 w-3 animate-pulse rounded-full bg-red-500" />
                <span className="text-sm font-medium text-red-600">실시간 업데이트</span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">소방서</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">발생 위치</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">상태</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">사상자</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">발생 시각</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-sm text-gray-500">
                        데이터를 불러오는 중...
                      </td>
                    </tr>
                  )}
                  {!loading && filteredIncidents.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-sm text-gray-500">
                        표시할 사고 정보가 없습니다.
                      </td>
                    </tr>
                  )}
                  {!loading && filteredIncidents.map((incident) => (
                    <tr key={incident.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{incident.title}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{incident.location_address}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${STATUS_BADGE_CLASS[incident.status]}`}
                        >
                          {STATUS_LABELS[incident.status]}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-sm text-gray-700">
                        {incident.casualties_dead > 0 || incident.casualties_injured > 0
                          ? `사망 ${incident.casualties_dead}명, 부상 ${incident.casualties_injured}명`
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-gray-500">
                        {formatExactTime(incident.occurred_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card>
            <h3 className="mb-4 text-lg font-bold text-gray-900">지역별 화재 사고 현황</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">지역</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">총 사고</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">출동 중</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">진압 중</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">진압 완료</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">귀소 완료</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr>
                      <td colSpan={6} className="px-4 py-6 text-center text-sm text-gray-500">
                        데이터를 불러오는 중...
                      </td>
                    </tr>
                  )}
                  {!loading && regionSummaries.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-6 text-center text-sm text-gray-500">
                        지역별 집계 정보가 없습니다.
                      </td>
                    </tr>
                  )}
                  {!loading && regionSummaries.map((region) => (
                    <tr key={region.region} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{region.region}</td>
                      <td className="px-4 py-3 text-center text-sm text-gray-700">{formatNumber(region.total)}</td>
                      <td className="px-4 py-3 text-center text-sm text-orange-600">{formatNumber(region.dispatching)}</td>
                      <td className="px-4 py-3 text-center text-sm text-red-600">{formatNumber(region.suppressing)}</td>
                      <td className="px-4 py-3 text-center text-sm text-blue-600">{formatNumber(region.contained)}</td>
                      <td className="px-4 py-3 text-center text-sm text-green-600">{formatNumber(region.resolved)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}
