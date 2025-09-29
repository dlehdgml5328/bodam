"use client";

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';

const FireStationDetailPage = () => {
  const router = useRouter();
  const params = useParams<{ id?: string }>();
  const stationId = params?.id ?? null;
  const stationName = stationId ? decodeURIComponent(stationId) : '서울강남소방서';

  // 강남소방서 데이터 (100잔 단위 전달 시스템)
  const stationData = {
    name: stationName,
    address: '서울특별시 강남구 테헤란로 326',
    phone: '02-1234-5678',
    totalDonationAmount: 750000, // 총 기부금액
    totalCoffeeCups: 250, // 총 누적 커피잔수
    deliveredBatches: 2, // 전달 완료된 배치 (200잔)
    deliveredCups: 200, // 전달 완료된 커피잔수
    pendingCups: 50, // 다음 전달 대기 중인 잔수
    cupsPerBatch: 100, // 배치당 커피잔수
    deliveryHistory: [
      {
        batchNumber: 2,
        deliveredDate: '2024-01-15',
        amount: 300000,
        cups: 100,
        status: '전달완료'
      },
      {
        batchNumber: 1,
        deliveredDate: '2024-01-01',
        amount: 300000,
        cups: 100,
        status: '전달완료'
      }
    ]
  };

  // 다음 전달까지 필요한 잔수
  const cupsNeededForNextDelivery = stationData.cupsPerBatch - stationData.pendingCups;
  
  // 전달률 계산
  const deliveryRate = Math.floor((stationData.deliveredCups / stationData.totalCoffeeCups) * 100);

  // 기존 코드 삽입 시작
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // 강남소방서 상세 데이터 (URL 파라미터에 따라 다른 데이터를 보여줄 수 있음)
  const stationInfo = {
    name: stationName,
    region: '서울특별시',
    address: '서울특별시 강남구 테헤란로 123',
    phone: '02-1234-5678',
    totalDonations: 450000,
    totalCups: 150,
    deliveredCups: 120,
    pendingCups: 30,
    deliveryRate: 80,
    lastDelivery: new Date(2024, 11, 15),
    nextDelivery: new Date(2024, 11, 20)
  };

  // 강남소방서의 기부 내역 데이터
  const donationHistory = [
    {
      id: 1,
      date: new Date(2024, 11, 15),
      donorName: '김**',
      donorType: '개인',
      amount: 45000,
      cups: 15,
      status: 'delivered',
      deliveryDate: new Date(2024, 11, 16),
      note: '감사 인사 전달 완료'
    },
    {
      id: 2,
      date: new Date(2024, 11, 12),
      donorName: '이**',
      donorType: '개인',
      amount: 30000,
      cups: 10,
      status: 'delivered',
      deliveryDate: new Date(2024, 11, 13),
      note: '맛있게 드셨다고 함'
    },
    {
      id: 3,
      date: new Date(2024, 11, 10),
      donorName: '박**',
      donorType: '개인',
      amount: 60000,
      cups: 20,
      status: 'pending',
      deliveryDate: null,
      note: '커피 재고 확인중'
    },
    {
      id: 4,
      date: new Date(2024, 11, 8),
      donorName: '정**',
      donorType: '개인',
      amount: 36000,
      cups: 12,
      status: 'delivered',
      deliveryDate: new Date(2024, 11, 9),
      note: '소방관들이 매우 기뻐함'
    },
    {
      id: 5,
      date: new Date(2024, 11, 5),
      donorName: '한국기업협회',
      donorType: '단체',
      amount: 150000,
      cups: 50,
      status: 'delivered',
      deliveryDate: new Date(2024, 11, 6),
      note: '대량 기부로 한 달치 커피 해결'
    },
    {
      id: 6,
      date: new Date(2024, 11, 3),
      donorName: '강남구청',
      donorType: '기관',
      amount: 90000,
      cups: 30,
      status: 'delivered',
      deliveryDate: new Date(2024, 11, 4),
      note: '구청장님 격려 방문'
    },
    {
      id: 7,
      date: new Date(2024, 11, 1),
      donorName: '최**',
      donorType: '개인',
      amount: 18000,
      cups: 6,
      status: 'pending',
      deliveryDate: null,
      note: '소방서 연락 대기중'
    },
    {
      id: 8,
      date: new Date(2024, 10, 28),
      donorName: '강남상공회의소',
      donorType: '단체',
      amount: 120000,
      cups: 40,
      status: 'delivered',
      deliveryDate: new Date(2024, 10, 29),
      note: '상공회의소 회원사들의 마음'
    },
    {
      id: 9,
      date: new Date(2024, 10, 25),
      donorName: '장**',
      donorType: '개인',
      amount: 24000,
      cups: 8,
      status: 'delivered',
      deliveryDate: new Date(2024, 10, 26),
      note: '직접 방문해서 전달'
    },
    {
      id: 10,
      date: new Date(2024, 10, 22),
      donorName: '윤**',
      donorType: '개인',
      amount: 15000,
      cups: 5,
      status: 'delivered',
      deliveryDate: new Date(2024, 10, 23),
      note: '따뜻한 편지와 함께'
    },
    {
      id: 11,
      date: new Date(2024, 10, 20),
      donorName: 'SK텔레콤',
      donorType: '기업',
      amount: 300000,
      cups: 100,
      status: 'delivered',
      deliveryDate: new Date(2024, 10, 21),
      note: '기업 사회공헌 활동의 일환'
    },
    {
      id: 12,
      date: new Date(2024, 10, 18),
      donorName: '송**',
      donorType: '개인',
      amount: 27000,
      cups: 9,
      status: 'pending',
      deliveryDate: null,
      note: '배송 지연 (교통상황)'
    }
  ];

  // 월별 기부 현황 (차트용 데이터)
  const monthlyData = [
    { month: '7월', donations: 240000, cups: 80, donors: 15 },
    { month: '8월', donations: 315000, cups: 105, donors: 18 },
    { month: '9월', donations: 390000, cups: 130, donors: 22 },
    { month: '10월', donations: 420000, cups: 140, donors: 25 },
    { month: '11월', donations: 480000, cups: 160, donors: 28 },
    { month: '12월', donations: 450000, cups: 150, donors: 24 }
  ];

  // 기부자 유형별 통계
  const donorTypeStats = [
    { type: '개인', count: 18, amount: 285000, cups: 95, percentage: 63 },
    { type: '단체', count: 4, amount: 360000, cups: 120, percentage: 80 },
    { type: '기업/기관', count: 2, amount: 390000, cups: 130, percentage: 87 }
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'delivered':
        return <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full font-medium">지급완료</span>;
      case 'pending':
        return <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full font-medium">지급대기</span>;
      case 'hold':
        return <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full font-medium">지급보류</span>;
      default:
        return <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full font-medium">알 수 없음</span>;
    }
  };

  const getDonorTypeBadge = (type: string) => {
    switch (type) {
      case '개인':
        return <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full font-medium">개인</span>;
      case '단체':
        return <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full font-medium">단체</span>;
      case '기업':
      case '기관':
        return <span className="px-2 py-1 text-xs bg-indigo-100 text-indigo-800 rounded-full font-medium">{type}</span>;
      default:
        return <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full font-medium">{type}</span>;
    }
  };

  // 페이지네이션
  const totalPages = Math.ceil(donationHistory.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = donationHistory.slice(startIndex, endIndex);

  const handleDonateClick = () => {
    router.push('/donations');
  };

  const handleBackClick = () => {
    router.push('/donation-ranking');
  };
  // 기존 코드 삽입 종료

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ... 기존 코드 ... */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 브레드크럼 */}
        <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-6">
          <button
            onClick={() => router.push('/donation-ranking')}
            className="hover:text-orange-600 transition-colors"
          >
            기부 현황 및 랭킹
          </button>
          <span>/</span>
          <span className="text-gray-900 font-medium">{stationData.name}</span>
        </nav>

        {/* 소방서 정보 헤더 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center">
                <i className="ri-fire-line text-3xl text-orange-600"></i>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">{stationData.name}</h1>
                <div className="space-y-1 text-gray-600">
                  <p className="flex items-center">
                    <i className="ri-map-pin-line mr-2"></i>
                    {stationData.address}
                  </p>
                  <p className="flex items-center">
                    <i className="ri-phone-line mr-2"></i>
                    {stationData.phone}
                  </p>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500 mb-1">배치당 전달 기준</div>
              <div className="text-2xl font-bold text-orange-600">{stationData.cupsPerBatch}잔</div>
            </div>
          </div>
        </div>

        {/* 커피 기부 현황 대시보드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600 mb-1">총 누적 기부</p>
                <p className="text-2xl font-bold text-blue-900">{stationData.totalCoffeeCups}잔</p>
                <p className="text-xs text-blue-700 mt-1">
                  {stationData.totalDonationAmount.toLocaleString()}원
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-200 rounded-full flex items-center justify-center">
                <i className="ri-cup-line text-xl text-blue-600"></i>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600 mb-1">전달 완료</p>
                <p className="text-2xl font-bold text-green-900">{stationData.deliveredCups}잔</p>
                <p className="text-xs text-green-700 mt-1">
                  {stationData.deliveredBatches}회 전달
                </p>
              </div>
              <div className="w-12 h-12 bg-green-200 rounded-full flex items-center justify-center">
                <i className="ri-check-line text-xl text-green-600"></i>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600 mb-1">대기 중</p>
                <p className="text-2xl font-bold text-orange-900">{stationData.pendingCups}잔</p>
                <p className="text-xs text-orange-700 mt-1">
                  다음 전달까지 {cupsNeededForNextDelivery}잔 필요
                </p>
              </div>
              <div className="w-12 h-12 bg-orange-200 rounded-full flex items-center justify-center">
                <i className="ri-hourglass-line text-xl text-orange-600"></i>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600 mb-1">전달률</p>
                <p className="text-2xl font-bold text-purple-900">{deliveryRate}%</p>
                <p className="text-xs text-purple-700 mt-1">
                  총 {stationData.totalCoffeeCups}잔 중 {stationData.deliveredCups}잔 전달
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-200 rounded-full flex items-center justify-center">
                <i className="ri-pie-chart-line text-xl text-purple-600"></i>
              </div>
            </div>
          </Card>
        </div>

        {/* 전달 진행 상황 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">전달 진행 상황</h3>
          
          {/* 현재 배치 진행률 */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-700">
                다음 전달까지 ({stationData.pendingCups}/{stationData.cupsPerBatch}잔)
              </span>
              <span className="text-sm text-gray-500">
                {Math.floor((stationData.pendingCups / stationData.cupsPerBatch) * 100)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-orange-400 to-orange-600 h-3 rounded-full transition-all duration-300"
                style={{ width: `${(stationData.pendingCups / stationData.cupsPerBatch) * 100}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              <strong>{cupsNeededForNextDelivery}잔</strong>이 더 모이면 다음 배치가 전달됩니다.
            </p>
          </div>

          {/* 배치별 전달 현황 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 다음 전달 예정 */}
            <div className="border-2 border-dashed border-orange-300 rounded-lg p-4">
              <div className="text-center">
                <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <i className="ri-time-line text-xl text-orange-600"></i>
                </div>
                <h4 className="font-semibold text-gray-900 mb-1">3배치 (대기중)</h4>
                <p className="text-2xl font-bold text-orange-600 mb-1">{stationData.pendingCups}/100잔</p>
                <p className="text-xs text-gray-500">
                  {cupsNeededForNextDelivery}잔 더 필요
                </p>
              </div>
            </div>

            {/* 전달 완료된 배치들 */}
            {stationData.deliveryHistory.map((batch) => (
              <div key={batch.batchNumber} className="border border-green-200 bg-green-50 rounded-lg p-4">
                <div className="text-center">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <i className="ri-check-double-line text-xl text-green-600"></i>
                  </div>
                  <h4 className="font-semibold text-gray-900 mb-1">{batch.batchNumber}배치</h4>
                  <p className="text-2xl font-bold text-green-600 mb-1">{batch.cups}잔</p>
                  <p className="text-xs text-gray-500">
                    {batch.deliveredDate} 전달완료
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 응원 메시지 */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-xl p-8 text-center text-white mb-8">
          <h3 className="text-2xl font-bold mb-4">🔥 소방관들을 위한 따뜻한 마음 🔥</h3>
          <p className="text-lg mb-2">
            현재 <strong>{stationData.pendingCups}잔</strong>의 커피가 다음 전달을 기다리고 있습니다.
          </p>
          <p className="text-orange-100">
            <strong>{cupsNeededForNextDelivery}잔</strong>이 더 모으면 소방관분들께 따뜻한 커피를 전달할 수 있어요!
          </p>
        </div>

        {/* 전달 내역 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-xl font-semibold text-gray-900">전달 내역</h3>
            <p className="text-sm text-gray-600 mt-1">100잔 단위로 기부금이 전달됩니다</p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    배치
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    전달일
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    커피잔수
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    전달금액
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    상태
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr className="bg-orange-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center mr-3">
                        <i className="ri-hourglass-line text-orange-600"></i>
                      </div>
                      <span className="font-medium text-gray-900">3배치</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    대기중
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-orange-600 font-semibold">{stationData.pendingCups}/100잔</span>
                    <div className="w-20 bg-gray-200 rounded-full h-2 mt-1">
                      <div 
                        className="bg-orange-400 h-2 rounded-full"
                        style={{ width: `${(stationData.pendingCups / 100) * 100}%` }}
                      ></div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    150,000원 예정
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-orange-100 text-orange-800">
                      대기중 ({cupsNeededForNextDelivery}잔 더 필요)
                    </span>
                  </td>
                </tr>
                {stationData.deliveryHistory.map((batch) => (
                  <tr key={batch.batchNumber}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                          <i className="ri-check-line text-green-600"></i>
                        </div>
                        <span className="font-medium text-gray-900">{batch.batchNumber}배치</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      {batch.deliveredDate}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-green-600 font-semibold">{batch.cups}잔</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      {batch.amount.toLocaleString()}원
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        전달완료
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 돌아가기 버튼 */}
        <div className="mt-8 text-center">
          <Button
            onClick={() => router.push('/donation-ranking')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-8 py-3 rounded-lg transition-colors"
          >
            <i className="ri-arrow-left-line mr-2"></i>
            목록으로 돌아가기
          </Button>
        </div>
      </div>
    </div>
  );
};

export default FireStationDetailPage;
