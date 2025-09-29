'use client';

import { useRouter } from 'next/navigation';
import Footer from '@/components/feature/Footer';
import ScrollToTop from '@/components/feature/ScrollToTop';
import Button from '@/components/base/Button';

export default function NotFoundPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 text-center px-4">
      <div className="max-w-2xl">
        <h1 className="text-6xl md:text-7xl font-bold text-red-600 mb-4">404</h1>
        <h2 className="text-2xl md:text-3xl font-semibold text-gray-900 mb-6">페이지를 찾을 수 없어요</h2>
        <p className="text-lg text-gray-600 mb-8">
          요청하신 페이지가 존재하지 않거나 이동되었어요.<br />
          필요한 정보가 있다면 언제든 알려주세요.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Button onClick={() => router.back()} className="px-8">
            이전 페이지로 돌아가기
          </Button>
          <Button variant="outline" onClick={() => router.push('/')} className="px-8">
            홈으로 이동
          </Button>
        </div>
      </div>

      <div className="w-full mt-16">
        <Footer />
        <ScrollToTop />
      </div>
    </div>
  );
}
