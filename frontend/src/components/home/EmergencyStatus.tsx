'use client';

import { useRouter } from 'next/navigation';
import Button from '../base/Button';
import Card from '../base/Card';

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

type EmergencyStatusProps = {
  stations?: EmergencyStation[];
};

export default function EmergencyStatus({ stations = [] }: EmergencyStatusProps) {
  const router = useRouter();
  const emergencyStations = stations.length ? stations : FALLBACK_STATIONS;

  const getStatusColor = (status: string, priority?: string) => {
    if (status === '출동 중' && priority === 'high') return 'text-red-600 bg-red-100';
    if (status === '진압 중') return 'text-orange-600 bg-orange-100';
    if (status === '출동 중') return 'text-yellow-600 bg-yellow-100';
    if (status === '점검 중') return 'text-blue-600 bg-blue-100';
    return 'text-green-600 bg-green-100';
  };

  const handleDonateClick = (stationName: string) => {
    router.push(`/donations?station=${encodeURIComponent(stationName)}`);
  };

  const handleViewAll = () => {
    router.push('/regions');
  };

  return (
    <section className="py-16 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-12">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">실시간 출동 현황</h2>
            <p className="text-lg text-gray-600">현재 전국 소방서의 실시간 출동 및 대응 상황을 확인하세요</p>
          </div>
          <Button variant="outline" onClick={handleViewAll} className="flex items-center space-x-2">
            <span>전체 보기</span>
            <i className="ri-arrow-right-line"></i>
          </Button>
        </div>

        <div className="mb-12">
          <div className="flex items-center space-x-2 mb-6">
            <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
            <h3 className="text-xl font-bold text-red-600">긴급 지원이 필요한 소방서</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {emergencyStations.map((station, index) => (
              <Card key={`${station.name}-${index}`} className="border-l-4 border-red-500 hover:shadow-xl transition-shadow duration-300">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-bold text-gray-900">{station.name}</h4>
                    <p className="text-gray-600">{station.location}</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                      station.status,
                      station.priority,
                    )}`}
                  >
                    {station.status}
                  </span>
                </div>

                <div className="space-y-2 mb-6">
                  <div className="flex items-center space-x-2">
                    <i className="ri-fire-fill text-red-500"></i>
                    <span className="text-gray-700">긴급 상황 대응 중</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <i className="ri-time-line text-gray-400"></i>
                    <span className="text-gray-600 text-sm">{station.time}</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <Button
                    variant="donate"
                    size="sm"
                    className="w-full text-sm"
                    onClick={() => handleDonateClick(station.name)}
                  >
                    <i className="ri-heart-fill mr-2"></i>
                    {station.name}에 기부하기
                  </Button>
                  <p className="text-xs text-gray-500 text-center mt-2">현장에서 힘쓰는 소방관들을 응원해주세요</p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
