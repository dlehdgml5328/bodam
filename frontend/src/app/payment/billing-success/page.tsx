'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiRequest } from '@/lib/api';

export default function BillingSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const processBillingAuth = async () => {
      const authKey = searchParams.get('authKey');
      const customerKey = searchParams.get('customerKey');
      const orderId = searchParams.get('orderId');

      if (!authKey || !customerKey) {
        setStatus('error');
        setErrorMessage('빌링키 정보가 올바르지 않습니다.');
        return;
      }

      try {
        // 백엔드 빌링키 콜백 API 호출
        await apiRequest('/payments/billing/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            customer_key: customerKey,
            auth_key: authKey,
          }),
        });

        console.log('빌링키 등록 완료');
        setStatus('success');

        // 3초 후 기부 내역 페이지로 이동
        setTimeout(() => {
          router.push('/donations/history');
        }, 3000);
      } catch (error: any) {
        console.error('빌링키 등록 실패:', error);
        setStatus('error');
        setErrorMessage(
          error.message || '빌링키 등록 중 오류가 발생했습니다.'
        );
      }
    };

    void processBillingAuth();
  }, [searchParams, router]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            정기결제를 설정하고 있습니다...
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
            정기결제 설정 실패
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
          정기결제가 설정되었습니다!
        </h2>
        <p className="text-gray-600 mb-6">
          설정하신 주기에 따라 자동으로 기부가 진행됩니다.
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
