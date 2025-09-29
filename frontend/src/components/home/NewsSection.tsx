'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Card from '../base/Card';

export default function NewsSection() {
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [currentBreakingIndex, setCurrentBreakingIndex] = useState(0);
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<any>(null);

  const videoNews = [
    {
      id: 1,
      title: '서울 아파트 화재 현장, 신속한 대응으로 인명피해 방지',
      thumbnail: 'https://readdy.ai/api/search-image?query=Korean%20firefighters%20responding%20to%20apartment%20fire%20emergency%2C%20news%20broadcast%20style%2C%20professional%20coverage%20with%20fire%20trucks%20and%20emergency%20response%2C%20dramatic%20but%20safe%20scene%2C%20TV%20news%20quality&width=400&height=250&seq=news1&orientation=landscape',
      duration: '2:34',
      time: '30분 전',
      videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
      category: '화재',
      summary: '아파트 화재 현장에서 신속한 구조와 진압으로 인명피해를 최소화했습니다.',
      views: 1024,
      likes: 256,
      videoId: 'dQw4w9WgXcQ'
    },
    {
      id: 2,
      title: '부산 고층빌딩 화재 진압 작업 현장 중계',
      thumbnail: 'https://readdy.ai/api/search-image?query=Korean%20firefighters%20battling%20high-rise%20building%20fire%20in%20Busan%2C%20aerial%20ladder%20trucks%20in%20action%2C%20news%20footage%20style%2C%20professional%20emergency%20response%20scene%2C%20dramatic%20urban%20firefighting&width=400&height=250&seq=news2&orientation=landscape',
      duration: '3:12',
      time: '1시간 전',
      videoUrl: 'https://www.youtube.com/embed/ScMzIvxBSi4',
      category: '화재',
      summary: '부산 고층빌딩 화재 진압 현장을 실시간 중계합니다.',
      views: 2048,
      likes: 512,
      videoId: 'ScMzIvxBSi4'
    },
    {
      id: 3,
      title: '대구 공장 폭발사고 구조작업 진행상황',
      thumbnail: 'https://readdy.ai/api/search-image?query=Korean%20emergency%20rescue%20team%20at%20industrial%20accident%20site%20in%20Daegu%2C%20professional%20rescue%20operation%2C%20news%20coverage%20style%2C%20safety%20equipment%20and%20emergency%20vehicles%2C%20controlled%20industrial%20scene&width=400&height=250&seq=news3&orientation=landscape',
      duration: '4:21',
      time: '2시간 전',
      videoUrl: 'https://www.youtube.com/embed/kJQP7kiw5Fk',
      category: '폭발',
      summary: '대구 공장 폭발 사고 현장의 구조 작업 상황을 전합니다.',
      views: 3072,
      likes: 768,
      videoId: 'kJQP7kiw5Fk'
    },
    {
      id: 4,
      title: '인천 화학공장 화재 진압 완료, 대형 사고 예방',
      thumbnail: 'https://readdy.ai/api/search-image?query=Korean%20firefighters%20at%20chemical%20factory%20fire%20scene%20in%20Incheon%2C%20successful%20fire%20suppression%20operation%2C%20news%20coverage%20style%2C%20industrial%20emergency%20response%2C%20professional%20safety%20equipment&width=400&height=250&seq=news4&orientation=landscape',
      duration: '2:45',
      time: '3시간 전',
      videoUrl: 'https://www.youtube.com/embed/fJ9rUzIMcZQ',
      category: '화학',
      summary: '인천 화학공장 화재를 신속히 진압하고 대형 사고를 예방했습니다.',
      views: 4096,
      likes: 1024,
      videoId: 'fJ9rUzIMcZQ'
    },
    {
      id: 5,
      title: '광주 지하상가 화재 대피 훈련 성공적 완료',
      thumbnail: 'https://readdy.ai/api/search-image?query=Korean%20fire%20drill%20evacuation%20at%20underground%20shopping%20center%20in%20Gwangju%2C%20organized%20emergency%20training%2C%20news%20documentation%20style%2C%20people%20safely%20evacuating%2C%20professional%20fire%20safety%20exercise&width=400&height=250&seq=news5&orientation=landscape',
      duration: '3:56',
      time: '4시간 전',
      videoUrl: 'https://www.youtube.com/embed/9bZkp7q19f0',
      category: '훈련',
      summary: '광주 지하상가에서 진행된 화재 대피 훈련이 성공적으로 마무리되었습니다.',
      views: 5120,
      likes: 1280,
      videoId: '9bZkp7q19f0'
    },
    {
      id: 6,
      title: '울산 석유화학단지 안전점검 실시',
      thumbnail: 'https://readdy.ai/api/search-image?query=Korean%20firefighters%20conducting%20safety%20inspection%20at%20petrochemical%20complex%20in%20Ulsan%2C%20professional%20safety%20check%20operation%2C%20news%20coverage%20style%2C%20industrial%20safety%20equipment%20and%20procedures&width=400&height=250&seq=news6&orientation=landscape',
      duration: '3:28',
      time: '5시간 전',
      videoUrl: 'https://www.youtube.com/embed/L_jWHffIx5E',
      category: '안전',
      summary: '울산 석유화학단지의 정기 안전점검이 실시되었습니다.',
      views: 1536,
      likes: 384,
      videoId: 'L_jWHffIx5E'
    }
  ];

  const breakingNews = [
    { 
      title: '[속보] 인천 화학공장 화재 발생, 소방당국 진압 작업 중', 
      time: '5분 전', 
      isBreaking: true,
      link: 'https://news.example.com/breaking-incheon-chemical-fire'
    },
    { 
      title: '서울 강남구 지하철역 화재경보 오작동으로 판명', 
      time: '15분 전', 
      isBreaking: false,
      link: 'https://news.example.com/seoul-subway-false-alarm'
    },
    { 
      title: '부산 해운대 호텔 화재, 투숙객 전원 안전 대피 완료', 
      time: '25분 전', 
      isBreaking: false,
      link: 'https://news.example.com/busan-hotel-fire-evacuation'
    },
    { 
      title: '[긴급] 대전 대형마트 화재 발생, 소방차 15대 출동', 
      time: '35분 전', 
      isBreaking: true,
      link: 'https://news.example.com/daejeon-mart-fire-emergency'
    },
    { 
      title: '광주 아파트 가스폭발 사고, 부상자 3명 병원 이송', 
      time: '45분 전', 
      isBreaking: false,
      link: 'https://news.example.com/gwangju-gas-explosion'
    },
    { 
      title: '울산 석유화학단지 화재경보, 예방차원 대응팀 출동', 
      time: '1시간 전', 
      isBreaking: false,
      link: 'https://news.example.com/ulsan-petrochemical-alert'
    },
    { 
      title: '[속보] 전주 상가건물 화재 진압 완료, 인명피해 없어', 
      time: '1시간 10분 전', 
      isBreaking: true,
      link: 'https://news.example.com/jeonju-building-fire-complete'
    },
    { 
      title: '춘천 산불 감시 드론 운영 확대, 예방 활동 강화', 
      time: '1시간 30분 전', 
      isBreaking: false,
      link: 'https://news.example.com/chuncheon-drone-forest-fire'
    },
    { 
      title: '제주 공항 화재경보 시스템 점검 완료', 
      time: '2시간 전', 
      isBreaking: false,
      link: 'https://news.example.com/jeju-airport-fire-system'
    },
    { 
      title: '[긴급] 수원 공장 화재 발생, 소방당국 출동 중', 
      time: '2시간 15분 전', 
      isBreaking: true,
      link: 'https://news.example.com/suwon-factory-fire-emergency'
    },
    { 
      title: '포항 제철소 안전점검 실시, 화재 예방 강화', 
      time: '2시간 30분 전', 
      isBreaking: false,
      link: 'https://news.example.com/pohang-steel-safety-check'
    },
    { 
      title: '창원 공단 화재경보 해제, 오작동으로 판명', 
      time: '2시간 45분 전', 
      isBreaking: false,
      link: 'https://news.example.com/changwon-false-alarm'
    },
    { 
      title: '[속보] 안산 화학공장 폭발 위험 경보, 대피령 발령', 
      time: '3시간 전', 
      isBreaking: true,
      link: 'https://news.example.com/ansan-chemical-explosion-alert'
    },
    { 
      title: '성남 아파트 화재, 소방헬기 출동으로 신속 진압', 
      time: '3시간 15분 전', 
      isBreaking: false,
      link: 'https://news.example.com/seongnam-apartment-fire'
    },
    { 
      title: '천안 물류창고 화재 완진, 재산피해 최소화', 
      time: '3시간 30분 전', 
      isBreaking: false,
      link: 'https://news.example.com/cheonan-warehouse-fire'
    }
  ];

  // 비디오 뉴스 자동 회전 (10초마다)
  useEffect(() => {
    const videoTimer = setInterval(() => {
      setCurrentVideoIndex((prev) => (prev + 1) % videoNews.length);
    }, 10000);
    return () => clearInterval(videoTimer);
  }, [videoNews.length]);

  // 속보 뉴스 자동 회전 (10초마다)
  useEffect(() => {
    const breakingTimer = setInterval(() => {
      setCurrentBreakingIndex((prev) => (prev + 1) % breakingNews.length);
    }, 10000);
    return () => clearInterval(breakingTimer);
  }, [breakingNews.length]);

  // 현재 표시할 비디오 뉴스 4개
  const getVisibleVideoNews = () => {
    const visible = [];
    for (let i = 0; i < 4; i++) {
      visible.push(videoNews[(currentVideoIndex + i) % videoNews.length]);
    }
    return visible;
  };

  // 현재 표시할 속보 뉴스 8개
  const getVisibleBreakingNews = () => {
    const visible = [];
    for (let i = 0; i < 8; i++) {
      visible.push(breakingNews[(currentBreakingIndex + i) % breakingNews.length]);
    }
    return visible;
  };

  // 준비된 비디오 뉴스 목록
  const displayedVideoNews = getVisibleVideoNews();

  const handleVideoClick = (news: any) => {
    setSelectedVideo(news);
    setShowVideoModal(true);
  };

  const handleCloseModal = () => {
    setShowVideoModal(false);
    setSelectedVideo(null);
  };

  const handleBreakingNewsClick = (newsItem: any) => {
    // 새 탭에서 뉴스 링크 열기
    window.open(newsItem.link, '_blank', 'noopener,noreferrer');
  };

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
            <span className="text-sm text-gray-500">10초마다 업데이트</span>
          </div>
          
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
        </div>

        {/* 실시간 속보 - 가로로 길게 */}
        <div>
          <div className="flex items-center space-x-2 mb-8">
            <div className="w-3 h-3 bg-orange-500 rounded-full animate-pulse"></div>
            <h2 className="text-2xl font-bold text-gray-900">실시간 속보</h2>
            <span className="text-sm text-gray-500 ml-auto">10초마다 업데이트</span>
          </div>
          
          <Card>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {getVisibleBreakingNews().map((news, index) => (
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
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
