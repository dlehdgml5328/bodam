import { DonationForm } from '../../../components/donations/DonationForm';
import { Dashboard } from '../../../components/dashboard/Dashboard';

interface StationPageProps {
  params: { id: string };
}

export default function StationPage({ params }: StationPageProps) {
  const stationId = params.id;
  const mockDonations = [
    {
      donationId: 'donation-1',
      amount: 30000,
      fireStationName: '강남소방서',
      status: 'completed',
      createdAt: new Date().toISOString(),
    },
  ];

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-4 py-12">
      <header className="rounded-lg bg-white p-6 shadow">
        <h1 className="text-3xl font-bold text-slate-900">소방서 상세 정보</h1>
        <p className="mt-2 text-sm text-slate-600">Station ID: {stationId}</p>
      </header>

      <section className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="text-xl font-semibold">현황</h2>
          <p className="mt-2 text-sm text-slate-600">
            최근 30일 동안 12건의 기부가 완료되었으며, 현재 긴급 장비 교체를 위해 추가 후원이 필요합니다.
          </p>
          <div className="mt-6">
            <Dashboard
              totalDonations={12}
              totalAmount={1250000}
              recurringCount={5}
              recentDonations={mockDonations}
            />
          </div>
        </div>
        <div className="rounded-lg bg-white p-6 shadow">
          <DonationForm
            stationName="강남소방서"
            onSubmit={async () => {
              // TODO: integrate with donations API
            }}
          />
        </div>
      </section>
    </main>
  );
}
