'use client';

import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DonationRankingPage() {
  const [activeTab, setActiveTab] = useState<'individual' | 'group' | 'company'>('individual');
  const [activeTimeRange, setActiveTimeRange] = useState<'monthly' | 'yearly'>('monthly');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;
  const router = useRouter();

  // 소방서별 커피 기부 현황 관련 상태 추가
  const [activeStatusFilter, setActiveStatusFilter] = useState<'all' | 'completed' | 'pending' | 'hold'>('all');
  const [searchFireStation, setSearchFireStation] = useState('');
  const [currentFireStationPage, setCurrentFireStationPage] = useState(1);
  const fireStationItemsPerPage = 15;
  
  // 새로운 필터 및 정렬 상태 추가
  const [sortField, setSortField] = useState<'date' | 'fireStation' | 'amount' | 'cups' | 'remainingCups'>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [dateFilter, setDateFilter] = useState<'all' | 'today' | 'week' | 'month'>('all');
  const [regionFilter, setRegionFilter] = useState<string>('all');

  // 비고 상세보기 모달 상태 추가
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [selectedFireStationItem, setSelectedFireStationItem] = useState<any>(null);

  // 로그인한 사용자 정보 (실제로는 context나 store에서 가져와야 함)
  const currentUser = {
    isLoggedIn: true,
    name: '홍길동',
    rank: 42,
    amount: 185000,
    cups: 62
  };

  // 소방서별 커피 기부 현황 데이터 추가 (남은 커피잔수 포함)
  const fireStationCoffeeStatus = [
    {
      id: 1,
      date: new Date(2024, 11, 15),
      fireStation: '서울강남소방서',
      region: '서울특별시',
      donationAmount: 45000,
      coffeeCups: 15,
      status: 'completed',
      deliveredCups: 15,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241215_001.pdf',
      deliveryDate: new Date(2024, 11, 16),
      totalAccumulatedCups: 85,
      remainingCupsForNext: 15
    },
    {
      id: 2,
      date: new Date(2024, 11, 14),
      fireStation: '부산해운대소방서',
      region: '부산광역시',
      donationAmount: 30000,
      coffeeCups: 10,
      status: 'pending',
      deliveredCups: 0,
      pendingCups: 10,
      note: '소방서 연락 대기중',
      evidence: '',
      deliveryDate: null,
      totalAccumulatedCups: 45,
      remainingCupsForNext: 55
    },
    {
      id: 3,
      date: new Date(2024, 11, 13),
      fireStation: '대구중부소방서',
      region: '대구광역시',
      donationAmount: 60000,
      coffeeCups: 20,
      status: 'completed',
      deliveredCups: 20,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241213_002.pdf',
      deliveryDate: new Date(2024, 11, 14),
      totalAccumulatedCups: 120,
      remainingCupsForNext: 80
    },
    {
      id: 4,
      date: new Date(2024, 11, 12),
      fireStation: '인천계양소방서',
      region: '인천광역시',
      donationAmount: 15000,
      coffeeCups: 5,
      status: 'hold',
      deliveredCups: 0,
      pendingCups: 5,
      note: '배송 지연 (교통상황)',
      evidence: '',
      deliveryDate: null,
      totalAccumulatedCups: 25,
      remainingCupsForNext: 75
    },
    {
      id: 5,
      date: new Date(2024, 11, 11),
      fireStation: '광주서구소방서',
      region: '광주광역시',
      donationAmount: 90000,
      coffeeCups: 30,
      status: 'completed',
      deliveredCups: 30,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241211_003.pdf',
      deliveryDate: new Date(2024, 11, 12),
      totalAccumulatedCups: 95,
      remainingCupsForNext: 5
    },
    {
      id: 6,
      date: new Date(2024, 11, 10),
      fireStation: '대전유성소방서',
      region: '대전광역시',
      donationAmount: 75000,
      coffeeCups: 25,
      status: 'pending',
      deliveredCups: 0,
      pendingCups: 25,
      note: '커피 재고 확인중',
      evidence: '',
      deliveryDate: null,
      totalAccumulatedCups: 60,
      remainingCupsForNext: 40
    },
    {
      id: 7,
      date: new Date(2024, 11, 9),
      fireStation: '울산남구소방서',
      region: '울산광역시',
      donationAmount: 36000,
      coffeeCups: 12,
      status: 'completed',
      deliveredCups: 12,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241209_004.pdf',
      deliveryDate: new Date(2024, 11, 10),
      totalAccumulatedCups: 78,
      remainingCupsForNext: 22
    },
    {
      id: 8,
      date: new Date(2024, 11, 8),
      fireStation: '경기수원소방서',
      region: '경기도',
      donationAmount: 120000,
      coffeeCups: 40,
      status: 'hold',
      deliveredCups: 0,
      pendingCups: 40,
      note: '소방서 공사로 인한 접근 불가',
      evidence: '',
      deliveryDate: null,
      totalAccumulatedCups: 140,
      remainingCupsForNext: 60
    },
    {
      id: 9,
      date: new Date(2024, 11, 7),
      fireStation: '강원춘천소방서',
      region: '강원특별자치도',
      donationAmount: 54000,
      coffeeCups: 18,
      status: 'completed',
      deliveredCups: 18,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241207_005.pdf',
      deliveryDate: new Date(2024, 11, 8),
      totalAccumulatedCups: 33,
      remainingCupsForNext: 67
    },
    {
      id: 10,
      date: new Date(2024, 11, 6),
      fireStation: '충북청주소방서',
      region: '충청북도',
      donationAmount: 42000,
      coffeeCups: 14,
      status: 'pending',
      deliveredCups: 0,
      pendingCups: 14,
      note: '담당자 부재로 연락 대기',
      evidence: '',
      deliveryDate: null,
      totalAccumulatedCups: 52,
      remainingCupsForNext: 48
    },
    {
      id: 11,
      date: new Date(2024, 11, 5),
      fireStation: '충남천안소방서',
      region: '충청남도',
      donationAmount: 66000,
      coffeeCups: 22,
      status: 'completed',
      deliveredCups: 22,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241205_006.pdf',
      deliveryDate: new Date(2024, 11, 6),
      totalAccumulatedCups: 88,
      remainingCupsForNext: 12
    },
    {
      id: 12,
      date: new Date(2024, 11, 4),
      fireStation: '전북전주소방서',
      region: '전라북도',
      donationAmount: 48000,
      coffeeCups: 16,
      status: 'hold',
      deliveredCups: 0,
      pendingCups: 16,
      note: '커피머신 고장으로 수리 대기',
      evidence: '',
      deliveryDate: null,
      totalAccumulatedCups: 42,
      remainingCupsForNext: 58
    },
    {
      id: 13,
      date: new Date(2024, 11, 3),
      fireStation: '전남목포소방서',
      region: '전라남도',
      donationAmount: 72000,
      coffeeCups: 24,
      status: 'completed',
      deliveredCups: 24,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241203_007.pdf',
      deliveryDate: new Date(2024, 11, 4),
      totalAccumulatedCups: 96,
      remainingCupsForNext: 4
    },
    {
      id: 14,
      date: new Date(2024, 11, 2),
      fireStation: '경북포항소방서',
      region: '경상북도',
      donationAmount: 39000,
      coffeeCups: 13,
      status: 'pending',
      deliveredCups: 0,
      pendingCups: 13,
      note: '날씨로 인한 배송 지연',
      evidence: '',
      deliveryDate: null,
      totalAccumulatedCups: 67,
      remainingCupsForNext: 33
    },
    {
      id: 15,
      date: new Date(2024, 11, 1),
      fireStation: '경남창원소방서',
      region: '경상남도',
      donationAmount: 84000,
      coffeeCups: 28,
      status: 'completed',
      deliveredCups: 28,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241201_008.pdf',
      deliveryDate: new Date(2024, 11, 2),
      totalAccumulatedCups: 155,
      remainingCupsForNext: 45
    },
    {
      id: 16,
      date: new Date(2024, 10, 30),
      fireStation: '제주제주소방서',
      region: '제주특별자치도',
      donationAmount: 57000,
      coffeeCups: 19,
      status: 'completed',
      deliveredCups: 19,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241130_009.pdf',
      deliveryDate: new Date(2024, 11, 1),
      totalAccumulatedCups: 74,
      remainingCupsForNext: 26
    },
    {
      id: 17,
      date: new Date(2024, 10, 29),
      fireStation: '서울마포소방서',
      region: '서울특별시',
      donationAmount: 63000,
      coffeeCups: 21,
      status: 'pending',
      deliveredCups: 0,
      pendingCups: 21,
      note: '소방서 훈련으로 인한 일정 조정',
      evidence: '',
      deliveryDate: null,
      totalAccumulatedCups: 89,
      remainingCupsForNext: 11
    },
    {
      id: 18,
      date: new Date(2024, 10, 28),
      fireStation: '부산중부소방서',
      region: '부산광역시',
      donationAmount: 51000,
      coffeeCups: 17,
      status: 'hold',
      deliveredCups: 0,
      pendingCups: 17,
      note: '커피 품질 검수 진행중',
      evidence: '',
      deliveryDate: null,
      totalAccumulatedCups: 38,
      remainingCupsForNext: 62
    },
    {
      id: 19,
      date: new Date(2024, 10, 27),
      fireStation: '대구수성소방서',
      region: '대구광역시',
      donationAmount: 78000,
      coffeeCups: 26,
      status: 'completed',
      deliveredCups: 26,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241127_010.pdf',
      deliveryDate: new Date(2024, 10, 28),
      totalAccumulatedCups: 110,
      remainingCupsForNext: 90
    },
    {
      id: 20,
      date: new Date(2024, 10, 26),
      fireStation: '인천남동소방서',
      region: '인천광역시',
      donationAmount: 45000,
      coffeeCups: 15,
      status: 'completed',
      deliveredCups: 15,
      pendingCups: 0,
      note: '',
      evidence: 'receipt_20241126_011.pdf',
      deliveryDate: new Date(2024, 10, 27),
      totalAccumulatedCups: 71,
      remainingCupsForNext: 29
    },
    // 같은 소방서 중복 데이터 예시 추가
    {
      id: 21,
      date: new Date(2024, 10, 20),
      fireStation: '서울강남소방서',
      region: '서울특별시',
      donationAmount: 30000,
      coffeeCups: 10,
      status: 'completed',
      deliveredCups: 10,
      pendingCups: 0,
      note: '2차 기부',
      evidence: 'receipt_20241120_012.pdf',
      deliveryDate: new Date(2024, 10, 21),
      totalAccumulatedCups: 70,
      remainingCupsForNext: 30
    },
    {
      id: 22,
      date: new Date(2024, 10, 15),
      fireStation: '부산해운대소방서',
      region: '부산광역시',
      donationAmount: 21000,
      coffeeCups: 7,
      status: 'completed',
      deliveredCups: 7,
      pendingCups: 0,
      note: '추가 기부',
      evidence: 'receipt_20241115_013.pdf',
      deliveryDate: new Date(2024, 10, 16),
      totalAccumulatedCups: 35,
      remainingCupsForNext: 65
    }
  ];

  // 지역 목록 추출
  const regions = [...new Set(fireStationCoffeeStatus.map(item => item.region))];

  // 날짜 필터링 함수
  const filterByDate = (item: any) => {
    const today = new Date();
    const itemDate = item.date;
    
    switch (dateFilter) {
      case 'today':
        return itemDate.toDateString() === today.toDateString();
      case 'week':
        const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
        return itemDate >= weekAgo;
      case 'month':
        const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
        return itemDate >= monthAgo;
      default:
        return true;
    }
  };

  // 소방서별 커피 현황 필터링 및 정렬
  const getFilteredFireStationStatus = () => {
    let filtered = fireStationCoffeeStatus;
    
    // 상태별 필터링
    if (activeStatusFilter !== 'all') {
      filtered = filtered.filter(item => item.status === activeStatusFilter);
    }
    
    // 날짜별 필터링
    filtered = filtered.filter(filterByDate);
    
    // 지역별 필터링
    if (regionFilter !== 'all') {
      filtered = filtered.filter(item => item.region === regionFilter);
    }
    
    // 소방서명 검색
    if (searchFireStation) {
      filtered = filtered.filter(item =>
        item.fireStation.toLowerCase().includes(searchFireStation.toLowerCase()) ||
        item.region.toLowerCase().includes(searchFireStation.toLowerCase())
      );
    }
    
    // 정렬
    filtered.sort((a, b) => {
      let aValue, bValue;
      
      switch (sortField) {
        case 'date':
          aValue = a.date.getTime();
          bValue = b.date.getTime();
          break;
        case 'fireStation':
          aValue = a.fireStation;
          bValue = b.fireStation;
          break;
        case 'amount':
          aValue = a.donationAmount;
          bValue = b.donationAmount;
          break;
        case 'cups':
          aValue = a.coffeeCups;
          bValue = b.coffeeCups;
          break;
        case 'remainingCups':
          aValue = a.remainingCupsForNext;
          bValue = b.remainingCupsForNext;
          break;
        default:
          aValue = a.date.getTime();
          bValue = b.date.getTime();
      }
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
      }
      
      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
    });
    
    return filtered;
  };

  // 정렬 핸들러
  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // 정렬 아이콘 표시
  const getSortIcon = (field: typeof sortField) => {
    if (sortField !== field) return 'ri-arrow-up-down-line text-gray-400';
    return sortDirection === 'asc' ? 'ri-arrow-up-line text-blue-600' : 'ri-arrow-down-line text-blue-600';
  };

  // 소방서별 커피 현황 통계
  const getFireStationStats = () => {
    const totalCups = fireStationCoffeeStatus.reduce((sum, item) => sum + item.coffeeCups, 0);
    const deliveredCups = fireStationCoffeeStatus.reduce((sum, item) => sum + item.deliveredCups, 0);
    const pendingCups = fireStationCoffeeStatus.reduce((sum, item) => sum + item.pendingCups, 0);
    const completedCount = fireStationCoffeeStatus.filter(item => item.status === 'completed').length;
    const pendingCount = fireStationCoffeeStatus.filter(item => item.status === 'pending').length;
    const holdCount = fireStationCoffeeStatus.filter(item => item.status === 'hold').length;
    
    return {
      totalCups,
      deliveredCups,
      pendingCups,
      completedCount,
      pendingCount,
      holdCount,
      deliveryRate: totalCups > 0 ? Math.round((deliveredCups / totalCups) * 100) : 0
    };
  };

  // 상태별 배지 색상
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full font-medium">지급완료</span>;
      case 'pending':
        return <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full font-medium">지급대기</span>;
      case 'hold':
        return <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full font-medium">지급보류</span>;
      default:
        return <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full font-medium">알 수 없음</span>;
    }
  };

  // 증빙자료 다운로드
  const downloadEvidence = (filename: string) => {
    if (filename) {
      alert(`증빙자료 다운로드: ${filename}`);
    }
  };

  // 비고 보기 버튼 클릭 핸들러 추가
  const handleViewNote = (item: any) => {
    setSelectedFireStationItem(item);
    setShowNoteModal(true);
  };

  const individualRankings = Array.from({ length: 100 }, (_, i) => ({
    rank: i + 1,
    name: `기부자${String(i + 1).padStart(3, '0')}`,
    amount: Math.floor(Math.random() * 2000000) + 50000,
    cups: Math.floor((Math.floor(Math.random() * 2000000) + 50000) / 3000),
    badge: i < 3 ? ['🥇', '🥈', '🥉'][i] : '',
    level: i < 5 ? 'VIP' : i < 15 ? 'Gold' : i < 35 ? 'Silver' : 'Bronze'
  })).sort((a, b) => b.amount - a.amount).map((item, index) => ({ ...item, rank: index + 1 }));

  const groupRankings = Array.from({ length: 100 }, (_, i) => ({
    rank: i + 1,
    name: `단체${String(i + 1).padStart(3, '0')}`,
    amount: Math.floor(Math.random() * 5000000) + 100000,
    cups: Math.floor((Math.floor(Math.random() * 5000000) + 100000) / 3000),
    badge: i < 3 ? ['🥇', '🥈', '🥉'][i] : '',
    level: i < 5 ? 'VIP' : i < 15 ? 'Gold' : i < 35 ? 'Silver' : 'Bronze'
  })).sort((a, b) => b.amount - a.amount).map((item, index) => ({ ...item, rank: index + 1 }));

  const companyRankings = Array.from({ length: 100 }, (_, i) => ({
    rank: i + 1,
    name: `${i % 2 === 0 ? '기업' : '기관'}${String(i + 1).padStart(3, '0')}`,
    amount: Math.floor(Math.random() * 8000000) + 300000,
    cups: Math.floor((Math.floor(Math.random() * 8000000) + 300000) / 3000),
    badge: i < 3 ? ['🥇', '🥈', '🥉'][i] : '',
    level: i < 5 ? 'VIP' : i < 15 ? 'Gold' : i < 35 ? 'Silver' : 'Bronze'
  })).sort((a, b) => b.amount - a.amount).map((item, index) => ({ ...item, rank: index + 1 }));

  const monthlyStats = [
    { month: '2024년 1월', totalAmount: 15420000, totalCups: 5140, totalDonors: 1230 },
    { month: '2024년 2월', totalAmount: 18350000, totalCups: 6117, totalDonors: 1456 },
    { month: '2024년 3월', totalAmount: 22180000, totalCups: 7393, totalDonors: 1789 },
    { month: '2024년 4월', totalAmount: 19875000, totalCups: 6625, totalDonors: 1623 },
    { month: '2024년 5월', totalAmount: 24690000, totalCups: 8230, totalDonors: 2010 },
    { month: '2024년 6월', totalAmount: 28450000, totalCups: 9483, totalDonors: 2287 },
    { month: '2024년 7월', totalAmount: 31240000, totalCups: 10413, totalDonors: 2498 },
    { month: '2024년 8월', totalAmount: 29870000, totalCups: 9957, totalDonors: 2356 },
    { month: '2024년 9월', totalAmount: 33120000, totalCups: 11040, totalDonors: 2645 },
    { month: '2024년 10월', totalAmount: 36580000, totalCups: 12193, totalDonors: 2834 },
    { month: '2024년 11월', totalAmount: 42350000, totalCups: 14117, totalDonors: 3201 },
    { month: '2024년 12월', totalAmount: 48920000, totalCups: 16307, totalDonors: 3687 }
  ];

  const yearlyStats = [
    { year: '2022년', totalAmount: 180500000, totalCups: 60167, totalDonors: 15420 },
    { year: '2023년', totalAmount: 285600000, totalCups: 95200, totalDonors: 24680 },
    { year: '2024년', totalAmount: 330540000, totalCups: 110180, totalDonors: 28456 }
  ];

  // 실시간 기부 현황
  const recentDonations = [
    { time: '방금', donor: '김**', amount: 15000, cups: 5, region: '서울' },
    { time: '1분 전', donor: '이**', amount: 30000, cups: 10, region: '부산' },
    { time: '2분 전', donor: '박**', amount: 6000, cups: 2, region: '대구' },
    { time: '3분 전', donor: '정**', amount: 45000, cups: 15, region: '인천' },
    { time: '4분 전', donor: '한**', amount: 9000, cups: 3, region: '광주' },
    { time: '5분 전', donor: '송**', amount: 60000, cups: 20, region: '대전' },
    { time: '6분 전', donor: '윤**', amount: 12000, cups: 4, region: '울산' },
    { time: '7분 전', donor: '장**', amount: 18000, cups: 6, region: '세종' }
  ];

  const getCurrentRankings = () => {
    switch (activeTab) {
      case 'individual':
        return individualRankings;
      case 'group':
        return groupRankings;
      case 'company':
        return companyRankings;
      default:
        return individualRankings;
    }
  };

  const getTabTitle = () => {
    switch (activeTab) {
      case 'individual':
        return '기부자명';
      case 'group':
        return '단체명';
      case 'company':
        return '기업·기관명';
      default:
        return '기부자명';
    }
  };

  const getLevelBadgeColor = (level: string) => {
    switch (level) {
      case 'VIP':
        return 'bg-purple-100 text-purple-800';
      case 'Gold':
        return 'bg-yellow-100 text-yellow-800';
      case 'Silver':
        return 'bg-gray-100 text-gray-800';
      case 'Bronze':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const handleDonateClick = () => {
    router.push('/donations');
  };

  const currentRankings = getCurrentRankings();
  const totalPages = Math.ceil(currentRankings.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = currentRankings.slice(startIndex, endIndex);

  const getCurrentStats = () => {
    return activeTimeRange === 'monthly' ? monthlyStats : yearlyStats;
  };

  const currentStats = getCurrentStats();
  const totalStatsAmount = currentStats.reduce((sum, stat) => sum + (stat.totalAmount || 0), 0);
  const totalStatsCups = currentStats.reduce((sum, stat) => sum + (stat.totalCups || 0), 0);
  const totalStatsDonors = activeTimeRange === 'yearly' ? yearlyStats[yearlyStats.length - 1].totalDonors : monthlyStats[monthlyStats.length - 1].totalDonors;

  // 소방서별 커피 현황 페이지네이션
  const filteredFireStationStatus = getFilteredFireStationStatus();
  const fireStationTotalPages = Math.ceil(filteredFireStationStatus.length / fireStationItemsPerPage);
  const fireStationStartIndex = (currentFireStationPage - 1) * fireStationItemsPerPage;
  const fireStationEndIndex = fireStationStartIndex + fireStationItemsPerPage;
  const currentFireStationItems = filteredFireStationStatus.slice(fireStationStartIndex, fireStationEndIndex);

  const fireStationStats = getFireStationStats();

  return (
    <div className="bg-gray-50">
      {/* 히어로 섹션 */}
      <section 
        className="relative h-[40vh] flex items-center justify-center bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.4)), url('https://readdy.ai/api/search-image?query=Trophy%20and%20awards%20ceremony%20for%20firefighter%20supporters%2C%20golden%20trophies%20with%20coffee%20theme%2C%20celebration%20of%20generosity%2C%20warm%20lighting%2C%20professional%20photography%2C%20red%20and%20gold%20color%20scheme%2C%20recognition%20ceremony%20atmosphere%2C%20inspiring%20and%20prestigious&width=1920&height=720&seq=donation-ranking-hero&orientation=landscape')`
        }}
      >
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-white">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            기부 랭킹 &amp; 기부현황
          </h1>
          <p className="text-xl text-gray-200">
            소방관들을 위한 따뜻한 마음을 나눠주신 분들을 소개합니다
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        
        {/* 기부 대시보드 */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">기부 대시보드</h2>
          
          {/* 첫 번째 줄: 총 기부금액, 총 기부된 커피, 지원한 소방서 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <Card className="p-6 text-center bg-gradient-to-br from-green-50 to-green-100">
              <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-money-dollar-circle-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-green-600 mb-2">
                2,450,000,000원
              </div>
              <div className="text-gray-600">총 기부금액</div>
            </Card>
            <Card className="p-6 text-center bg-gradient-to-br from-orange-50 to-orange-100">
              <div className="w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-cup-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-orange-600 mb-2">
                127,543잔
              </div>
              <div className="text-gray-600">총 기부된 커피</div>
            </Card>
            <Card className="p-6 text-center bg-gradient-to-br from-red-50 to-red-100">
              <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-building-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-red-600 mb-2">
                342개
              </div>
              <div className="text-gray-600">지원한 소방서</div>
            </Card>
          </div>

          {/* 두 번째 줄: 참여한 시민, 참여한 단체, 참여한 기관 및 기업 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card className="p-6 text-center bg-gradient-to-br from-blue-50 to-blue-100">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-user-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-blue-600 mb-2">
                28,956명
              </div>
              <div className="text-gray-600">참여한 시민</div>
            </Card>
            <Card className="p-6 text-center bg-gradient-to-br from-purple-50 to-purple-100">
              <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-group-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-purple-600 mb-2">
                1,847개
              </div>
              <div className="text-gray-600">참여한 단체</div>
            </Card>
            <Card className="p-6 text-center bg-gradient-to-br from-indigo-50 to-indigo-100">
              <div className="w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-building-2-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-indigo-600 mb-2">
                423개
              </div>
              <div className="text-gray-600">참여한 기관 및 기업</div>
            </Card>
          </div>

          {/* 대시보드 하단 - 실시간 기부와 차트 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* 실시간 기부 현황 */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900 flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                  실시간 기부 현황
                </h3>
                <span className="text-sm text-gray-500">자동 업데이트</span>
              </div>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {recentDonations.map((donation, index) => (
                  <div key={index} className="flex justify-between items-center p-3 border-l-4 border-red-500 bg-red-50 rounded">
                    <div>
                      <div className="font-medium text-gray-900">{donation.donor}</div>
                      <div className="text-sm text-gray-600">{donation.time} | {donation.region}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-red-600">{donation.amount.toLocaleString()}원</div>
                      <div className="text-sm text-gray-600 flex items-center justify-end">
                        <i className="ri-cup-fill text-orange-500 mr-1"></i>
                        {donation.cups}잔
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* 기간별 트렌드 차트 (간단한 바 차트) */}
            <Card className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900">기부 트렌드</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setActiveTimeRange('monthly')}
                    className={`px-3 py-1 text-sm rounded-full transition-all duration-200 ${
                      activeTimeRange === 'monthly'
                        ? 'bg-red-600 text-white'
                        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                    }`}
                  >
                    월별
                  </button>
                  <button
                    onClick={() => setActiveTimeRange('yearly')}
                    className={`px-3 py-1 text-sm rounded-full transition-all duration-200 ${
                      activeTimeRange === 'yearly'
                        ? 'bg-red-600 text-white'
                        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                    }`}
                  >
                    연별
                  </button>
                </div>
              </div>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {activeTimeRange === 'monthly' 
                  ? monthlyStats.slice(-6).reverse().map((stat, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 w-20">{stat.month.replace('2024년 ', '')}</span>
                        <div className="flex-1 mx-4">
                          <div className="bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-gradient-to-r from-red-500 to-orange-500 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${(stat.totalAmount / 50000000) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                        <span className="text-sm font-medium text-red-600">
                          {(stat.totalAmount / 1000000).toFixed(0)}M원
                        </span>
                      </div>
                    ))
                  : yearlyStats.map((stat, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 w-20">{stat.year}</span>
                        <div className="flex-1 mx-4">
                          <div className="bg-gray-200 rounded-full h-3">
                            <div 
                              className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-colors duration-500"
                              style={{ width: `${(stat.totalAmount / 400000000) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                        <span className="text-sm font-medium text-blue-600">
                          {(stat.totalAmount / 1000000).toFixed(0)}M원
                        </span>
                      </div>
                    ))
                }
              </div>
            </Card>
          </div>
        </div>

        {/* 소방서별 커피 기부 현황 섹션 추가 */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">소방서별 커피 기부 현황</h2>
          
          {/* 커피 기부 현황 통계 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="p-6 text-center bg-gradient-to-br from-orange-50 to-orange-100">
              <div className="w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-cup-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-orange-600 mb-2">
                {fireStationStats.totalCups}잔
              </div>
              <div className="text-gray-600">총 기부 커피</div>
            </Card>
            <Card className="p-6 text-center bg-gradient-to-br from-green-50 to-green-100">
              <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-check-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-green-600 mb-2">
                {fireStationStats.deliveredCups}잔
              </div>
              <div className="text-gray-600">지급 완료</div>
            </Card>
            <Card className="p-6 text-center bg-gradient-to-br from-yellow-50 to-yellow-100">
              <div className="w-12 h-12 bg-yellow-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-time-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-yellow-600 mb-2">
                {fireStationStats.pendingCups}잔
              </div>
              <div className="text-gray-600">지급 대기</div>
            </Card>
            <Card className="p-6 text-center bg-gradient-to-br from-blue-50 to-blue-100">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-percent-fill text-white text-xl"></i>
              </div>
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {fireStationStats.deliveryRate}%
              </div>
              <div className="text-gray-600">지급률</div>
            </Card>
          </div>

          {/* 필터 및 검색 - 개선된 버전 */}
          <div className="mb-6 space-y-4">
            {/* 첫 번째 줄: 상태, 날짜, 지역 필터 */}
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">상태:</span>
                <select 
                  value={activeStatusFilter}
                  onChange={(e) => setActiveStatusFilter(e.target.value as any)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm pr-8"
                >
                  <option value="all">전체</option>
                  <option value="completed">지급완료</option>
                  <option value="pending">지급대기</option>
                  <option value="hold">지급보류</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">기간:</span>
                <select 
                  value={dateFilter}
                  onChange={(e) => setDateFilter(e.target.value as any)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm pr-8"
                >
                  <option value="all">전체</option>
                  <option value="today">오늘</option>
                  <option value="week">최근 1주일</option>
                  <option value="month">최근 1개월</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">지역:</span>
                <select 
                  value={regionFilter}
                  onChange={(e) => setRegionFilter(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm pr-8"
                >
                  <option value="all">전체 지역</option>
                  {regions.map(region => (
                    <option key={region} value={region}>{region}</option>
                  ))}
                </select>
              </div>
            </div>
            
            {/* 두 번째 줄: 검색 */}
            <div className="flex justify-between items-center">
              <div className="relative flex-1 max-w-md">
                <input
                  type="text"
                  value={searchFireStation}
                  onChange={(e) => setSearchFireStation(e.target.value)}
                  placeholder="소방서명 또는 지역명 검색"
                  className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
                />
                <i className="ri-search-line absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
              </div>
              
              <div className="text-sm text-gray-500">
                총 {getFilteredFireStationStatus().length}건
              </div>
            </div>
          </div>

          {/* 소방서별 커피 현황 테이블 - 개선된 버전 */}
          <Card className="overflow-hidden">
            <div className="p-4 bg-gray-50 border-b flex justify-between items-center">
              <h3 className="font-semibold text-gray-900">
                소방서별 커피 지급 현황 ({filteredFireStationStatus.length}건)
              </h3>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span>지급완료: {fireStationStats.completedCount}건</span>
                <span>지급대기: {fireStationStats.pendingCount}건</span>
                <span>지급보류: {fireStationStats.holdCount}건</span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th 
                      className="text-left py-4 px-4 font-semibold text-gray-900 cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => handleSort('date')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>일자</span>
                        <i className={getSortIcon('date')}></i>
                      </div>
                    </th>
                    <th 
                      className="text-left py-4 px-4 font-semibold text-gray-900 cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => handleSort('fireStation')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>소방서</span>
                        <i className={getSortIcon('fireStation')}></i>
                      </div>
                    </th>
                    <th className="text-left py-4 px-4 font-semibold text-gray-900">지역</th>
                    <th 
                      className="text-right py-4 px-4 font-semibold text-gray-900 cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => handleSort('amount')}
                    >
                      <div className="flex items-center justify-end space-x-1">
                        <span>기부금액</span>
                        <i className={getSortIcon('amount')}></i>
                      </div>
                    </th>
                    <th 
                      className="text-right py-4 px-4 font-semibold text-gray-900 cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => handleSort('cups')}
                    >
                      <div className="flex items-center justify-end space-x-1">
                        <span>커피잔수</span>
                        <i className={getSortIcon('cups')}></i>
                      </div>
                    </th>
                    <th 
                      className="text-right py-4 px-4 font-semibold text-gray-900 cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => handleSort('remainingCups')}
                    >
                      <div className="flex items-center justify-end space-x-1">
                        <span>남은 잔수</span>
                        <i className={getSortIcon('remainingCups')}></i>
                      </div>
                    </th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900">지급상태</th>
                    <th className="text-left py-4 px-4 font-semibold text-gray-900">보기</th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900">증빙자료</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {currentFireStationItems.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50 transition-colors duration-200">
                      <td className="py-4 px-4 text-sm text-gray-900">
                        {item.date.toLocaleDateString('ko-KR')}
                      </td>
                      <td className="py-4 px-4 text-sm font-medium text-gray-900">
                        <button
                          onClick={() => router.push(`/fire-station-detail/${encodeURIComponent(item.fireStation)}`)}
                          className="text-blue-600 hover:text-blue-800 hover:underline transition-colors duration-200"
                        >
                          {item.fireStation}
                        </button>
                      </td>
                      <td className="py-4 px-4 text-sm text-gray-600">
                        {item.region}
                      </td>
                      <td className="py-4 px-4 text-sm text-right font-medium text-gray-900">
                        {item.donationAmount.toLocaleString()}원
                      </td>
                      <td className="py-4 px-4 text-sm text-right">
                        <div className="flex items-center justify-end space-x-1">
                          <i className="ri-cup-fill text-orange-500"></i>
                          <span className="font-medium text-gray-900">{item.coffeeCups}잔</span>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-sm text-right">
                        <div className="flex items-center justify-end space-x-1">
                          <span className={`font-medium ${
                            item.remainingCupsForNext <= 10 
                              ? 'text-red-600' 
                              : item.remainingCupsForNext <= 30 
                                ? 'text-orange-600' 
                                : 'text-gray-900'
                          }`}>
                            {item.remainingCupsForNext}잔
                          </span>
                          <div className="text-xs text-gray-500">
                            ({item.totalAccumulatedCups}/100)
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        {getStatusBadge(item.status)}
                      </td>
                      <td className="py-4 px-4 text-sm text-center">
                        <button
                          onClick={() => handleViewNote(item)}
                          className="text-blue-600 hover:text-blue-800 font-medium transition-colors duration-200"
                        >
                          보기
                        </button>
                      </td>
                      <td className="py-4 px-4 text-center">
                        {item.evidence ? (
                          <button
                            onClick={() => downloadEvidence(item.evidence)}
                            className="text-blue-600 hover:text-blue-800 font-medium transition-colors duration-200"
                          >
                            <i className="ri-download-2-line mr-1"></i>
                            다운로드
                          </button>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 소방서별 현황 페이지네이션 */}
            <div className="p-4 bg-gray-50 border-t flex justify-between items-center">
              <div className="text-sm text-gray-700">
                전체 {filteredFireStationStatus.length}건 중 {fireStationStartIndex + 1} - {Math.min(fireStationEndIndex, filteredFireStationStatus.length)}건 표시
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentFireStationPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentFireStationPage === 1}
                  className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  <i className="ri-arrow-left-s-line"></i>
                </button>
                <div className="flex space-x-1">
                  {Array.from({ length: Math.min(fireStationTotalPages, 5) }, (_, i) => {
                    const page = Math.max(1, currentFireStationPage - 2) + i;
                    if (page > fireStationTotalPages) return null;
                    return (
                      <button
                        key={page}
                        onClick={() => setCurrentFireStationPage(page)}
                        className={`w-10 h-10 rounded-lg font-medium transition-colors duration-200 ${
                          page === currentFireStationPage
                            ? 'bg-red-600 text-white'
                            : 'bg-white text-gray-700 hover:bg-red-50 border border-gray-300'
                        }`}
                      >
                        {page}
                      </button>
                    );
                  })}
                </div>
                <button
                  onClick={() => setCurrentFireStationPage(prev => Math.min(prev + 1, fireStationTotalPages))}
                  disabled={currentFireStationPage === fireStationTotalPages}
                  className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  <i className="ri-arrow-right-s-line"></i>
                </button>
              </div>
            </div>
          </Card>
        </div>

        {/* 비고 상세보기 모달 추가 */}
        {showNoteModal && selectedFireStationItem && (
          <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900">소방서별 커피 기부 상세 정보</h3>
                <button
                  onClick={() => setShowNoteModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
                >
                  <i className="ri-close-line text-2xl"></i>
                </button>
              </div>

              <div className="space-y-6">
                {/* 기본 정보 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        기부 일자
                      </label>
                      <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                        {selectedFireStationItem.date.toLocaleDateString('ko-KR', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          weekday: 'short'
                        })}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        소방서명
                      </label>
                      <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900 font-medium">
                        {selectedFireStationItem.fireStation}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        지역
                      </label>
                      <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                        {selectedFireStationItem.region}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        기부 금액
                      </label>
                      <div className="px-4 py-3 bg-green-50 border border-green-300 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          {selectedFireStationItem.donationAmount.toLocaleString()}원
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        커피 잔수
                      </label>
                      <div className="px-4 py-3 bg-orange-50 border border-orange-300 rounded-lg">
                        <div className="flex items-center justify-center space-x-2">
                          <i className="ri-cup-fill text-orange-500 text-2xl"></i>
                          <span className="text-2xl font-bold text-orange-600">
                            {selectedFireStationItem.coffeeCups}잔
                          </span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        지급 상태
                      </label>
                      <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg">
                        {getStatusBadge(selectedFireStationItem.status)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 진행 현황 */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-blue-900 mb-4">
                    <i className="ri-progress-3-line mr-2"></i>
                    100잔 단위 전달 진행 현황
                  </h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-blue-700">현재 누적 커피잔수</span>
                      <span className="font-bold text-blue-900">
                        {selectedFireStationItem.totalAccumulatedCups}잔
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-blue-700">다음 전달까지 남은 잔수</span>
                      <span className={`font-bold ${
                        selectedFireStationItem.remainingCupsForNext <= 10 
                          ? 'text-red-600' 
                          : selectedFireStationItem.remainingCupsForNext <= 30 
                            ? 'text-orange-600' 
                            : 'text-blue-900'
                      }`}>
                        {selectedFireStationItem.remainingCupsForNext}잔
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 mt-4">
                      <div 
                        className="bg-gradient-to-r from-blue-400 to-blue-600 h-3 rounded-full transition-all duration-300"
                        style={{ 
                          width: `${(selectedFireStationItem.totalAccumulatedCups % 100)}%` 
                        }}
                      ></div>
                    </div>
                    <div className="text-center text-sm text-blue-600 mt-2">
                      진행률: {selectedFireStationItem.totalAccumulatedCups % 100}%
                    </div>
                  </div>
                </div>

                {/* 배송 정보 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      지급 완료 잔수
                    </label>
                    <div className="px-4 py-3 bg-green-50 border border-green-300 rounded-lg text-center">
                      <span className="text-xl font-bold text-green-600">
                        {selectedFireStationItem.deliveredCups}잔
                      </span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      지급 대기 잔수
                    </label>
                    <div className="px-4 py-3 bg-yellow-50 border border-yellow-300 rounded-lg text-center">
                      <span className="text-xl font-bold text-yellow-600">
                        {selectedFireStationItem.pendingCups}잔
                      </span>
                    </div>
                  </div>
                </div>

                {/* 배송일 정보 */}
                {selectedFireStationItem.deliveryDate && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      배송 완료일
                    </label>
                    <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                      {selectedFireStationItem.deliveryDate.toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        weekday: 'short'
                      })}
                    </div>
                  </div>
                )}

                {/* 비고 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    비고 및 특이사항
                  </label>
                  <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900 min-h-[80px]">
                    {selectedFireStationItem.note || '특이사항 없음'}
                  </div>
                </div>

                {/* 증빙자료 */}
                {selectedFireStationItem.evidence && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      증빙자료
                    </label>
                    <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <i className="ri-file-text-line text-blue-600"></i>
                          <span className="text-gray-900">{selectedFireStationItem.evidence}</span>
                        </div>
                        <button
                          onClick={() => downloadEvidence(selectedFireStationItem.evidence)}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors duration-200"
                        >
                          <i className="ri-download-2-line mr-2"></i>
                          다운로드
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* 소방서 상세 정보 링크 */}
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="font-medium text-orange-900 mb-1">
                        소방서 상세 정보
                      </h5>
                      <p className="text-sm text-orange-700">
                        {selectedFireStationItem.fireStation}의 전체 기부 현황과 상세 정보를 확인하세요
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setShowNoteModal(false);
                        router.push(`/fire-station-detail/${encodeURIComponent(selectedFireStationItem.fireStation)}`);
                      }}
                      className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors duration-200 whitespace-nowrap"
                    >
                      상세보기
                    </button>
                  </div>
                </div>
              </div>

              <div className="mt-8 flex justify-end space-x-3">
                <button
                  onClick={() => setShowNoteModal(false)}
                  className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors duration-200"
                >
                  닫기
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 내 랭킹 (로그인한 경우만 표시) */}
        {currentUser.isLoggedIn && activeTab === 'individual' && (
          <Card className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                  {currentUser.rank}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">내 랭킹</h3>
                  <p className="text-gray-600">{currentUser.name}님의 현재 순위</p>
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold text-blue-600 text-xl">
                  {currentUser.amount.toLocaleString()}원
                </div>
                <div className="text-gray-600 flex items-center justify-end">
                  <i className="ri-cup-fill text-orange-500 mr-1"></i>
                  {currentUser.cups}잔
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* 기간별 통계 */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">기부 현황 통계</h2>
            <div className="flex space-x-2">
              <button
                onClick={() => setActiveTimeRange('monthly')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  activeTimeRange === 'monthly'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                }`}
              >
                월별
              </button>
              <button
                onClick={() => setActiveTimeRange('yearly')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  activeTimeRange === 'yearly'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                }`}
              >
                연별
              </button>
            </div>
          </div>

          {/* 상세 통계 */}
          <Card className="p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              {activeTimeRange === 'monthly' ? '월별' : '연별'} 상세 현황
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {currentStats.reverse().map((stat, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-lg">
                  <div className="font-semibold text-gray-900 mb-2">
                    {(stat as any).month || (stat as any).year}
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">기부금액</span>
                      <span className="font-medium text-red-600">
                        {stat.totalAmount.toLocaleString()}원
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">커피</span>
                      <span className="font-medium text-orange-600">
                        {stat.totalCups.toLocaleString()}잔
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">기부자</span>
                      <span className="font-medium text-blue-600">
                        {stat.totalDonors.toLocaleString()}명
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* 탭 전환 버튼 */}
        <div className="flex justify-center mb-8">
          <div className="bg-white shadow-sm p-1 rounded-full border">
            <button
              onClick={() => {
                setActiveTab('individual');
                setCurrentPage(1);
              }}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'individual'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              개인 기부자
            </button>
            <button
              onClick={() => {
                setActiveTab('group');
                setCurrentPage(1);
              }}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'group'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              단체
            </button>
            <button
              onClick={() => {
                setActiveTab('company');
                setCurrentPage(1);
              }}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'company'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              기업·기관
            </button>
          </div>
        </div>

        {/* 랭킹 테이블 */}
        <Card className="overflow-hidden mb-8">
          <div className="p-4 bg-gray-50 border-b">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-gray-900">
                전체 {currentRankings.length}위 중 {startIndex + 1}-{Math.min(endIndex, currentRankings.length)}위
              </h3>
              <span className="text-sm text-gray-600">
                페이지 {currentPage} / {totalPages}
              </span>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-4 px-6 font-semibold text-gray-900">순위</th>
                  <th className="text-left py-4 px-6 font-semibold text-gray-900">
                    {getTabTitle()}
                  </th>
                  <th className="text-left py-4 px-6 font-semibold text-gray-900">등급</th>
                  <th className="text-right py-4 px-6 font-semibold text-gray-900">총 기부금액</th>
                  <th className="text-right py-4 px-6 font-semibold text-gray-900">커피잔수</th>
                </tr>
              </thead>
              <tbody>
                {currentItems.map((item) => (
                  <tr key={item.rank} className={`border-b border-gray-100 hover:bg-gray-50 transition-colors duration-200 ${
                    currentUser.isLoggedIn && activeTab === 'individual' && item.rank === currentUser.rank 
                      ? 'bg-blue-50 border-blue-200' 
                      : ''
                  }`}>
                    <td className="py-4 px-6">
                      <div className="flex items-center space-x-3">
                        <span className={`text-lg font-bold ${
                          item.rank <= 3 ? 'text-red-600' : 'text-gray-900'
                        }`}>
                          {item.rank}
                        </span>
                        {item.badge && <span className="text-xl">{item.badge}</span>}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <div className={`font-medium ${
                        currentUser.isLoggedIn && activeTab === 'individual' && item.rank === currentUser.rank 
                          ? 'text-blue-700' 
                          : 'text-gray-900'
                      }`}>
                        {currentUser.isLoggedIn && activeTab === 'individual' && item.rank === currentUser.rank 
                          ? currentUser.name + ' (나)' 
                          : item.name}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`px-3 py-1 text-xs rounded-full font-medium ${getLevelBadgeColor(item.level)}`}>
                        {item.level}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="font-semibold text-red-600">
                        {item.amount.toLocaleString()}원
                      </div>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end space-x-1">
                        <i className="ri-cup-fill text-orange-500"></i>
                        <span className="font-medium text-gray-900">{item.cups}잔</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* 페이지네이션 */}
        <div className="flex justify-center items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <i className="ri-arrow-left-line"></i>
          </Button>
          
          {/* 페이지 번호 표시 로직 개선 */}
          {(() => {
            const maxVisiblePages = 10;
            const startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
            const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
            const pages = [];
            
            for (let i = startPage; i <= endPage; i++) {
              pages.push(i);
            }
            
            return pages.map(page => (
              <Button
                key={page}
                variant={currentPage === page ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setCurrentPage(page)}
                className="w-10"
              >
                {page}
              </Button>
            ));
          })()}
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <i className="ri-arrow-right-line"></i>
          </Button>
        </div>

        {/* 기부 참여하기 */}
        <Card className="mt-12 p-8 text-center bg-gradient-to-r from-red-50 to-orange-50">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            여러분도 랭킹에 참여해보세요
          </h3>
          <p className="text-gray-600 mb-6">
            작은 기부가 소방관들에게 큰 힘이 되고, 여러분을 랭킹에 올려드립니다
          </p>
          <div className="flex justify-center">
            <Button 
              size="lg" 
              className="px-12 py-4"
              onClick={handleDonateClick}
            >
              <i className="ri-heart-fill mr-2"></i>
              지금 기부하기
            </Button>
          </div>
        </Card>
      </section>
    </div>
  );
}
