import Link from 'next/link';

export default function PaymentFailurePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-6 px-4 text-center">
      <div className="rounded-lg bg-white p-8 shadow">
        <h1 className="text-3xl font-bold text-rose-600">결제를 완료할 수 없습니다</h1>
        <p className="mt-3 text-slate-600">
          결제 진행 중 오류가 발생했습니다. 결제 정보를 확인하거나 다시 시도해 주세요.
        </p>
        <div className="mt-6 flex justify-center gap-4">
          <Link href="/donate" className="rounded bg-primary px-4 py-2 font-medium text-white">
            다시 시도하기
          </Link>
          <Link href="/support" className="rounded border border-slate-300 px-4 py-2 font-medium text-slate-600">
            고객 지원 문의
          </Link>
        </div>
      </div>
    </main>
  );
}
