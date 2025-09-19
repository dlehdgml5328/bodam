interface MetricCard {
  label: string;
  value: string;
  description?: string;
}

interface AdminPanelProps {
  metrics: MetricCard[];
  pendingReviews: Array<{ id: string; title: string; submittedAt: string }>;
}

export function AdminPanel({ metrics, pendingReviews }: AdminPanelProps) {
  return (
    <div className="flex flex-col gap-8">
      <section className="grid gap-4 md:grid-cols-3">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">{metric.label}</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{metric.value}</p>
            {metric.description ? <p className="mt-1 text-xs text-slate-500">{metric.description}</p> : null}
          </div>
        ))}
      </section>

      <section className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-semibold">승인 대기 콘텐츠</h3>
        <div className="space-y-3">
          {pendingReviews.length === 0 ? (
            <p className="text-sm text-slate-500">검토할 콘텐츠가 없습니다.</p>
          ) : (
            pendingReviews.map((item) => (
              <div key={item.id} className="flex items-center justify-between rounded border border-slate-200 px-4 py-3">
                <div>
                  <p className="font-medium text-slate-900">{item.title}</p>
                  <p className="text-xs text-slate-500">{new Date(item.submittedAt).toLocaleString()}</p>
                </div>
                <div className="flex gap-2">
                  <button className="rounded border border-emerald-500 px-3 py-1 text-sm text-emerald-600 hover:bg-emerald-50">
                    승인
                  </button>
                  <button className="rounded border border-rose-500 px-3 py-1 text-sm text-rose-600 hover:bg-rose-50">
                    거절
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
