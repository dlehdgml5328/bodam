import HeroSection from '@/components/home/HeroSection';
import DashboardStats from '@/components/home/DashboardStats';
import AdBanner from '@/components/home/AdBanner';
import DonationRanking from '@/components/home/DonationRanking';
import FirefighterMessages from '@/components/home/FirefighterMessages';
import NewsSection from '@/components/home/NewsSection';
import EmergencyStatus from '@/components/home/EmergencyStatus';
import DonateSection from '@/components/home/DonateSection';
import { getEmergencyStations } from '@/lib/data/emergency';

export default async function HomePage() {
  const emergencyStations = await getEmergencyStations();

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
