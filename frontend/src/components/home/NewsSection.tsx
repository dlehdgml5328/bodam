'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Card from '../base/Card';
import { apiRequest } from '@/lib/api';

interface VideoNews {
  id: number;
  title: string;
  thumbnail: string;
  duration: string;
  time: string;
  videoUrl?: string | null;
  articleUrl: string;
  category: string;
  summary: string;
  views: number;
  likes: number;
  videoId: string;
}

interface BreakingNews {
  title: string;
  time: string;
  isBreaking: boolean;
  link: string;
}

export default function NewsSection() {
  const [currentVideoPage, setCurrentVideoPage] = useState(0);
  const [currentBreakingIndex, setCurrentBreakingIndex] = useState(0);
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<VideoNews | null>(null);
  const [videoNews, setVideoNews] = useState<VideoNews[]>([]);
  const [breakingNews, setBreakingNews] = useState<BreakingNews[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadNews() {
      try {
        const [videos, breaking] = await Promise.all([
          apiRequest<VideoNews[]>('/api/news/videos?limit=50'),
          apiRequest<BreakingNews[]>('/api/news/breaking?limit=15'),
        ]);

        if (!cancelled) {
          // 중복 제거: id 기준으로 unique하게
          const uniqueVideos = Array.isArray(videos)
            ? videos.filter((video, index, self) =>
                index === self.findIndex((v) => v.id === video.id)
              )
            : [];

          setVideoNews((prev) => {
            // 기존 뉴스와 새로운 뉴스 합치기
            const combined = [...prev];
            uniqueVideos.forEach((newVideo) => {
              // 이미 존재하는 뉴스가 아니면 추가
              if (!combined.find((v) => v.id === newVideo.id)) {
                combined.push(newVideo);
              }
            });
            return combined;
          });

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

  const getVisibleVideoNews = () => {
    if (videoNews.length === 0) return [];
    const startIndex = currentVideoPage * 4;
    return videoNews.slice(startIndex, startIndex + 4);
  };

  const totalVideoPages = Math.ceil(videoNews.length / 4);

  const handlePrevPage = () => {
    setCurrentVideoPage((prev) => (prev > 0 ? prev - 1 : totalVideoPages - 1));
  };

  const handleNextPage = () => {
    setCurrentVideoPage((prev) => (prev < totalVideoPages - 1 ? prev + 1 : 0));
  };

  const getVisibleBreakingNews = () => {
    if (breakingNews.length === 0) return [];
    const count = Math.min(8, breakingNews.length);
    const visible = [];
    for (let i = 0; i < count; i++) {
      visible.push(breakingNews[(currentBreakingIndex + i) % breakingNews.length]);
    }
    return visible;
  };

  const handleVideoClick = (news: VideoNews) => {
    if (news.videoUrl) {
      setSelectedVideo(news);
      setShowVideoModal(true);
    } else {
      if (news.articleUrl) {
        window.open(news.articleUrl, '_blank', 'noopener,noreferrer');
      }
    }
  };

  const handleCloseModal = () => {
    setShowVideoModal(false);
    setSelectedVideo(null);
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

  const displayedVideoNews = getVisibleVideoNews();
  const displayedBreakingNews = getVisibleBreakingNews();

  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 실시간 주요 뉴스 - 영상 뉴스 */}
        <div className="mb-16">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded-full mr-2 animate-pulse"></div>
              실시간 주요 뉴스
            </h2>
            {videoNews.length > 4 && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">
                  {currentVideoPage + 1} / {totalVideoPages}
                </span>
                <button
                  onClick={handlePrevPage}
                  className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                >
                  <i className="ri-arrow-left-s-line text-gray-700"></i>
                </button>
                <button
                  onClick={handleNextPage}
                  className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                >
                  <i className="ri-arrow-right-s-line text-gray-700"></i>
                </button>
              </div>
            )}
          </div>

          {displayedVideoNews.length === 0 ? (
            <Card className="p-12 text-center">
              <p className="text-gray-500">현재 표시할 영상 뉴스가 없습니다</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {displayedVideoNews.map((news) => (
                <div
                  key={news.id}
                  className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer"
                  onClick={() => handleVideoClick(news)}
                >
                  <div className="relative w-full h-48">
                    <Image
                      src={news.thumbnail}
                      alt={news.title}
                      fill
                      className="object-cover object-top"
                      sizes="(min-width: 768px) 50vw, 100vw"
                    />
                    <div className="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-300">
                      <div className="w-16 h-16 bg-red-600 bg-opacity-90 rounded-full flex items-center justify-center">
                        <i className="ri-play-fill text-white text-2xl"></i>
                      </div>
                    </div>
                    <div className="absolute top-4 left-4">
                      <span className="bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                        영상
                      </span>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-3">
                      <span className="bg-red-600 text-white px-3 py-1 rounded-full text-xs font-medium">
                        {news.category}
                      </span>
                      <div className="flex items-center text-gray-500 text-sm">
                        <i className="ri-time-line mr-1"></i>
                        {news.time}
                      </div>
                    </div>
                    <h3 className="font-bold text-gray-900 text-lg mb-2 line-clamp-2">
                      {news.title}
                    </h3>
                    <p className="text-gray-600 text-sm line-clamp-2">
                      {news.summary}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

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

      {/* 영상 모달 */}
      {showVideoModal && selectedVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl overflow-hidden w-full max-w-4xl mx-4 max-h-[90vh]">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900">{selectedVideo.title}</h3>
              <button
                onClick={handleCloseModal}
                className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors duration-200"
              >
                <i className="ri-close-line text-xl text-gray-500"></i>
              </button>
            </div>
            {selectedVideo.videoUrl ? (
              <div className="relative">
                <iframe
                  src={selectedVideo.videoUrl}
                  title={selectedVideo.title}
                  className="w-full h-[60vh] border-0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
            ) : (
              <div className="relative bg-black">
                <Image
                  src={selectedVideo.thumbnail}
                  alt={selectedVideo.title}
                  width={1280}
                  height={720}
                  className="w-full h-[60vh] object-cover opacity-70"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <button
                    onClick={() => window.open(selectedVideo.articleUrl, '_blank', 'noopener,noreferrer')}
                    className="flex items-center space-x-2 rounded-full bg-red-600 px-6 py-3 text-white shadow-lg hover:bg-red-700 transition-colors duration-200"
                  >
                    <i className="ri-external-link-fill text-lg"></i>
                    <span>기사 보러가기</span>
                  </button>
                </div>
              </div>
            )}
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-red-600 font-medium">{selectedVideo.category}</span>
                <div className="flex items-center text-gray-500 text-sm">
                  <i className="ri-time-line mr-1"></i>
                  {selectedVideo.time}
                </div>
              </div>
              <p className="text-gray-600 leading-relaxed">{selectedVideo.summary}</p>
              {!selectedVideo.videoUrl && selectedVideo.articleUrl && (
                <div className="flex justify-end mt-4 pt-4 border-t border-gray-100">
                  <a
                    href={selectedVideo.articleUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-2 text-red-600 hover:text-red-700 transition-colors duration-200"
                  >
                    <i className="ri-external-link-line"></i>
                    <span>원문 보기</span>
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
