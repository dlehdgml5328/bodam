'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { apiRequest, ApiError } from '@/lib/api';

export default function SignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [redirectTo, setRedirectTo] = useState('/login');

  useEffect(() => {
    const redirectParam = searchParams.get('redirect');
    if (redirectParam && redirectParam.startsWith('/')) {
      setRedirectTo(`/login?redirect=${encodeURIComponent(redirectParam)}`);
    }
  }, [searchParams]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!name.trim()) {
      setErrorMessage('이름을 입력해주세요.');
      return;
    }

    if (!email.trim()) {
      setErrorMessage('이메일을 입력해주세요.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('비밀번호는 최소 8자 이상이어야 합니다.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('비밀번호가 일치하지 않습니다.');
      return;
    }

    const submit = async () => {
      setIsSubmitting(true);
      setErrorMessage('');
      setSuccessMessage('');
      try {
        await apiRequest<{
          user_id: string;
          email: string;
          message: string;
        }>('/auth/signup', {
          method: 'POST',
          body: JSON.stringify({ name, email, password, phone: phone || undefined }),
        });
        setSuccessMessage('회원가입이 완료되었습니다. 이메일을 확인한 뒤 로그인해주세요.');
        setTimeout(() => {
          router.push(redirectTo);
        }, 1200);
      } catch (error) {
        if (error instanceof ApiError) {
          if (error.status === 409) {
            setErrorMessage('이미 가입된 이메일입니다. 다른 이메일을 사용해주세요.');
          } else {
            setErrorMessage(error.message);
          }
        } else {
          setErrorMessage('회원가입 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
        }
      } finally {
        setIsSubmitting(false);
      }
    };

    void submit();
  };

  return (
    <div className="bg-gray-50">
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">회원가입</h1>
            <p className="text-gray-600">보담과 함께 소방관에게 따뜻한 마음을 전해주세요.</p>
          </div>

          <Card className="p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  이름
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="홍길동"
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>

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
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                  휴대폰 번호 (선택)
                </label>
                <input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  placeholder="01012345678"
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
                <p className="text-xs text-gray-500 mt-2">비밀번호는 최소 8자 이상이어야 합니다.</p>
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  비밀번호 확인
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  placeholder="비밀번호를 다시 입력하세요"
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>

              {errorMessage && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
                  {errorMessage}
                </div>
              )}

              {successMessage && (
                <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-3 rounded-lg">
                  {successMessage}
                </div>
              )}

              <Button type="submit" variant="primary" size="lg" className="w-full" disabled={isSubmitting}>
                가입하기
              </Button>
            </form>

            <div className="text-sm text-gray-600 mt-6 text-center">
              이미 계정이 있으신가요?{' '}
              <button
                className="text-red-600 hover:text-red-700 font-medium"
                onClick={() => router.push(redirectTo)}
                type="button"
              >
                로그인하러 가기
              </button>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}
