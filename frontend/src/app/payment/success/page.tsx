'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiRequest } from '@/lib/api';

export default function PaymentSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const confirmPayment = async () => {
      const paymentKey = searchParams.get('paymentKey');
      const orderId = searchParams.get('orderId');
      const amount = searchParams.get('amount');

      if (!paymentKey || !orderId || !amount) {
        setStatus('error');
        setErrorMessage('결제 정보가 올바르지 않습니다.');
        return;
      }

      try {
        // 백엔드 결제 승인 API 호출
        const response = await apiRequest('/payments/confirm', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            payment_key: paymentKey,
            order_id: orderId,
            amount: parseFloat(amount),
          }),
        });

        console.log('결제 승인 완료:', response);
        setStatus('success');

        // 3초 후 기부 내역 페이지로 이동
        setTimeout(() => {
          router.push('/donations/history');
        }, 3000);
      } catch (error: any) {
        console.error('결제 승인 실패:', error);
        setStatus('error');
        setErrorMessage(
          error.message || '결제 승인 중 오류가 발생했습니다.'
        );
      }
    };

    void confirmPayment();
  }, [searchParams, router]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            결제를 승인하고 있습니다...
          </h2>
          <p className="text-gray-600">잠시만 기다려주세요.</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
            <i className="ri-close-line text-3xl text-red-600"></i>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            결제 승인 실패
          </h2>
          <p className="text-gray-600 mb-6">{errorMessage}</p>
          <button
            onClick={() => router.push('/donations')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            기부 페이지로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center max-w-md mx-auto p-6">
        <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
          <i className="ri-check-line text-3xl text-green-600"></i>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          기부가 완료되었습니다!
        </h2>
        <p className="text-gray-600 mb-6">
          따뜻한 마음을 전해주셔서 감사합니다.
          <br />
          기부 내역 페이지로 이동합니다...
        </p>
        <div className="text-sm text-gray-500">
          자동으로 이동하지 않으면{' '}
          <button
            onClick={() => router.push('/donations/history')}
            className="text-blue-600 hover:underline"
          >
            여기를 클릭
          </button>
          하세요.
        </div>
      </div>
    </div>
  );
}
