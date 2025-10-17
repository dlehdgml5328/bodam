'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiRequest, ApiError } from '@/lib/api';

export default function NaverCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState('');

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');

      if (!code || !state) {
        setError('인증 정보가 올바르지 않습니다.');
        return;
      }

      // Verify state
      const savedState = sessionStorage.getItem('oauth_state_naver');
      if (savedState !== state) {
        setError('인증 상태가 일치하지 않습니다. 다시 시도해주세요.');
        return;
      }

      try {
        // Call backend callback endpoint
        const data = await apiRequest<{
          user: { id: string; email: string; name: string };
          access_token: string;
          csrf_token: string;
        }>('/auth/social/naver/callback', {
          method: 'POST',
          body: JSON.stringify({ code, state }),
        });

        // Save tokens
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('bodam_access_token', data.access_token);
          sessionStorage.setItem('bodam_csrf_token', data.csrf_token);
          sessionStorage.removeItem('oauth_state_naver');
        }

        // Save login state
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('loggedInEmail', data.user.email);
        localStorage.setItem('loggedInName', data.user.name);
        localStorage.setItem('loggedInProvider', 'naver');

        window.dispatchEvent(new Event('bodam-auth-change'));

        // Redirect to home
        router.push('/');
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('네이버 로그인 중 문제가 발생했습니다.');
        }
      }
    };

    void handleCallback();
  }, [router, searchParams]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow">
          <h2 className="text-2xl font-bold text-red-600 mb-4">로그인 실패</h2>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={() => router.push('/login')}
            className="w-full bg-red-600 text-white py-2 rounded hover:bg-red-700"
          >
            로그인 페이지로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
        <p className="text-gray-600">네이버 로그인 처리 중...</p>
      </div>
    </div>
  );
}
