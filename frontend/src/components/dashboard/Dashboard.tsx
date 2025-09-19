import Link from 'next/link';

export interface DonationSummary {
  donationId: string;
  amount: number;
  fireStationName: string;
  status: string;
  createdAt: string;
}

interface DashboardProps {
  totalDonations: number;
  totalAmount: number;
  recurringCount: number;
  recentDonations: DonationSummary[];
}

export function Dashboard({ totalDonations, totalAmount, recurringCount, recentDonations }: DashboardProps) {
  return (
    <div className="flex flex-col gap-8">
      <section className="grid gap-4 sm:grid-cols-3">
        <DashboardCard title="총 기부 횟수" value={`${totalDonations}회`} />
        <DashboardCard title="총 기부 금액" value={`${totalAmount.toLocaleString()}원`} />
        <DashboardCard title="정기 기부" value={`${recurringCount}건`} />
      </section>

      <section className="rounded-lg bg-white p-6 shadow">
        <header className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">최근 기부 내역</h3>
          <Link href="/donations" className="text-sm text-primary">
            전체보기
          </Link>
        </header>
        <div className="space-y-3">
          {recentDonations.length === 0 ? (
            <p className="text-sm text-slate-500">아직 기부 내역이 없습니다.</p>
          ) : (
            recentDonations.map((donation) => (
              <div key={donation.donationId} className="flex items-center justify-between rounded border border-slate-200 px-4 py-3">
                <div>
                  <p className="font-medium text-slate-900">{donation.fireStationName}</p>
                  <p className="text-xs text-slate-500">{new Date(donation.createdAt).toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-primary">{donation.amount.toLocaleString()}원</p>
                  <p className="text-xs text-slate-500">{donation.status}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

interface DashboardCardProps {
  title: string;
  value: string;
}

function DashboardCard({ title, value }: DashboardCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
