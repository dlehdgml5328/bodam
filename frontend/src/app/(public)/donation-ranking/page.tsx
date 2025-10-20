'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { apiRequest } from '@/lib/api';

type RankingItem = {
  rank: number;
  name: string;
  amount: number;
  cups: number;
};

type RankingsResponse = {
  individual: RankingItem[];
};

type DashboardStats = {
  total_amount: number;
  total_cups: number;
  total_fire_stations: number;
  total_users: number;
};


const currencyFormatter = new Intl.NumberFormat('ko-KR');

function formatCurrency(amount: number): string {
  return `₩${currencyFormatter.format(amount)}`;
}

function formatNumber(value: number): string {
  return currencyFormatter.format(value);
}

export default function DonationRankingPage() {
  const router = useRouter();
  const [rankings, setRankings] = useState<RankingsResponse | null>(null);
  const [rankingsLoading, setRankingsLoading] = useState(true);
  const [rankingsError, setRankingsError] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [limit, setLimit] = useState(10);

  useEffect(() => {
    let active = true;

    async function loadRankings() {
      setRankingsLoading(true);
      setRankingsError(null);
      try {
        const response = await apiRequest<RankingsResponse>(`/rankings?limit=${limit}`);
        if (!active) {
          return;
        }
        setRankings(response);
      } catch (error) {
        console.error('[DonationRankingPage] failed to load rankings', error);
        if (active) {
          setRankings(null);
          setRankingsError('기부 랭킹을 불러오지 못했습니다.');
        }
      } finally {
        if (active) {
          setRankingsLoading(false);
        }
      }
    }

    loadRankings();

    return () => {
      active = false;
    };
  }, [limit]);

  useEffect(() => {
    let active = true;

    async function loadStats() {
      setStatsLoading(true);
      setStatsError(null);
      try {
        const response = await apiRequest<DashboardStats>('/stats');
        if (!active) {
          return;
        }
        setStats(response);
      } catch (error) {
        console.error('[DonationRankingPage] failed to load stats', error);
        if (active) {
          setStats(null);
          setStatsError('요약 지표를 불러오지 못했습니다.');
        }
      } finally {
        if (active) {
          setStatsLoading(false);
        }
      }
    }

    loadStats();

    return () => {
      active = false;
    };
  }, []);

  const currentRankings = useMemo(() => {
    if (!rankings) {
      return [];
    }
    return rankings.individual ?? [];
  }, [rankings]);

  const handleDonateClick = () => {
    router.push('/donations');
  };

  return (
    <div className="bg-gray-50">
      <section className="py-8">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h1 className="mb-2 text-3xl font-bold text-gray-900">기부 랭킹</h1>
            <p className="text-lg text-gray-600">
              실제 기부 데이터를 기반으로 개인 기부 순위를 확인하세요.
            </p>
          </div>

          {(statsError || rankingsError) && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {statsError && <div>{statsError}</div>}
              {rankingsError && <div>{rankingsError}</div>}
            </div>
          )}

          <div className="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-gray-900">
                {statsLoading || !stats ? '—' : formatCurrency(stats.total_amount)}
              </div>
              <div className="text-sm text-gray-600">누적 기부 금액</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-amber-600">
                {statsLoading || !stats ? '—' : formatNumber(stats.total_cups)}
              </div>
              <div className="text-sm text-gray-600">누적 커피 잔수</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-blue-600">
                {statsLoading || !stats ? '—' : formatNumber(stats.total_users)}
              </div>
              <div className="text-sm text-gray-600">참여 시민 수</div>
            </Card>
            <Card className="text-center">
              <div className="mb-1 text-2xl font-bold text-green-600">
                {statsLoading || !stats ? '—' : formatNumber(stats.total_fire_stations)}
              </div>
              <div className="text-sm text-gray-600">지원한 소방서 수</div>
            </Card>
          </div>

          <Card className="mb-8">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
              <h2 className="text-xl font-bold text-gray-900">개인 기부 순위</h2>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">표시할 개수</span>
                <select
                  value={limit}
                  onChange={(event) => setLimit(Number(event.target.value))}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  {[10, 25, 50, 100].map((value) => (
                    <option key={value} value={value}>
                      상위 {value}명
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">순위</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">이름</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">총 기부 금액</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">커피 잔수</th>
                  </tr>
                </thead>
                <tbody>
                  {rankingsLoading ? (
                    <tr>
                      <td colSpan={4} className="px-4 py-6 text-center text-sm text-gray-500">
                        랭킹을 불러오는 중입니다...
                      </td>
                    </tr>
                  ) : currentRankings.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-4 py-6 text-center text-sm text-gray-500">
                        표시할 랭킹 데이터가 없습니다.
                      </td>
                    </tr>
                  ) : (
                    currentRankings.map((item) => (
                      <tr key={`individual-${item.rank}`} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-semibold text-gray-900">{item.rank}</td>
                        <td className="px-4 py-3 text-sm text-gray-700">{item.name}</td>
                        <td className="px-4 py-3 text-right text-sm font-medium text-gray-900">
                          {formatCurrency(item.amount)}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-gray-600">{formatNumber(item.cups)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          <Card>
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">기부에 참여하고 싶으신가요?</h3>
                <p className="text-sm text-gray-600">
                  소방관 분들에게 따뜻한 커피 한 잔을 전하는 일에 함께해주세요.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button onClick={handleDonateClick} className="bg-red-600 text-white hover:bg-red-700">
                  <i className="ri-heart-line mr-2" />
                  지금 기부하기
                </Button>
                <Button
                  variant="outline"
                  onClick={() => router.push('/regions')}
                >
                  지원 가능한 소방서 보기
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}
