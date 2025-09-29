'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Card from '../base/Card';
import Button from '../base/Button';

export default function DonationRanking() {
  const [activeTab, setActiveTab] = useState<'individual' | 'group' | 'organization'>('individual');
  const router = useRouter();

  const individualRankings = [
    { rank: 1, name: '김민수', amount: 150000, cups: 300, badge: '🥇' },
    { rank: 2, name: '이영희', amount: 100000, cups: 200, badge: '🥈' },
    { rank: 3, name: '박정민', amount: 85000, cups: 170, badge: '🥉' },
    { rank: 4, name: '정수진', amount: 65000, cups: 130, badge: '' },
    { rank: 5, name: '강대호', amount: 45000, cups: 90, badge: '' },
    { rank: 6, name: '윤미래', amount: 40000, cups: 80, badge: '' },
    { rank: 7, name: '송지훈', amount: 35000, cups: 70, badge: '' },
    { rank: 8, name: '한소영', amount: 30000, cups: 60, badge: '' },
    { rank: 9, name: '최준호', amount: 25000, cups: 50, badge: '' },
    { rank: 10, name: '장민정', amount: 20000, cups: 40, badge: '' }
  ];

  const groupRankings = [
    { rank: 1, name: '서울시민연합', amount: 400000, cups: 800, badge: '🥇', type: '시민단체' },
    { rank: 2, name: '부산소방후원회', amount: 320000, cups: 640, badge: '🥈', type: '후원단체' },
    { rank: 3, name: '시민안전협회', amount: 280000, cups: 560, badge: '🥉', type: '시민단체' },
    { rank: 4, name: '인천봉사회', amount: 200000, cups: 400, badge: '', type: '봉사단체' },
    { rank: 5, name: '대구안전모임', amount: 180000, cups: 360, badge: '', type: '시민단체' },
    { rank: 6, name: '울산시민봉사단', amount: 150000, cups: 300, badge: '', type: '봉사단체' },
    { rank: 7, name: '광주희망연대', amount: 120000, cups: 240, badge: '', type: '시민단체' },
    { rank: 8, name: '전주나눔회', amount: 100000, cups: 200, badge: '', type: '봉사단체' },
    { rank: 9, name: '제주평화단체', amount: 80000, cups: 160, badge: '', type: '시민단체' },
    { rank: 10, name: '강원도민회', amount: 70000, cups: 140, badge: '', type: '지역단체' }
  ];

  const organizationRankings = [
    { rank: 1, name: '㈜따뜻한마음', amount: 600000, cups: 1200, badge: '🥇', type: '기업' },
    { rank: 2, name: '대한적십자사', amount: 450000, cups: 900, badge: '🥈', type: '공공기관' },
    { rank: 3, name: '㈜커피사랑', amount: 380000, cups: 760, badge: '🥉', type: '기업' },
    { rank: 4, name: '한국전력공사', amount: 300000, cups: 600, badge: '', type: '공공기관' },
    { rank: 5, name: '㈜안전나라', amount: 250000, cups: 500, badge: '', type: '기업' },
    { rank: 6, name: '소방청', amount: 200000, cups: 400, badge: '', type: '정부기관' },
    { rank: 7, name: '㈜희망건설', amount: 180000, cups: 360, badge: '', type: '기업' },
    { rank: 8, name: '한국가스공사', amount: 150000, cups: 300, badge: '', type: '공공기관' },
    { rank: 9, name: '㈜커피플러스', amount: 120000, cups: 240, badge: '', type: '기업' },
    { rank: 10, name: '국립재난안전연구원', amount: 100000, cups: 200, badge: '', type: '연구기관' }
  ];

  const getCurrentRankings = () => {
    switch (activeTab) {
      case 'individual':
        return individualRankings;
      case 'group':
        return groupRankings;
      case 'organization':
        return organizationRankings;
      default:
        return individualRankings;
    }
  };

  const getTabTitle = () => {
    switch (activeTab) {
      case 'individual':
        return '기부자';
      case 'group':
        return '단체명';
      case 'organization':
        return '기관·기업명';
      default:
        return '기부자';
    }
  };

  const handleViewAll = () => {
    router.push('/donation-ranking');
  };

  const currentRankings = getCurrentRankings();

  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-12">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              이달의 기부 랭킹 TOP 10
            </h2>
            <p className="text-lg text-gray-600">
              소방관들을 위한 따뜻한 마음을 나눠주신 분들을 소개합니다
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

        {/* 탭 전환 버튼 */}
        <div className="flex justify-center mb-8">
          <div className="bg-gray-100 p-1 rounded-full">
            <button
              onClick={() => setActiveTab('individual')}
              className={`px-6 py-2 rounded-full font-medium transition-all duration-200 ${
                activeTab === 'individual'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              개인 기부자
            </button>
            <button
              onClick={() => setActiveTab('group')}
              className={`px-6 py-2 rounded-full font-medium transition-all duration-200 ${
                activeTab === 'group'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              단체
            </button>
            <button
              onClick={() => setActiveTab('organization')}
              className={`px-6 py-2 rounded-full font-medium transition-all duration-200 ${
                activeTab === 'organization'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              기관·기업
            </button>
          </div>
        </div>

        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-4 px-4 font-semibold text-gray-900">순위</th>
                  <th className="text-left py-4 px-4 font-semibold text-gray-900">
                    {getTabTitle()}
                  </th>
                  {(activeTab === 'group' || activeTab === 'organization') && (
                    <th className="text-left py-4 px-4 font-semibold text-gray-900">구분</th>
                  )}
                  <th className="text-right py-4 px-4 font-semibold text-gray-900">기부금액</th>
                  <th className="text-right py-4 px-4 font-semibold text-gray-900">커피잔수</th>
                </tr>
              </thead>
              <tbody>
                {currentRankings.map((item) => (
                  <tr key={item.rank} className="border-b border-gray-100 hover:bg-gray-50 transition-colors duration-200">
                    <td className="py-4 px-4">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg font-bold text-gray-900">{item.rank}</span>
                        {item.badge && <span className="text-xl">{item.badge}</span>}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="font-medium text-gray-900">{item.name}</div>
                    </td>
                    {(activeTab === 'group' || activeTab === 'organization') && (
                      <td className="py-4 px-4">
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                          activeTab === 'group' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {(item as any).type}
                        </span>
                      </td>
                    )}
                    <td className="py-4 px-4 text-right">
                      <div className="font-semibold text-red-600">
                        {item.amount.toLocaleString()}원
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right">
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
      </div>
    </section>
  );
}
