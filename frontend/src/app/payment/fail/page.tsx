'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function PaymentFailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [errorCode, setErrorCode] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const code = searchParams.get('code') || 'UNKNOWN_ERROR';
    const message = searchParams.get('message') || '결제 중 오류가 발생했습니다.';

    setErrorCode(code);
    setErrorMessage(message);
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center max-w-md mx-auto p-6">
        <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
          <i className="ri-close-line text-3xl text-red-600"></i>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">결제 실패</h2>
        <p className="text-gray-600 mb-2">{errorMessage}</p>
        {errorCode && (
          <p className="text-sm text-gray-500 mb-6">오류 코드: {errorCode}</p>
        )}
        <div className="space-y-3">
          <button
            onClick={() => router.push('/donations')}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            다시 시도하기
          </button>
          <button
            onClick={() => router.push('/')}
            className="w-full px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    </div>
  );
}
