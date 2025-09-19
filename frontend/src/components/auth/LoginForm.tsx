import { useState } from 'react';

interface LoginFormProps {
  onSubmit?: (credentials: { email: string; password: string }) => Promise<void> | void;
}

export function LoginForm({ onSubmit }: LoginFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit?.({ email, password });
    } catch (err) {
      setError((err as Error).message || '로그인에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-sm flex-col gap-4 rounded-lg bg-white p-6 shadow">
      <h2 className="text-xl font-semibold">로그인</h2>
      <label className="flex flex-col gap-2">
        <span className="text-sm text-slate-600">이메일</span>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
          required
        />
      </label>
      <label className="flex flex-col gap-2">
        <span className="text-sm text-slate-600">비밀번호</span>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
          required
        />
      </label>
      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      <button
        type="submit"
        disabled={loading}
        className="rounded bg-primary px-4 py-2 font-medium text-white transition hover:bg-primary-dark disabled:opacity-60"
      >
        {loading ? '확인 중...' : '로그인'}
      </button>
    </form>
  );
}
