'use client';

import { FormEvent, useState } from 'react';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { apiRequest, ApiError } from '@/lib/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [requestMessage, setRequestMessage] = useState('');
  const [requestError, setRequestError] = useState('');
  const [isRequesting, setIsRequesting] = useState(false);
  const [resetToken, setResetToken] = useState('');

  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [confirmMessage, setConfirmMessage] = useState('');
  const [confirmError, setConfirmError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRequest = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!email.trim()) {
      setRequestError('이메일을 입력해주세요.');
      return;
    }

    const submit = async () => {
      setIsRequesting(true);
      setRequestError('');
      setRequestMessage('');
      try {
        const response = await apiRequest<{ message: string; reset_token?: string }>(
          '/auth/password-reset/request',
          {
            method: 'POST',
            body: JSON.stringify({ email }),
          }
        );
        setRequestMessage(response.message);
        if (response.reset_token) {
          setResetToken(response.reset_token);
          setToken(response.reset_token);
        }
      } catch (error) {
        if (error instanceof ApiError) {
          setRequestError(error.message);
        } else {
          setRequestError('요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
        }
      } finally {
        setIsRequesting(false);
      }
    };

    void submit();
  };

  const handleConfirm = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!token.trim()) {
      setConfirmError('재설정 토큰을 입력해주세요.');
      return;
    }

    if (newPassword.length < 8) {
      setConfirmError('비밀번호는 최소 8자 이상이어야 합니다.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setConfirmError('비밀번호가 일치하지 않습니다.');
      return;
    }

    const submit = async () => {
      setIsSubmitting(true);
      setConfirmError('');
      setConfirmMessage('');
      try {
        const response = await apiRequest<{ message: string }>(
          '/auth/password-reset/confirm',
          {
            method: 'POST',
            body: JSON.stringify({ token, new_password: newPassword }),
          }
        );
        setConfirmMessage(response.message);
      } catch (error) {
        if (error instanceof ApiError) {
          if (error.status === 400 && error.message === 'TOKEN_EXPIRED') {
            setConfirmError('토큰이 만료되었습니다. 다시 요청해주세요.');
          } else {
            setConfirmError('토큰을 확인할 수 없습니다. 다시 시도해주세요.');
          }
        } else {
          setConfirmError('비밀번호 재설정 중 오류가 발생했습니다.');
        }
      } finally {
        setIsSubmitting(false);
      }
    };

    void submit();
  };

  return (
    <div className="bg-gray-50">
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card className="p-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">비밀번호 재설정 요청</h1>
            <p className="text-sm text-gray-600 mb-6">
              가입하신 이메일을 입력하시면 비밀번호 재설정 안내를 보내드립니다.
            </p>
            <form onSubmit={handleRequest} className="space-y-6">
              <div>
                <label htmlFor="requestEmail" className="block text-sm font-medium text-gray-700 mb-2">
                  이메일
                </label>
                <input
                  id="requestEmail"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>

              {requestError && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
                  {requestError}
                </div>
              )}

              {requestMessage && (
                <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-3 rounded-lg">
                  {requestMessage}
                </div>
              )}

              {resetToken && (
                <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 text-xs px-4 py-3 rounded-lg">
                  개발 편의를 위해 발급된 토큰입니다: <code className="break-words">{resetToken}</code>
                </div>
              )}

              <Button type="submit" variant="primary" size="md" className="w-full" disabled={isRequesting}>
                재설정 링크 보내기
              </Button>
            </form>
          </Card>

          <Card className="p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">새 비밀번호 설정</h2>
            <p className="text-sm text-gray-600 mb-6">
              이메일로 받은 토큰을 입력하고 새로운 비밀번호를 만들어주세요.
            </p>
            <form onSubmit={handleConfirm} className="space-y-6">
              <div>
                <label htmlFor="token" className="block text-sm font-medium text-gray-700 mb-2">
                  재설정 토큰
                </label>
                <input
                  id="token"
                  type="text"
                  value={token}
                  onChange={(event) => setToken(event.target.value)}
                  placeholder="발급받은 토큰을 입력하세요"
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>

              <div>
                <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  새 비밀번호
                </label>
                <input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  placeholder="새 비밀번호"
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

              {confirmError && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
                  {confirmError}
                </div>
              )}

              {confirmMessage && (
                <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-3 rounded-lg">
                  {confirmMessage}
                </div>
              )}

              <Button type="submit" variant="primary" size="md" className="w-full" disabled={isSubmitting}>
                비밀번호 재설정
              </Button>
            </form>
          </Card>
        </div>
      </section>
    </div>
  );
}
