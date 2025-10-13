import HeroSection from '@/components/home/HeroSection';
import DashboardStats from '@/components/home/DashboardStats';
import AdBanner from '@/components/home/AdBanner';
import DonationRanking from '@/components/home/DonationRanking';
import FirefighterMessages from '@/components/home/FirefighterMessages';
import NewsSection from '@/components/home/NewsSection';
import EmergencyStatus from '@/components/home/EmergencyStatus';
import DonateSection from '@/components/home/DonateSection';
import { getActiveIncidents } from '@/lib/data/incidents';

export default async function HomePage() {
  // 진행 중인 화재 사고 가져오기
  const activeIncidents = await getActiveIncidents();

  // 화재 사고를 EmergencyStatus 컴포넌트 형식에 맞게 변환
  const emergencyStations = activeIncidents.map((incident) => ({
    name: incident.title,
    location: incident.location_address,
    status:
      incident.status === 'dispatching'
        ? '출동 중'
        : incident.status === 'suppressing'
          ? '진압 중'
          : '대응 완료',
    priority:
      incident.severity === 'critical'
        ? ('high' as const)
        : incident.severity === 'high'
          ? ('high' as const)
          : incident.severity === 'medium'
            ? ('medium' as const)
            : ('low' as const),
    time: new Date(incident.occurred_at).toLocaleString('ko-KR', {
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
  }));

  return (
    <>
      <HeroSection />
      <DashboardStats />
      <AdBanner />
      <DonationRanking />
      <FirefighterMessages />
      <NewsSection />
      <EmergencyStatus stations={emergencyStations} />
      <DonateSection />
    </>
  );
}
