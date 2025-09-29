'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Card from '../base/Card';

export default function AdBanner() {
  const [currentSlide, setCurrentSlide] = useState(0);
  
  const banners = [
    {
      id: 1,
      title: '㈜커피빈과 함께하는 소방관 지원 캠페인',
      subtitle: '매월 1,000잔의 프리미엄 커피를 소방관들에게',
      image: 'https://readdy.ai/api/search-image?query=Professional%20coffee%20brand%20advertisement%20supporting%20Korean%20firefighters%2C%20premium%20coffee%20products%20display%2C%20corporate%20social%20responsibility%20campaign%2C%20warm%20and%20professional%20atmosphere%2C%20high-quality%20commercial%20photography&width=800&height=400&seq=ad1&orientation=landscape',
      sponsor: '㈜커피빈코리아',
      cta: '캠페인 참여하기'
    },
    {
      id: 2,
      title: '안전한 대한민국을 위한 시민연대',
      subtitle: '소방관 복지 향상을 위한 시민 모금 운동',
      image: 'https://readdy.ai/api/search-image?query=Korean%20citizens%20united%20for%20firefighter%20welfare%20campaign%2C%20community%20support%20advertisement%2C%20patriotic%20theme%20with%20Korean%20flag%20elements%2C%20professional%20campaign%20poster%20design%2C%20inspiring%20social%20movement%20imagery&width=800&height=400&seq=ad2&orientation=landscape',
      sponsor: '시민안전연대',
      cta: '후원하기'
    },
    {
      id: 3,
      title: '㈜따뜻한마음 정기후원 프로그램',
      subtitle: '매월 정기적으로 소방관들에게 전달되는 감사의 마음',
      image: 'https://readdy.ai/api/search-image?query=Corporate%20monthly%20donation%20program%20advertisement%20for%20Korean%20firefighters%2C%20professional%20business%20charity%20campaign%2C%20heartwarming%20corporate%20social%20responsibility%20theme%2C%20elegant%20and%20trustworthy%20design&width=800&height=400&seq=ad3&orientation=landscape',
      sponsor: '㈜따뜻한마음',
      cta: '정기후원 신청'
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % banners.length);
    }, 6000);

    return () => clearInterval(timer);
  }, [banners.length]);

  return (
    <section className="py-12 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            후원 기업과 함께하는 캠페인
          </h2>
          <p className="text-gray-600">
            소방관들을 지원하는 다양한 기업들의 따뜻한 마음을 소개합니다
          </p>
        </div>

        <div className="relative">
          <Card className="overflow-hidden">
            <div className="relative h-80 md:h-96">
              {banners.map((banner, index) => (
                <div
                  key={banner.id}
                  className={`absolute inset-0 transition-opacity duration-500 ${
                    index === currentSlide ? 'opacity-100' : 'opacity-0'
                  }`}
                >
                  <div className="flex flex-col md:flex-row h-full">
                    <div className="md:w-1/2 p-8 flex flex-col justify-center">
                      <div className="text-sm text-red-600 font-semibold mb-2">
                        {banner.sponsor}
                      </div>
                      <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
                        {banner.title}
                      </h3>
                      <p className="text-gray-600 mb-6 leading-relaxed">
                        {banner.subtitle}
                      </p>
                      <div>
                        <button className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-medium transition-colors duration-200 whitespace-nowrap cursor-pointer">
                          {banner.cta}
                        </button>
                      </div>
                    </div>
                    <div className="md:w-1/2 relative h-48 md:h-auto min-h-[200px]">
                      <Image
                        src={banner.image}
                        alt={banner.title}
                        fill
                        className="object-cover object-top"
                        sizes="(min-width: 768px) 50vw, 100vw"
                        priority={index === currentSlide}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* 슬라이드 인디케이터 */}
          <div className="flex justify-center space-x-2 mt-6">
            {banners.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                className={`w-3 h-3 rounded-full transition-colors duration-200 ${
                  index === currentSlide ? 'bg-red-600' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>

          {/* 이전/다음 버튼 */}
          <button
            onClick={() => setCurrentSlide((prev) => (prev - 1 + banners.length) % banners.length)}
            className="absolute left-4 top-1/2 transform -translate-y-1/2 w-10 h-10 bg-white bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg hover:bg-white transition-colors duration-200"
          >
            <i className="ri-arrow-left-s-line text-gray-700"></i>
          </button>
          <button
            onClick={() => setCurrentSlide((prev) => (prev + 1) % banners.length)}
            className="absolute right-4 top-1/2 transform -translate-y-1/2 w-10 h-10 bg-white bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg hover:bg-white transition-colors duration-200"
          >
            <i className="ri-arrow-right-s-line text-gray-700"></i>
          </button>
        </div>
      </div>
    </section>
  );
}
