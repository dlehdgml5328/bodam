'use client';

import { useState, useEffect } from 'react';
import Card from '../base/Card';
import { apiRequest } from '@/lib/api';

interface Message {
  name: string;
  message: string;
  date: string;
  location: string;
}

export default function FirefighterMessages() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadMessages() {
      try {
        const data = await apiRequest<Message[]>('/messages?limit=4');
        if (!cancelled) {
          setMessages(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('[FirefighterMessages] Failed to fetch messages', error);
          setMessages([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadMessages();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (messages.length === 0) return;

    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % messages.length);
    }, 5000);

    return () => clearInterval(timer);
  }, [messages.length]);

  if (loading) {
    return (
      <section className="py-16 bg-gradient-to-br from-orange-50 to-red-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">메시지 로딩 중...</div>
        </div>
      </section>
    );
  }

  if (messages.length === 0) {
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
            <Card className="p-12 text-center">
              <p className="text-gray-500">아직 응원 메시지가 없습니다</p>
            </Card>
          </div>
        </div>
      </section>
    );
  }

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
