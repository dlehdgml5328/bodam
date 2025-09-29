'use client';

import Card from '../base/Card';
import Button from '../base/Button';
import { useRouter } from 'next/navigation';

export default function DashboardStats() {
  const router = useRouter();

  const stats = [
    {
      icon: 'ri-money-dollar-circle-fill',
      value: '2,450,000,000원',
      label: '총 기부금액',
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      icon: 'ri-cup-fill',
      value: '127,543잔',
      label: '총 기부된 커피',
      color: 'text-orange-600',
      bgColor: 'bg-orange-100'
    },
    {
      icon: 'ri-building-fill',
      value: '342개',
      label: '지원한 소방서',
      color: 'text-red-600',
      bgColor: 'bg-red-100'
    },
    {
      icon: 'ri-user-fill',
      value: '28,956명',
      label: '참여한 시민',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      icon: 'ri-group-fill',
      value: '1,847개',
      label: '참여한 단체',
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    },
    {
      icon: 'ri-building-2-fill',
      value: '423개',
      label: '참여한 기관 및 기업',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100'
    }
  ];

  const handleViewAll = () => {
    router.push('/donation-ranking');
  };

  return (
    <section className="py-16 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-12">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              함께 만들어가는 감사의 마음
            </h2>
            <p className="text-lg text-gray-600">
              많은 분들의 따뜻한 마음이 소방관들에게 전달되고 있습니다
            </p>
          </div>
          <Button 
            variant="outline" 
            onClick={handleViewAll}
            className="flex items-center space-x-2"
          >
            <span>전체 보기</span>
            <i className="ri-arrow-right-line"></i>
          </Button>
        </div>

        {/* 첫 번째 줄: 총 기부금액, 총 기부된 커피, 지원한 소방서 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {stats.slice(0, 3).map((stat, index) => (
            <Card key={index} className="text-center hover:shadow-xl transition-shadow duration-300">
              <div className={`w-16 h-16 ${stat.bgColor} rounded-full flex items-center justify-center mx-auto mb-4`}>
                <i className={`${stat.icon} ${stat.color} text-2xl`}></i>
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-3">
                {stat.value}
              </div>
              <div className="text-gray-600 font-medium">
                {stat.label}
              </div>
            </Card>
          ))}
        </div>

        {/* 두 번째 줄: 참여한 시민, 참여한 단체, 참여한 기관 및 기업 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {stats.slice(3, 6).map((stat, index) => (
            <Card key={index + 3} className="text-center hover:shadow-xl transition-shadow duration-300">
              <div className={`w-16 h-16 ${stat.bgColor} rounded-full flex items-center justify-center mx-auto mb-4`}>
                <i className={`${stat.icon} ${stat.color} text-2xl`}></i>
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-3">
                {stat.value}
              </div>
              <div className="text-gray-600 font-medium">
                {stat.label}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
