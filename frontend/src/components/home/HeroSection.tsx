'use client';

import Button from '../base/Button';
import { useRouter } from 'next/navigation';

export default function HeroSection() {
  const router = useRouter();

  const handleDonationClick = () => {
    router.push('/donations');
  };

  const handleDonationStatusClick = () => {
    router.push('/donation-ranking');
  };

  return (
    <section 
      className="relative h-[80vh] flex items-center justify-center bg-cover bg-center bg-no-repeat"
      style={{
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.3)), url('https://readdy.ai/api/search-image?query=Korean%20firefighters%20in%20action%20with%20bright%20red%20fire%20truck%2C%20warm%20lighting%2C%20heroic%20atmosphere%2C%20professional%20emergency%20response%20scene%20with%20coffee%20support%20theme%2C%20cinematic%20quality%2C%20inspiring%20and%20heartwarming%20mood%2C%20dominant%20red%20and%20orange%20color%20palette%2C%20modern%20firefighting%20equipment%2C%20red%20emergency%20vehicle%20prominently%20featured&width=1920&height=1080&seq=hero-main-red&orientation=landscape')`
      }}
    >
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center text-white">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            소방관들에게<br />
            <span className="text-orange-400">따뜻한 커피 한 잔을</span><br />
            보담하세요
          </h1>
          <p className="text-xl md:text-2xl mb-8 text-gray-100 max-w-3xl mx-auto">
            24시간 우리를 지키는 소방관들에게 따뜻한 마음을 전해보세요
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button variant="donate" size="lg" className="text-xl px-12 py-4" onClick={handleDonationClick}>
              <i className="ri-heart-fill mr-2"></i>
              지금 기부하기
            </Button>
            <Button 
              variant="outline" 
              size="lg" 
              className="text-xl px-12 py-4 border-white text-white hover:bg-white hover:text-gray-900"
              onClick={handleDonationStatusClick}
            >
              기부 현황 보기
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
