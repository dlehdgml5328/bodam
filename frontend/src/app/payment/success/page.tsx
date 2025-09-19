import Link from 'next/link';

export default function PaymentSuccessPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-6 px-4 text-center">
      <div className="rounded-lg bg-white p-8 shadow">
        <h1 className="text-3xl font-bold text-emerald-600">결제가 완료되었습니다!</h1>
        <p className="mt-3 text-slate-600">
          기부해 주셔서 감사합니다. 이메일로 영수증과 기부 내역을 보내드렸습니다.
        </p>
        <div className="mt-6 flex justify-center gap-4">
          <Link href="/profile" className="rounded bg-primary px-4 py-2 font-medium text-white">
            기부 내역 보기
          </Link>
          <Link href="/stations" className="rounded border border-primary px-4 py-2 font-medium text-primary">
            다른 소방서 살펴보기
          </Link>
        </div>
      </div>
    </main>
  );
}
