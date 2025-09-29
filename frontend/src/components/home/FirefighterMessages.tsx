'use client';

import { useState, useEffect } from 'react';
import Card from '../base/Card';

export default function FirefighterMessages() {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const messages = [
    {
      name: '김민수',
      message: '항상 우리의 안전을 지켜주셔서 감사합니다. 추운 겨울밤에도 힘내세요! 따뜻한 커피 한 잔으로나마 응원합니다.',
      date: '2024.03.15',
      location: '서울시 중구'
    },
    {
      name: '박지영',
      message: '지난주 화재 현장에서 우리 가족을 구해주신 소방관님들께 정말 감사드립니다. 작은 마음이지만 커피로 보답하고 싶어요.',
      date: '2024.03.14',
      location: '부산시 해운대구'
    },
    {
      name: '이상호',
      message: '24시간 언제든 출동해주시는 소방관님들이 정말 대단합니다. 늘 건강하시고 안전하게 근무하세요!',
      date: '2024.03.13',
      location: '대구시 수성구'
    },
    {
      name: '최수진',
      message: '응급상황에서 신속하게 대응해주시는 모습이 정말 감동적이에요. 소방관님들도 따뜻한 커피로 잠시나마 휴식하세요.',
      date: '2024.03.12',
      location: '인천시 연수구'
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % messages.length);
    }, 5000);

    return () => clearInterval(timer);
  }, [messages.length]);

  return (
    <section className="py-16 bg-gradient-to-br from-orange-50 to-red-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            시민 응원 메시지
          </h2>
          <p className="text-lg text-gray-600">
            소방관님들을 향한 시민들의 따뜻한 응원과 감사 메시지입니다
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <Card className="relative overflow-hidden">
            <div className="flex items-center space-x-4 mb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                <i className="ri-user-heart-fill text-blue-600 text-2xl"></i>
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">
                  {messages[currentIndex].name}
                </h3>
                <p className="text-gray-600">{messages[currentIndex].location}</p>
              </div>
              <div className="ml-auto text-sm text-gray-500">
                {messages[currentIndex].date}
              </div>
            </div>
            
            <blockquote className="text-lg text-gray-700 leading-relaxed mb-6">
              &quot;{messages[currentIndex].message}&quot;
            </blockquote>
            
            <div className="flex justify-center space-x-2">
              {messages.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentIndex(index)}
                  className={`w-3 h-3 rounded-full transition-colors duration-200 ${
                    index === currentIndex ? 'bg-red-600' : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
