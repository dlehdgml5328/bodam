'use client';

import { AdminPanel } from '../../components/admin/AdminPanel';

const METRICS = [
  { label: '오늘 접속자', value: '1,024명' },
  { label: '승인 대기 콘텐츠', value: '6건', description: '뉴스/재난문자 검토' },
  { label: '환불 요청', value: '2건', description: '확인 필요' },
];

const PENDING_REVIEWS = [
  { id: 'content-1', title: '서울 강남구 화재 사고 요약', submittedAt: new Date().toISOString() },
  { id: 'content-2', title: '재난 문자 – 기상 특보', submittedAt: new Date().toISOString() },
];

export default function AdminPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-4 py-12">
      <header className="rounded-lg bg-white p-6 shadow">
        <h1 className="text-3xl font-bold text-slate-900">관리자 대시보드</h1>
        <p className="mt-2 text-sm text-slate-600">
          콘텐츠 검토, 환불 처리, 실시간 지표를 확인할 수 있는 관리자 전용 페이지입니다.
        </p>
      </header>

      <AdminPanel metrics={METRICS} pendingReviews={PENDING_REVIEWS} />
    </main>
  );
}
