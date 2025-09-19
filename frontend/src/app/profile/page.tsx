'use client';

import { useState } from 'react';
import { Dashboard } from '../../components/dashboard/Dashboard';

export default function ProfilePage() {
  const [name, setName] = useState('홍길동');
  const [phone, setPhone] = useState('01012345678');
  const [message, setMessage] = useState<string | null>(null);

  const handleSave = (event: React.FormEvent) => {
    event.preventDefault();
    setMessage('프로필이 저장되었습니다.');
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-10 px-4 py-12">
      <section className="rounded-lg bg-white p-6 shadow">
        <h1 className="text-3xl font-bold text-slate-900">내 프로필</h1>
        <form onSubmit={handleSave} className="mt-6 flex flex-col gap-4">
          <label className="flex flex-col gap-2">
            <span className="text-sm text-slate-600">이름</span>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-sm text-slate-600">휴대폰 번호</span>
            <input
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
            />
          </label>
          <button
            type="submit"
            className="rounded bg-primary px-4 py-2 font-medium text-white transition hover:bg-primary-dark"
          >
            저장하기
          </button>
          {message ? <p className="text-sm text-emerald-600">{message}</p> : null}
        </form>
      </section>

      <section className="rounded-lg bg-white p-6 shadow">
        <Dashboard
          totalDonations={8}
          totalAmount={560000}
          recurringCount={3}
          recentDonations={[]}
        />
      </section>
    </main>
  );
}
