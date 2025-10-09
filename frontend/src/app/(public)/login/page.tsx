'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { apiRequest, ApiError } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [redirectTo, setRedirectTo] = useState('/donations');
  const [keepSignedIn, setKeepSignedIn] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const redirectParam = searchParams.get('redirect');
    const nextPath = redirectParam && redirectParam.startsWith('/') ? redirectParam : '/donations';
    setRedirectTo(nextPath);

    const alreadyLoggedIn = typeof window !== 'undefined' && localStorage.getItem('isLoggedIn') === 'true';
    if (alreadyLoggedIn) {
      router.replace(nextPath);
    }
  }, [router, searchParams]);

  const handleLogin = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!email.trim()) {
      setErrorMessage('이메일을 입력해주세요.');
      return;
    }

    if (!password.trim()) {
      setErrorMessage('비밀번호를 입력해주세요.');
      return;
    }

    const persistLoginState = (params: { email: string; name?: string; provider: string }) => {
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('loggedInEmail', params.email);
      if (params.name) {
        localStorage.setItem('loggedInName', params.name);
      }
      localStorage.setItem('loggedInProvider', params.provider);

      if (keepSignedIn) {
        localStorage.setItem('keepSignedIn', 'true');
      } else {
        localStorage.removeItem('keepSignedIn');
      }

      window.dispatchEvent(new Event('bodam-auth-change'));
    };

    const submit = async () => {
      setIsSubmitting(true);
      setErrorMessage('');
      try {
        const data = await apiRequest<{
          user: { id: string; email: string; name: string };
          access_token: string;
          csrf_token: string;
        }>('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });

        if (typeof window !== 'undefined') {
          sessionStorage.setItem('bodam_access_token', data.access_token);
          sessionStorage.setItem('bodam_csrf_token', data.csrf_token);
        }

        persistLoginState({ email: data.user.email, name: data.user.name, provider: 'password' });
        router.push(redirectTo);
      } catch (error) {
        if (error instanceof ApiError) {
          if (error.status === 401) {
            setErrorMessage('이메일 혹은 비밀번호가 올바르지 않습니다.');
          } else if (error.status === 403) {
            setErrorMessage('비활성화된 계정입니다. 고객센터로 문의해주세요.');
          } else {
            setErrorMessage(error.message);
          }
        } else {
          setErrorMessage('로그인 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
        }
      } finally {
        setIsSubmitting(false);
      }
    };

    void submit();
  };

  const handleSocialLogin = (provider: 'google' | 'kakao' | 'naver') => {
    setErrorMessage('소셜 로그인은 아직 준비 중입니다.');
  };

  return (
    <div className="bg-gray-50">
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">로그인</h1>
            <p className="text-gray-600">
              기부 과정을 이어가거나 마이페이지에서 기부 내역을 확인하려면 로그인하세요.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-8 items-start">
            <Card className="p-8 md:col-span-3">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">이메일로 로그인</h2>
              <form onSubmit={handleLogin} className="space-y-6">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    이메일
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                    비밀번호
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="비밀번호를 입력하세요"
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>

                <div className="flex items-center justify-between text-sm text-gray-600">
                  <label className="inline-flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={keepSignedIn}
                      onChange={(event) => setKeepSignedIn(event.target.checked)}
                      className="form-checkbox h-4 w-4 text-red-600"
                    />
                    <span>로그인 상태 유지</span>
                  </label>
                  <button
                    type="button"
                    className="text-red-600 hover:text-red-700"
                    onClick={() => router.push('/forgot-password')}
                  >
                    비밀번호 찾기
                  </button>
                </div>

                {errorMessage && (
                  <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
                    {errorMessage}
                  </div>
                )}

                <Button type="submit" variant="primary" size="lg" className="w-full" disabled={isSubmitting}>
                  로그인하기
                </Button>
              </form>
            </Card>

            <Card className="p-8 space-y-6 md:col-span-2">
              <h2 className="text-xl font-semibold text-gray-900">소셜 로그인</h2>
              <p className="text-sm text-gray-600">
                간편 로그인으로 빠르게 인증하고 기부를 진행할 수 있어요.
              </p>

              <Button
                variant="outline"
                size="md"
                className="w-full border-gray-300 text-gray-800 hover:border-red-400 hover:text-red-600"
                onClick={() => handleSocialLogin('google')}
              >
                <i className="ri-google-fill text-lg mr-2"></i>
                Google로 계속하기
              </Button>

              <Button
                variant="outline"
                size="md"
                className="w-full border-gray-300 text-gray-800 hover:border-red-400 hover:text-red-600"
                onClick={() => handleSocialLogin('kakao')}
              >
                <i className="ri-kakao-talk-fill text-lg mr-2 text-yellow-500"></i>
                카카오로 계속하기
              </Button>

              <Button
                variant="outline"
                size="md"
                className="w-full border-gray-300 text-gray-800 hover:border-red-400 hover:text-red-600"
                onClick={() => handleSocialLogin('naver')}
              >
                <i className="ri-naver-fill text-lg mr-2 text-green-600"></i>
                네이버로 계속하기
              </Button>

              <div className="text-sm text-gray-500">
                로그인에 어려움이 있으신가요?
                <br />
                고객센터 1588-1234 또는 support@firefighter-donation.com 으로 문의해주세요.
              </div>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}
