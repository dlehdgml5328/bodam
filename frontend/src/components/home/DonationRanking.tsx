'use client';

import { useEffect, useState } from 'react';
import Card from '../base/Card';
import Button from '../base/Button';
import { useRouter } from 'next/navigation';

interface RankingItem {
  rank: number;
  name: string;
  amount: number;
  cups: number;
}

interface RankingsData {
  individual: RankingItem[];
  group: RankingItem[];
  company: RankingItem[];
}

export default function DonationRanking() {
  const router = useRouter();
  const [rankings, setRankings] = useState<RankingsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.bodam.website';
    fetch(`${apiBaseUrl}/rankings?limit=10`)
      .then((res) => res.json())
      .then((data: RankingsData) => {
        setRankings(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Failed to fetch rankings:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">랭킹 데이터 로딩 중...</div>
        </div>
      </section>
    );
  }

  const topRankings = rankings?.individual.slice(0, 10) || [];

  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-12">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">이달의 기부 랭킹 TOP 10</h2>
            <p className="text-lg text-gray-600">소방관들을 위한 따뜻한 마음을 나눠주신 분들을 소개합니다</p>
          </div>
          <Button variant="outline" onClick={() => router.push('/donation-ranking')} className="flex items-center space-x-2">
            <span>전체 보기</span>
            <i className="ri-arrow-right-line"></i>
          </Button>
        </div>

        {topRankings.length === 0 ? (
          <Card className="p-12 text-center">
            <p className="text-gray-500">아직 기부 데이터가 없습니다</p>
          </Card>
        ) : (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">순위</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">기부자</th>
                    <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">기부금액</th>
                    <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">커피잔수</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {topRankings.map((item) => (
                    <tr key={item.rank} className="hover:bg-gray-50 transition-colors duration-150">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          {item.rank <= 3 && (
                            <span className="mr-2 text-2xl">
                              {item.rank === 1 && '🥇'}
                              {item.rank === 2 && '🥈'}
                              {item.rank === 3 && '🥉'}
                            </span>
                          )}
                          <span className="font-semibold text-gray-900">{item.rank}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-medium text-gray-900">{item.name}</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className="text-red-600 font-semibold">{item.amount.toLocaleString()}원</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end space-x-1">
                          <i className="ri-cup-fill text-orange-500"></i>
                          <span className="font-medium text-gray-900">{item.cups}잔</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </section>
  );
}
