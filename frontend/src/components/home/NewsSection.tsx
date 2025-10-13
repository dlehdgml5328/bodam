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
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
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
          apiRequest<VideoNews[]>('/news/videos?limit=6'),
          apiRequest<BreakingNews[]>('/news/breaking?limit=15'),
        ]);

        if (!cancelled) {
          setVideoNews(Array.isArray(videos) ? videos : []);
          setBreakingNews(Array.isArray(breaking) ? breaking : []);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('[NewsSection] Failed to fetch news', error);
          setVideoNews([]);
          setBreakingNews([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadNews();

    return () => {
      cancelled = true;
    };
  }, []);

  // 비디오 뉴스 자동 회전 (10초마다)
  useEffect(() => {
    if (videoNews.length === 0) return;

    const videoTimer = setInterval(() => {
      setCurrentVideoIndex((prev) => (prev + 1) % videoNews.length);
    }, 10000);
    return () => clearInterval(videoTimer);
  }, [videoNews.length]);

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
    const visible = [];
    for (let i = 0; i < 4; i++) {
      visible.push(videoNews[(currentVideoIndex + i) % videoNews.length]);
    }
    return visible;
  };

  const getVisibleBreakingNews = () => {
    if (breakingNews.length === 0) return [];
    const visible = [];
    for (let i = 0; i < 8; i++) {
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
        {/* 실시간 주요 뉴스 - 2x2 그리드 */}
        <div className="mb-16">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded-full mr-2 animate-pulse"></div>
              실시간 주요 뉴스
            </h2>
            {videoNews.length > 0 && <span className="text-sm text-gray-500">10초마다 업데이트</span>}
          </div>

          {displayedVideoNews.length === 0 ? (
            <Card className="p-12 text-center">
              <p className="text-gray-500">현재 표시할 영상 뉴스가 없습니다</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {displayedVideoNews.map((news, index) => (
                <div
                  key={index}
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
                      priority={index === currentVideoIndex}
                    />
                    <div className="absolute inset-0 bg-black bg-black/30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-300">
                      <div className="w-16 h-16 bg-red-600 bg-red-600/90 rounded-full flex items-center justify-center">
                        <i className="ri-play-fill text-white text-2xl"></i>
                      </div>
                    </div>
                    <div className="absolute top-4 left-4">
                      <span className="bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                        영상
                      </span>
                    </div>
                    <div className="absolute bottom-4 right-4">
                      <span className="bg-black bg-black/70 text-white px-2 py-1 rounded text-sm">
                        {news.duration}
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
                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span className="flex items-center">
                          <i className="ri-eye-line mr-1"></i>
                          {news.views}
                        </span>
                        <span className="flex items-center">
                          <i className="ri-heart-line mr-1"></i>
                          {news.likes}
                        </span>
                      </div>
                      <div className="w-8 h-8 bg-red-600 bg-red-600/80 rounded-full flex items-center justify-center">
                        <i className="ri-play-fill text-white text-sm"></i>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 실시간 속보 - 가로로 길게 */}
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
        <div className="fixed inset-0 bg-black bg-black/80 flex items-center justify-center z-50">
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
                  className="w-full h-[60vh]"
                  frameBorder="0"
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
              <div className="flex items-center space-x-6 mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">
                <span className="flex items-center">
                  <i className="ri-eye-line mr-2"></i>
                  조회수 {selectedVideo.views}
                </span>
                <span className="flex items-center">
                  <i className="ri-heart-line mr-2"></i>
                  좋아요 {selectedVideo.likes}
                </span>
                {!selectedVideo.videoUrl && selectedVideo.articleUrl && (
                  <a
                    href={selectedVideo.articleUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-auto flex items-center space-x-2 text-red-600 hover:text-red-700 transition-colors duration-200"
                  >
                    <i className="ri-external-link-line"></i>
                    <span>원문 보기</span>
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
