'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';

export default function PaymentSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hasConfirmed = useRef(false);  // 중복 실행 방지용 ref

  const [paymentInfo, setPaymentInfo] = useState({
    orderId: '',
    amount: 0,
    station: '',
    cups: 0,
    paymentKey: '',
    isConfirmed: false
  });
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const orderId = searchParams.get('orderId') || '';
    const amountValueRaw = searchParams.get('amount') || '0';
    const amount = parseInt(amountValueRaw, 10);
    const stationValue = searchParams.get('station') || '';
    const station = stationValue ? decodeURIComponent(stationValue) : '';
    const paymentKey = searchParams.get('paymentKey') || '';

    setPaymentInfo({
      orderId,
      amount,
      station,
      cups: Number.isFinite(amount) && amount > 0 ? Math.floor(amount / 3000) : 0,
      paymentKey,
      isConfirmed: false,
    });

    // useRef로 중복 실행 방지 (React Strict Mode 대응)
    if (!hasConfirmed.current && paymentKey && orderId && amount > 0) {
      hasConfirmed.current = true;
      confirmPayment(paymentKey, orderId, amount);
    }
  }, [searchParams]);

  useEffect(() => {
    setCurrentTime(new Date().toLocaleString('ko-KR'));
  }, []);

  const confirmPayment = async (paymentKey: string, orderId: string, amount: number) => {
    try {
      console.log('결제 승인 요청:', { paymentKey, orderId, amount });

      // 백엔드 API 호출하여 결제 승인
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://api.bodam.website';
      const response = await fetch(`${apiBaseUrl}/payments/confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          payment_key: paymentKey,
          order_id: orderId,
          amount: amount,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ 결제 승인 API 에러:', errorData);

        // S008 에러 (이미 처리중/완료된 결제)는 성공으로 간주
        if (errorData.detail && typeof errorData.detail === 'string' && errorData.detail.includes('S008')) {
          console.warn('⚠️ 이미 처리된 결제입니다. 성공으로 간주합니다.');
          setPaymentInfo(prev => ({ ...prev, isConfirmed: true }));
          setTimeout(() => {
            router.push('/donations/history');
          }, 3000);
          return;
        }

        const errorMsg = typeof errorData.detail === 'string'
          ? errorData.detail
          : JSON.stringify(errorData.detail || errorData);
        throw new Error(errorMsg);
      }

      const result = await response.json();
      console.log('✅ 결제 승인 완료:', result);
      setPaymentInfo(prev => ({ ...prev, isConfirmed: true }));

      // 3초 후 기부 내역 페이지로 이동
      setTimeout(() => {
        router.push('/donations/history');
      }, 3000);

    } catch (error) {
      console.error('❌ 결제 승인 오류:', error);
      alert(`결제 승인 중 오류가 발생했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      router.push('/');
    }
  };

  const handleGoHome = () => {
    router.push('/');
  };

  const handleViewRanking = () => {
    router.push('/donation-ranking');
  };

  return (
    <div className="bg-gray-50">
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <i className="ri-check-line text-green-600 text-4xl"></i>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            기부가 완료되었습니다!
          </h1>
          <p className="text-lg text-gray-600">
            소방관들에게 따뜻한 마음이 전달됩니다. 감사합니다!
          </p>
        </div>

        <Card className="p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            기부 내역
          </h2>
          
          <div className="bg-gray-50 p-6 rounded-lg mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">주문번호</span>
                  <span className="font-mono text-sm text-gray-900">{paymentInfo.orderId}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">기부 금액</span>
                  <span className="font-bold text-red-600 text-xl">
                    {paymentInfo.amount.toLocaleString()}원
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">커피</span>
                  <span className="font-medium text-gray-900 flex items-center">
                    <i className="ri-cup-fill text-orange-500 mr-1"></i>
                    {paymentInfo.cups}잔
                  </span>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">소방서</span>
                  <span className="font-medium text-gray-900">{paymentInfo.station}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">결제 상태</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    paymentInfo.isConfirmed 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {paymentInfo.isConfirmed ? '결제 완료' : '승인 중'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">결제일시</span>
                  <span className="text-gray-900 text-sm">
                    {currentTime || '결제일시 로딩 중'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 감사 메시지 */}
          <div className="bg-gradient-to-r from-red-50 to-orange-50 p-6 rounded-lg border border-red-100 mb-6">
            <div className="text-center">
              <i className="ri-heart-fill text-red-500 text-3xl mb-3"></i>
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                따뜻한 마음에 감사드립니다
              </h3>
              <p className="text-gray-700">
                여러분의 기부는 {paymentInfo.station}에서 근무하는 소방관들에게<br />
                따뜻한 커피와 간식으로 전달됩니다.
              </p>
            </div>
          </div>

          {/* 기부 영수증 안내 */}
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 mb-6">
            <div className="flex items-start space-x-3">
              <i className="ri-file-text-line text-blue-600 text-xl mt-0.5"></i>
              <div>
                <h4 className="font-medium text-blue-900 mb-1">기부금 영수증 발급</h4>
                <p className="text-sm text-blue-700">
                  기부금 영수증은 이메일로 발송되며, 연말정산 시 소득공제를 받으실 수 있습니다.
                </p>
              </div>
            </div>
          </div>

          {/* 액션 버튼들 */}
          <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
            <Button 
              variant="outline" 
              size="lg" 
              className="flex-1"
              onClick={handleViewRanking}
            >
              <i className="ri-trophy-line mr-2"></i>
              기부 랭킹 보기
            </Button>
            <Button 
              size="lg" 
              className="flex-1"
              onClick={handleGoHome}
            >
              <i className="ri-home-line mr-2"></i>
              홈으로 돌아가기
            </Button>
          </div>
        </Card>

        {/* 추가 기부 유도 */}
        <Card className="p-6 bg-gradient-to-r from-orange-50 to-red-50">
          <div className="text-center">
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              더 많은 소방관들을 도와주세요
            </h3>
            <p className="text-gray-700 mb-4">
              전국의 소방관들이 여러분의 따뜻한 마음을 기다리고 있습니다
            </p>
            <Button 
              variant="donate"
              onClick={() => router.push('/donations')}
            >
              <i className="ri-heart-fill mr-2"></i>
              추가 기부하기
            </Button>
          </div>
        </Card>
      </section>

    </div>
  );
}
