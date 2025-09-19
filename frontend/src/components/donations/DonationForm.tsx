import { useState } from 'react';

export interface DonationFormValues {
  amount: number;
  type: 'one_time' | 'recurring';
  frequency?: 'monthly' | 'yearly';
  message?: string;
  isAnonymous: boolean;
}

interface DonationFormProps {
  stationName: string;
  onSubmit?: (values: DonationFormValues) => Promise<void> | void;
}

export function DonationForm({ stationName, onSubmit }: DonationFormProps) {
  const [amount, setAmount] = useState(10000);
  const [type, setType] = useState<DonationFormValues['type']>('one_time');
  const [frequency, setFrequency] = useState<DonationFormValues['frequency']>('monthly');
  const [message, setMessage] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit?.({ amount, type, frequency: type === 'recurring' ? frequency : undefined, message, isAnonymous });
    } catch (err) {
      setError((err as Error).message || '기부 요청에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-lg flex-col gap-4 rounded-lg bg-white p-6 shadow">
      <h2 className="text-xl font-semibold">{stationName}에 기부하기</h2>
      <label className="flex flex-col gap-2">
        <span className="text-sm text-slate-600">기부 금액 (원)</span>
        <input
          type="number"
          min={1000}
          step={1000}
          value={amount}
          onChange={(event) => setAmount(Number(event.target.value))}
          className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
          required
        />
      </label>
      <div className="flex gap-4">
        <button
          type="button"
          onClick={() => setType('one_time')}
          className={`flex-1 rounded border px-3 py-2 text-sm transition ${
            type === 'one_time' ? 'border-primary bg-primary text-white' : 'border-slate-300'
          }`}
        >
          일시 기부
        </button>
        <button
          type="button"
          onClick={() => setType('recurring')}
          className={`flex-1 rounded border px-3 py-2 text-sm transition ${
            type === 'recurring' ? 'border-primary bg-primary text-white' : 'border-slate-300'
          }`}
        >
          정기 기부
        </button>
      </div>
      {type === 'recurring' ? (
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-600">정기결제 주기</span>
          <select
            value={frequency}
            onChange={(event) => setFrequency(event.target.value as DonationFormValues['frequency'])}
            className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
          >
            <option value="monthly">매월</option>
            <option value="yearly">매년</option>
          </select>
        </label>
      ) : null}
      <label className="flex flex-col gap-2">
        <span className="text-sm text-slate-600">응원 메시지 (선택)</span>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          maxLength={500}
          rows={3}
          className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
        />
      </label>
      <label className="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" checked={isAnonymous} onChange={(event) => setIsAnonymous(event.target.checked)} />
        익명으로 기부하기
      </label>
      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      <button
        type="submit"
        disabled={loading}
        className="rounded bg-primary px-4 py-2 font-medium text-white transition hover:bg-primary-dark disabled:opacity-60"
      >
        {loading ? '진행 중...' : '결제 페이지로 이동'}
      </button>
    </form>
  );
}
