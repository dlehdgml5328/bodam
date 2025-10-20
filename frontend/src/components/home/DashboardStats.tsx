'use client';

import { useEffect, useState } from 'react';
import Card from '../base/Card';
import Button from '../base/Button';
import { useRouter } from 'next/navigation';

interface StatsData {
  total_amount: number;
  total_cups: number;
  total_fire_stations: number;
  total_users: number;
}

export default function DashboardStats() {
  const router = useRouter();
  const [statsData, setStatsData] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // API에서 통계 데이터 가져오기
    fetch('http://localhost:8000/stats')
      .then((res) => res.json())
      .then((data: StatsData) => {
        setStatsData(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Failed to fetch stats:', error);
        setLoading(false);
      });
  }, []);

  const stats = statsData
    ? [
        {
          icon: 'ri-money-dollar-circle-fill',
          value: `${statsData.total_amount.toLocaleString()}원`,
          label: '총 기부금액',
          color: 'text-green-600',
          bgColor: 'bg-green-100',
        },
        {
          icon: 'ri-cup-fill',
          value: `${statsData.total_cups.toLocaleString()}잔`,
          label: '총 기부된 커피',
          color: 'text-orange-600',
          bgColor: 'bg-orange-100',
        },
        {
          icon: 'ri-building-fill',
          value: `${statsData.total_fire_stations}개`,
          label: '지원한 소방서',
          color: 'text-red-600',
          bgColor: 'bg-red-100',
        },
        {
          icon: 'ri-user-fill',
          value: `${statsData.total_users.toLocaleString()}명`,
          label: '참여한 시민',
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
        },
      ]
    : [];

  const handleViewAll = () => {
    router.push('/donation-ranking');
  };

  if (loading) {
    return (
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">데이터 로딩 중...</div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-16 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-12">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">함께 만들어가는 감사의 마음</h2>
            <p className="text-lg text-gray-600">
              많은 분들의 따뜻한 마음이 소방관들에게 전달되고 있습니다
            </p>
          </div>
          <Button variant="outline" onClick={handleViewAll} className="flex items-center space-x-2">
            <span>전체 보기</span>
            <i className="ri-arrow-right-line"></i>
          </Button>
        </div>

        {/* 기부 통계 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <Card key={index} className="text-center hover:shadow-xl transition-shadow duration-300">
              <div
                className={`w-16 h-16 ${stat.bgColor} rounded-full flex items-center justify-center mx-auto mb-4`}
              >
                <i className={`${stat.icon} ${stat.color} text-2xl`}></i>
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-3">{stat.value}</div>
              <div className="text-gray-600 font-medium">{stat.label}</div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
