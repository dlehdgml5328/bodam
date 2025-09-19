import { useState } from 'react';

interface SignupFormProps {
  onSubmit?: (
    payload: {
      email: string;
      password: string;
      name: string;
      phone?: string;
    }
  ) => Promise<void> | void;
}

export function SignupForm({ onSubmit }: SignupFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);

    try {
      await onSubmit?.({ email, password, name, phone: phone || undefined });
      setMessage('인증 이메일을 확인해 주세요.');
    } catch (err) {
      setError((err as Error).message || '회원가입에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-sm flex-col gap-4 rounded-lg bg-white p-6 shadow">
      <h2 className="text-xl font-semibold">회원가입</h2>
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
          minLength={8}
          required
        />
      </label>
      <label className="flex flex-col gap-2">
        <span className="text-sm text-slate-600">이름</span>
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
          minLength={2}
          required
        />
      </label>
      <label className="flex flex-col gap-2">
        <span className="text-sm text-slate-600">휴대폰 번호 (선택)</span>
        <input
          type="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          placeholder="01012345678"
          className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
        />
      </label>
      {message ? <p className="text-sm text-green-600">{message}</p> : null}
      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      <button
        type="submit"
        disabled={loading}
        className="rounded bg-primary px-4 py-2 font-medium text-white transition hover:bg-primary-dark disabled:opacity-60"
      >
        {loading ? '확인 중...' : '회원가입'}
      </button>
    </form>
  );
}
