'use client';

import { useState, useEffect } from 'react';
import Card from '../base/Card';
import { apiRequest } from '@/lib/api';

interface BreakingNews {
  title: string;
  time: string;
  isBreaking: boolean;
  link: string;
}

export default function NewsSection() {
  const [currentBreakingIndex, setCurrentBreakingIndex] = useState(0);
  const [breakingNews, setBreakingNews] = useState<BreakingNews[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadNews() {
      try {
        const breaking = await apiRequest<BreakingNews[]>('/api/news/breaking?limit=15');

        if (!cancelled) {
          setBreakingNews(Array.isArray(breaking) ? breaking : []);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('[NewsSection] Failed to fetch news', error);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadNews();

    // 30초마다 새로운 뉴스 확인
    const interval = setInterval(loadNews, 30000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // 속보 뉴스 자동 회전 (10초마다)
  useEffect(() => {
    if (breakingNews.length === 0) return;

    const breakingTimer = setInterval(() => {
      setCurrentBreakingIndex((prev) => (prev + 1) % breakingNews.length);
    }, 10000);
    return () => clearInterval(breakingTimer);
  }, [breakingNews.length]);

  const getVisibleBreakingNews = () => {
    if (breakingNews.length === 0) return [];
    // 데이터가 8개보다 적으면 실제 개수만큼만 표시 (중복 방지)
    const count = Math.min(8, breakingNews.length);
    const visible = [];
    for (let i = 0; i < count; i++) {
      visible.push(breakingNews[(currentBreakingIndex + i) % breakingNews.length]);
    }
    return visible;
  };

  const handleBreakingNewsClick = (newsItem: BreakingNews) => {
    window.open(newsItem.link, '_blank', 'noopener,noreferrer');
  };

  if (loading) {
    return (
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">뉴스 로딩 중...</div>
        </div>
      </section>
    );
  }

  const displayedBreakingNews = getVisibleBreakingNews();

  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 실시간 속보 */}
        <div>
          <div className="flex items-center space-x-2 mb-8">
            <div className="w-3 h-3 bg-orange-500 rounded-full animate-pulse"></div>
            <h2 className="text-2xl font-bold text-gray-900">실시간 속보</h2>
            {breakingNews.length > 0 && <span className="text-sm text-gray-500 ml-auto">10초마다 업데이트</span>}
          </div>

          <Card>
            {displayedBreakingNews.length === 0 ? (
              <div className="p-12 text-center">
                <p className="text-gray-500">현재 표시할 속보가 없습니다</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {displayedBreakingNews.map((news, index) => (
                  <div
                    key={`breaking-${currentBreakingIndex}-${index}`}
                    className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg transition-colors duration-200 cursor-pointer"
                    onClick={() => handleBreakingNewsClick(news)}
                  >
                    <div className="flex-shrink-0 mt-1">
                      {news.isBreaking ? (
                        <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full font-bold">
                          속보
                        </span>
                      ) : (
                        <div className="w-2 h-2 bg-gray-400 rounded-full mt-2"></div>
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="text-gray-900 font-medium mb-1 leading-tight hover:text-red-600 transition-colors duration-200">
                        {news.title}
                      </h4>
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-gray-500">{news.time}</p>
                        <i className="ri-external-link-line text-gray-400 text-sm"></i>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </section>
  );
}
