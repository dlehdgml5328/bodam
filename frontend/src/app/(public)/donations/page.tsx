'use client';

import Link from 'next/link';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { ChangeEvent, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { loadTossPayments } from '@tosspayments/payment-sdk';
import { apiRequest } from '@/lib/api';

export default function DonationsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [selectedAmount, setSelectedAmount] = useState(3000);
  const [customAmount, setCustomAmount] = useState('');
  const [donorName, setDonorName] = useState('');
  const [donorEmail, setDonorEmail] = useState('');
  // 연락처와 주민번호 필드 추가
  const [donorPhone, setDonorPhone] = useState('');
  const [donorIdNumber, setDonorIdNumber] = useState('');
  const [message, setMessage] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [useAccountInfo, setUseAccountInfo] = useState(false);
  const [needReceipt, setNeedReceipt] = useState(true);
  const [selectedFireStation, setSelectedFireStation] = useState('');
  const [searchFireStation, setSearchFireStation] = useState('');
  const [showFireStationList, setShowFireStationList] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showRegionModal, setShowRegionModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState('');
  const [locationPermission, setLocationPermission] = useState<'granted' | 'denied' | 'pending'>('pending');
  const [showPaymentMethodModal, setShowPaymentMethodModal] = useState(false);
  const [paymentData, setPaymentData] = useState<any>(null);
  const [showDonationLoginModal, setShowDonationLoginModal] = useState(false);
  
  // 기부 내역 조회 모달 상태 추가
  const [showDonationHistoryModal, setShowDonationHistoryModal] = useState(false);
  
  // 정기 기부 관련 상태 추가
  const [isRegularDonation, setIsRegularDonation] = useState(false);
  const [regularCycle, setRegularCycle] = useState<'monthly' | 'quarterly' | 'yearly'>('monthly');
  const [startDate, setStartDate] = useState('');
  
  // 비회원 이메일 인증 관련 상태
  const [guestEmailVerificationCode, setGuestEmailVerificationCode] = useState('');
  const [isGuestEmailVerificationSent, setIsGuestEmailVerificationSent] = useState(false);
  const [isGuestEmailVerified, setIsGuestEmailVerified] = useState(false);
  const [guestVerificationTimer, setGuestVerificationTimer] = useState(0);

  // 로그인 상태 감지
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userInfo, setUserInfo] = useState({
    name: '',
    email: '',
    phone: '',
    idNumber: ''
  });

  // 기부 방식 관련 상태 추가
  const [donationMode, setDonationMode] = useState<'single' | 'multiple'>('single');
  const [multipleType, setMultipleType] = useState<'split' | 'each' | 'custom'>('split');
  const [selectedFireStations, setSelectedFireStations] = useState<string[]>([]);
  const [customAmounts, setCustomAmounts] = useState<{[key: string]: number}>({});

  // 소방서 목록 상태 추가
  const [fireStations, setFireStations] = useState<Array<{
    id: string;
    name: string;
    region: string;
    district: string;
  }>>([]);
  const [isLoadingStations, setIsLoadingStations] = useState(true);

  // 기부 통계 상태 추가
  const [donationStats, setDonationStats] = useState({
    total_amount: 0,
    total_cups: 0,
    total_users: 0,
  });

  // 실시간 기부 현황 상태 추가
  const [recentDonations, setRecentDonations] = useState<Array<{
    donor: string;
    amount: number;
    cups: number;
    time: string;
  }>>([]);

  // 기존 코드 삽입 시작
  const amounts = [
    { value: 3000, cups: 1, label: '커피 1잔' },
    { value: 6000, cups: 2, label: '커피 2잔' },
    { value: 15000, cups: 5, label: '커피 5잔' },
    { value: 30000, cups: 10, label: '커피 10잔' },
    { value: 60000, cups: 20, label: '커피 20잔' },
    { value: 150000, cups: 50, label: '커피 50잔' },
  ];

  const regions = [
    '서울특별시',
    '부산광역시',
    '인천광역시',
    '대구광역시',
    '광주광역시',
    '대전광역시',
    '울산광역시',
    '세종특별자치시',
    '경기도',
    '강원도',
    '충청북도',
    '충청남도',
    '전라북도',
    '전라남도',
    '경상북도',
    '경상남도',
    '제주특별자치도',
  ];

  // 로그인 상태 및 사용자 정보 확인
  useEffect(() => {
    const checkLoginStatus = async () => {
      const loggedIn = localStorage.getItem('isLoggedIn') === 'true';
      setIsLoggedIn(loggedIn);

      if (loggedIn) {
        try {
          const userData = await apiRequest<{
            id: string;
            email: string;
            name: string;
            phone: string;
            id_number: string;
            role: string;
            created_at: string;
          }>('/auth/me');

          console.log('✅ API에서 받은 사용자 데이터:', userData);
          setUserInfo({
            name: userData.name || '',
            email: userData.email || '',
            phone: userData.phone || '',
            idNumber: userData.id_number || ''
          });
          setDonorName(userData.name || '');
          setDonorEmail(userData.email || '');
          setDonorPhone(userData.phone || '');
          setDonorIdNumber(userData.id_number || '');
          console.log('✅ State 업데이트 완료 - 전화번호:', userData.phone, '주민등록번호:', userData.id_number);
        } catch (error) {
          console.error('사용자 정보 로딩 실패:', error);
          // 401 에러 시 로그인 상태 초기화
          localStorage.removeItem('isLoggedIn');
          setIsLoggedIn(false);
        }
      }
    };

    checkLoginStatus();
  }, []);

  // 백엔드 API에서 소방서 목록 가져오기
  useEffect(() => {
    const fetchFireStations = async () => {
      try {
        setIsLoadingStations(true);
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        console.log('🔥 소방서 목록 API 호출:', `${apiBaseUrl}/stations?limit=1000`);
        const response = await fetch(`${apiBaseUrl}/stations?limit=1000`);
        if (!response.ok) {
          throw new Error('소방서 목록 조회 실패');
        }
        const data = await response.json();
        console.log('✅ 소방서 목록 로드 완료:', data.stations?.length, '개', data.stations);
        setFireStations(data.stations || []);
      } catch (error) {
        console.error('❌ 소방서 목록 로드 오류:', error);
        alert('소방서 목록을 불러오는데 실패했습니다. 페이지를 새로고침해주세요.');
      } finally {
        setIsLoadingStations(false);
      }
    };

    fetchFireStations();
  }, []);

  // 기부 통계 데이터 가져오기
  useEffect(() => {
    const fetchDonationStats = async () => {
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const response = await fetch(`${apiBaseUrl}/stats`);
        if (!response.ok) {
          throw new Error('통계 데이터 조회 실패');
        }
        const data = await response.json();
        setDonationStats({
          total_amount: Number(data.total_amount) || 0,
          total_cups: Number(data.total_cups) || 0,
          total_users: Number(data.total_users) || 0,
        });
      } catch (error) {
        console.error('통계 데이터 로드 오류:', error);
      }
    };

    fetchDonationStats();
  }, []);

  // 실시간 기부 현황 가져오기
  useEffect(() => {
    const fetchRecentDonations = async () => {
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const response = await fetch(`${apiBaseUrl}/donations/recent?limit=5`);
        if (!response.ok) {
          throw new Error('최근 기부 내역 조회 실패');
        }
        const data = await response.json();
        console.log('최근 기부 내역 API 응답:', data);
        const donations = data.donations || [];
        console.log('기부 내역 개수:', donations.length);

        // 데이터를 실시간 기부 현황 형식으로 변환
        const formatted = donations.map((d: any) => {
          const amount = Number(d.amount) || 0;
          const cups = Math.floor(amount / 3000);

          // 기부자 이름 마스킹 (익명이면 "익명", 아니면 첫 글자 + **)
          let donor = '익명';
          if (!d.is_anonymous && d.donor_name) {
            donor = d.donor_name.charAt(0) + '**';
          }

          // 시간 계산 (몇 분 전)
          const createdAt = new Date(d.created_at);
          const now = new Date();
          const diffMs = now.getTime() - createdAt.getTime();
          const diffMins = Math.floor(diffMs / 60000);

          let time = '';
          if (diffMins < 1) {
            time = '방금 전';
          } else if (diffMins < 60) {
            time = `${diffMins}분 전`;
          } else if (diffMins < 1440) {
            time = `${Math.floor(diffMins / 60)}시간 전`;
          } else {
            time = `${Math.floor(diffMins / 1440)}일 전`;
          }

          return {
            donor,
            amount,
            cups,
            time,
          };
        });

        console.log('포맷된 기부 내역:', formatted);
        setRecentDonations(formatted);
      } catch (error) {
        console.error('최근 기부 내역 로드 오류:', error);
      }
    };

    fetchRecentDonations();

    // 30초마다 새로고침
    const interval = setInterval(fetchRecentDonations, 30000);

    return () => clearInterval(interval);
  }, []);

  // 지역 이름 매핑 (프론트엔드 표시명 -> 백엔드 DB 값)
  const regionMapping: { [key: string]: string } = {
    '서울특별시': '서울',
    '부산광역시': '부산',
    '인천광역시': '인천',
    '대구광역시': '대구',
    '광주광역시': '광주',
    '대전광역시': '대전',
    '울산광역시': '울산',
    '세종특별자치시': '세종',
    '경기도': '경기',
    '강원도': '강원',
    '충청북도': '충청북',
    '충청남도': '충청남',
    '전라북도': '전북',
    '전라남도': '전라남',
    '경상북도': '경상북',
    '경상남도': '경상남',
    '제주특별자치도': '제주',
  };

  // 지역별 소방서 필터링
  const getFireStationsByRegion = (region: string) => {
    const dbRegion = regionMapping[region] || region;
    return fireStations.filter((station) => station.region === dbRegion);
  };

  // 내 위치 기반 추천 소방서 (실제 크롤링 데이터 기반)
  const getNearbyFireStations = () => {
    return [
      {
        id: 1,
        name: '서울중부소방서',
        region: '서울특별시',
        district: '중구',
        distance: '1.2km',
        todayDispatch: 8,
        todayFires: 3,
      },
      {
        id: 2,
        name: '서울강남소방서',
        region: '서울특별시',
        district: '강남구',
        distance: '2.8km',
        todayDispatch: 12,
        todayFires: 2,
      },
      {
        id: 3,
        name: '서울서초소방서',
        region: '서울특별시',
        district: '서초구',
        distance: '3.5km',
        todayDispatch: 6,
        todayFires: 1,
      },
      {
        id: 4,
        name: '서울용산소방서',
        region: '서울특별시',
        district: '용산구',
        distance: '4.1km',
        todayDispatch: 9,
        todayFires: 4,
      },
    ];
  };

  // 필터링된 소방서 목록 - 지역 선택 시 해당 지역 소방서만 표시
  const getFilteredFireStations = () => {
    let stations = fireStations;
    
    // 지역이 선택된 경우 해당 지역의 소방서만 필터링
    if (selectedRegion) {
      stations = getFireStationsByRegion(selectedRegion);
    }
    
    // 검색어가 있는 경우 추가 필터링
    if (searchFireStation) {
      stations = stations.filter(
        (station) =>
          station.name.toLowerCase().includes(searchFireStation.toLowerCase()) ||
          station.region.toLowerCase().includes(searchFireStation.toLowerCase()) ||
          station.district.toLowerCase().includes(searchFireStation.toLowerCase())
      );
    }
    
    return stations;
  };

  // 출동 건수에 따른 색상 반환 함수
  const getEmergencyColor = (count: number) => {
    if (count >= 15) return 'text-red-600 font-semibold';
    if (count >= 10) return 'text-orange-500 font-medium';
    if (count >= 5) return 'text-yellow-600 font-medium';
    return 'text-green-600';
  };

  // 화재 건수에 따른 색상 반환 함수
  const getFireColor = (count: number) => {
    if (count >= 8) return 'text-red-600 font-semibold';
    if (count >= 5) return 'text-orange-500 font-medium';
    if (count >= 2) return 'text-yellow-600 font-medium';
    return 'text-green-600';
  };

  // 정기 기부 옵션 배열
  const regularCycles = [
    { value: 'monthly', label: '매월', description: '매월 정기적으로 기부' },
    { value: 'quarterly', label: '분기별', description: '3개월마다 기부' },
    { value: 'yearly', label: '연간', description: '1년마다 기부' }
  ];


  // 비회원 이메일 인증 발송
  const sendGuestEmailVerification = async () => {
    if (!donorEmail.trim()) {
      alert('이메일을 입력해주세요.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(donorEmail)) {
      alert('올바른 이메일 형식을 입력해주세요.');
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setIsGuestEmailVerificationSent(true);
    setGuestVerificationTimer(300);
    alert('인증번호가 이메일로 발송되었습니다. 5분 내에 입력해주세요.');

    const timer = setInterval(() => {
      setGuestVerificationTimer(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          setIsGuestEmailVerificationSent(false);
          setGuestEmailVerificationCode('');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // 비회원 이메일 인증 확인
  const verifyGuestEmail = async () => {
    if (!guestEmailVerificationCode.trim()) {
      alert('인증번호를 입력해주세요.');
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 500));
    
    if (guestEmailVerificationCode === '123456') {
      setIsGuestEmailVerified(true);
      setGuestVerificationTimer(0);
      alert('이메일 인증이 완료되었습니다.');
    } else {
      alert('인증번호가 올바르지 않습니다. 다시 확인해주세요.');
    }
  };

  // 타이머 형식 변환
  const formatTimer = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // URL 매개변수에서 금액과 소방서 정보 가져오기
  useEffect(() => {
    const amountFromUrl = searchParams.get('amount');
    const stationFromUrl = searchParams.get('station');

    if (amountFromUrl) {
      const amount = parseInt(amountFromUrl, 10);
      if (Number.isFinite(amount) && amount > 0) {
        setSelectedAmount(amount);
        const predefinedAmounts = [3000, 6000, 15000, 30000, 60000, 150000];
        if (!predefinedAmounts.includes(amount)) {
          setCustomAmount(amount.toString());
        }
      }
    }

    if (stationFromUrl) {
      const decodedStation = decodeURIComponent(stationFromUrl);
      setSelectedFireStation(decodedStation);
      setSearchFireStation(decodedStation);
    }
  }, [searchParams]);

  // 로그인 상태 체크
  useEffect(() => {
    const checkLoginStatus = () => {
      const loginStatus = localStorage.getItem('isLoggedIn') === 'true';
      setIsLoggedIn(loginStatus);
    };

    checkLoginStatus();
    
    // 로그인 상태 변경 감지
    const interval = setInterval(checkLoginStatus, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const handleAmountSelect = (amount: number) => {
    setSelectedAmount(amount);
    setCustomAmount('');
  };

  const handleCustomAmountChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/[^0-9]/g, '');
    setCustomAmount(value);
    if (value) {
      setSelectedAmount(parseInt(value));
    }
  };

  const getCurrentAmount = () => {
    if (donationMode === 'multiple' && multipleType === 'custom') {
      return Object.values(customAmounts).reduce((sum, amount) => sum + (amount || 0), 0);
    }
    return customAmount ? parseInt(customAmount) : selectedAmount;
  };

  const getCupCount = (amount: number) => {
    return Math.floor(amount / 3000);
  };

  const handleUseAccountInfo = (checked: boolean) => {
    console.log('🔘 계정 정보 사용하기 클릭:', checked);
    console.log('📋 현재 userInfo:', userInfo);
    setUseAccountInfo(checked);
    if (checked && isLoggedIn) {
      setDonorName(userInfo.name);
      setDonorEmail(userInfo.email);
      setDonorPhone(userInfo.phone);
      setDonorIdNumber(userInfo.idNumber);
      console.log('✅ 폼 필드 업데이트:', {
        name: userInfo.name,
        email: userInfo.email,
        phone: userInfo.phone,
        idNumber: userInfo.idNumber
      });
    } else {
      setDonorName('');
      setDonorEmail('');
      setDonorPhone('');
      setDonorIdNumber('');
    }
  };

  const handleFireStationSelect = (stationId: string, stationName: string) => {
    setSelectedFireStation(stationId);
    setSearchFireStation(stationName);
    setShowFireStationList(false);
  };

  // 선택된 소방서 이름 가져오기
  const getSelectedFireStationName = () => {
    const station = fireStations.find(s => s.id === selectedFireStation);
    return station ? station.name : '';
  };

  const handleRegionSelect = (region: string) => {
    setSelectedRegion(region);
    setShowRegionModal(false);
    setSearchFireStation('');
    setShowFireStationList(true);
  };

  const handleLocationSelect = () => {
    setShowLocationModal(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocationPermission('granted');
          console.log('위치 정보:', position.coords);
        },
        (error) => {
          setLocationPermission('denied');
          console.error('위치 정보 가져오기 실패:', error);
        }
      );
    } else {
      setLocationPermission('denied');
    }
  };

  const handleDonate = () => {
    // 단일 소방서 기부 검증
    if (donationMode === 'single') {
      if (!selectedFireStation) {
        alert('기부할 소방서를 선택해주세요.');
        return;
      }
    } 
    // 복수 소방서 기부 검증
    else {
      if (selectedFireStations.length === 0) {
        alert('기부할 소방서를 최소 1개 이상 선택해주세요.');
        return;
      }
      
      // custom 모드일 때 모든 소방서에 금액이 설정되었는지 확인
      if (multipleType === 'custom') {
        const missingAmounts = selectedFireStations.filter(station => !customAmounts[station] || customAmounts[station] <= 0);
        if (missingAmounts.length > 0) {
          alert(`다음 소방서의 기부 금액을 설정해주세요: ${missingAmounts.join(', ')}`);
          return;
        }
      }
    }

    // 기존 검증 로직 유지
    if (!isAnonymous && !donorName.trim()) {
      alert('기부자명을 입력해주세요.');
      return;
    }

    if (!donorEmail.trim()) {
      alert('이메일을 입력해주세요.');
      return;
    }

    // 영수증 발급 시 연락처와 주민번호 필수 체크
    if (needReceipt) {
      if (!donorPhone.trim()) {
        alert('영수증 발급을 위해 연락처를 입력해주세요.');
        return;
      }
      if (!donorIdNumber.trim()) {
        alert('영수증 발급을 위해 주민등록번호를 입력해주세요.');
        return;
      }
    }

    if (!isLoggedIn && !isGuestEmailVerified) {
      alert('이메일 인증을 완료해주세요.');
      return;
    }

    if (isRegularDonation && !startDate) {
      alert('정기 기부 시작일을 선택해주세요.');
      return;
    }

    setShowConfirmModal(true);
  };

  const handleConfirmDonate = async () => {
    try {
      // 기부 데이터 구성
      let donationData;
      
      if (donationMode === 'single') {
        donationData = {
          mode: 'single',
          amount: getCurrentAmount(),
          cups: getCupCount(getCurrentAmount()),
          fireStation: selectedFireStation,
          // ... 기존 필드들
        };
      } else {
        let totalAmount = 0;
        let stationAmounts: {[key: string]: number} = {};
        
        if (multipleType === 'split') {
          const amountPerStation = Math.floor(getCurrentAmount() / selectedFireStations.length);
          selectedFireStations.forEach(station => {
            stationAmounts[station] = amountPerStation;
          });
          totalAmount = getCurrentAmount();
        } else if (multipleType === 'each') {
          selectedFireStations.forEach(station => {
            stationAmounts[station] = getCurrentAmount();
          });
          totalAmount = getCurrentAmount() * selectedFireStations.length;
        } else if (multipleType === 'custom') {
          stationAmounts = { ...customAmounts };
          totalAmount = Object.values(customAmounts).reduce((sum, amount) => sum + (amount || 0), 0);
        }
        
        donationData = {
          mode: 'multiple',
          multipleType: multipleType,
          amount: totalAmount,
          selectedFireStations: selectedFireStations,
          stationAmounts: stationAmounts,
          cups: getCupCount(totalAmount),
          // ... 기존 필드들
        };
      }

      // 공통 필드 추가
      donationData = {
        ...donationData,
        donorName: false 
          ? (isAnonymous ? null?.name || '단체' : `${donorName} (${null?.name})`)
          : (isAnonymous ? '익명' : donorName || '익명'),
        donorEmail: donorEmail,
        donorPhone: donorPhone,
        donorIdNumber: donorIdNumber,
        message: message,
        isAnonymous: isAnonymous,
        needReceipt: needReceipt,
        false: false,
        null: false ? null : null,
        null: false ? null : null,
        individualDonorName: false ? donorName : null,
        isRegularDonation: isRegularDonation,
        regularCycle: isRegularDonation ? regularCycle : null,
        startDate: isRegularDonation ? startDate : null,
      };

      console.log('기부 데이터:', donationData);

      // 백엔드 API 호출하여 기부 생성 및 결제 URL 받기
      const checkoutData = await apiRequest<{
        donation_id: string;
        order_id: string;
        payment_url?: string;
        billing_auth_url?: string;
      }>('/donations', {
        method: 'POST',
        body: JSON.stringify({
          mode: donationMode,
          amount: donationData.amount,
          currency: 'KRW',
          fire_station_id: donationMode === 'single' ? selectedFireStation : null,
          donor: {
            display_name: donationData.donorName,
            email: donationData.donorEmail,
            phone: donationData.donorPhone,
            is_anonymous: isAnonymous,
            needs_receipt: needReceipt,
          },
          regular: isRegularDonation ? {
            enabled: true,
            cycle: regularCycle,
            start_date: startDate,
          } : null,
          message: message,
        })
      });
      const orderId = checkoutData.order_id;

      const tossClientKey = process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY || 'test_ck_oEjb0gm23PYMm6epMNvoVpGwBJn5';
      const tossPayments = await loadTossPayments(tossClientKey);
      let orderName = '';

      if (donationMode === 'single') {
        orderName = `${getSelectedFireStationName()} ${isRegularDonation ? '정기 ' : ''}기부${false ? ` (${null?.name})` : ''} (커피 ${getCupCount(getCurrentAmount())}잔)`;
      } else {
        orderName = `${selectedFireStations.length}개 소방서 ${multipleType === 'split' ? '분할' : multipleType === 'each' ? '각각' : '개별'} ${isRegularDonation ? '정기 ' : ''}기부${false ? ` (${null?.name})` : ''} (총 커피 ${getCupCount(donationData.amount)}잔)`;
      }

      if (isRegularDonation) {
        // 정기결제는 빌링키 발급
        const customerKey = `customer_${checkoutData.donation_id}`;
        await tossPayments.requestBillingAuth('카드', {
          customerKey: customerKey,
          successUrl: `${window.location.origin}/payment/billing-success?type=regular&customerKey=${customerKey}`,
          failUrl: `${window.location.origin}/payment/fail`,
        });
      } else {
        setShowPaymentMethodModal(true);
        setShowConfirmModal(false);
        setPaymentData({
          tossPayments,
          orderId,
          orderName,
          donationData,
        });
      }
    } catch (error) {
      console.error('결제 요청 중 오류:', error);
      alert('결제 요청 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
  };

  const handlePaymentMethod = async (method: string) => {
    try {
      const { tossPayments, orderId, orderName, donationData } = paymentData;

      await tossPayments.requestPayment(method, {
        amount: donationData.amount,
        orderId,
        orderName,
        customerName: donationData.donorName,
        customerEmail: donationData.donorEmail || 'anonymous@example.com',
        successUrl: `${window.location.origin}/payment/success?station=${encodeURIComponent(getSelectedFireStationName())}`,
        failUrl: `${window.location.origin}/payment/fail`,
        flowMode: 'DIRECT',  // 웹 결제창 직접 표시 (앱 연동 방지)
        easyPay: method === '간편결제' ? '토스페이' : undefined,  // 간편결제 선택 시에만
        metadata: {
          fireStation: getSelectedFireStationName(),
          donorName: donationData.donorName,
          message,
          needReceipt: needReceipt.toString(),
          cups: getCupCount(donationData.amount).toString(),
        },
      });
    } catch (error) {
      console.error('결제 요청 중 오류:', error);
      alert('결제 요청 중 오류가 발생했습니다. 다시 시도해주세요.');
    }

    setShowPaymentMethodModal(false);
  };

  const handleCancelDonate = () => {
    setShowConfirmModal(false);
  };

  const handleIsAnonymousChange = (checked: boolean) => {
    setIsAnonymous(checked);
  };

  const handleDonationLoginChoice = (choice: 'login' | 'guest') => {
    setShowDonationLoginModal(false);
    if (choice === 'login') {
      const loginEvent = new CustomEvent('openLoginModal', { detail: { purpose: 'donation' } });
      window.dispatchEvent(loginEvent);
    } else {
      window.location.href = '/donations';
    }
  };

  const features = [
    {
      icon: 'ri-shield-check-line',
      title: '안전한 결제',
      description: '모든 결제는 SSL 암호화로 안전하게 보호됩니다',
    },
    {
      icon: 'ri-eye-line',
      title: '투명한 운영',
      description: '기부금 사용 내역을 실시간으로 확인할 수 있습니다',
    },
    {
      icon: 'ri-heart-line',
      title: '직접 전달',
      description: '전국 소방서에 커피와 간식으로 직접 전달됩니다',
    },
    {
      icon: 'ri-trophy-line',
      title: '기부 랭킹',
      description: '기부 랭킹에 참여하여 더 많은 분들과 함께해요',
    },
  ];


  const donationHistory = [
    {
      id: 1,
      date: new Date(),
      fireStation: '서울강남소방서',
      amount: 30000,
      message: '항상 고생이 많으십니다',
      status: 'completed',
      receiptIssued: true,
    },
  ];

  const getStatusBadge = (status: string) => {
    const statusMap: { [key: string]: { bg: string; text: string } } = {
      completed: { bg: 'bg-green-100', text: 'text-green-800' },
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
      failed: { bg: 'bg-red-100', text: 'text-red-800' },
    };
    const cfg = statusMap[status] || statusMap['pending'];
    return (
      <span className={`px-2 py-1 text-xs ${cfg.bg} ${cfg.text} rounded-full`}>
        {status}
      </span>
    );
  };

  const downloadReceipt = (donationId: number) => {
    alert(`영수증 다운로드: ${donationId}`);
  };
  // 기존 코드 삽입 종료

  return (
    <div className="bg-gray-50">
      {/* 히어로 섹션 */}
      <section
        className="relative h-[50vh] flex items-center justify-center bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.4)), url('https://readdy.ai/api/search-image?query=Korean%20firefighters%20drinking%20coffee%20together%20in%20fire%20station%2C%20warm%20community%20moment%2C%20grateful%20firefighters%20with%20steaming%20coffee%20cups%2C%20brotherhood%20and%20camaraderie%2C%20professional%20photography%2C%20warm%20orange%20and%20red%20lighting%2C%20heartwarming%20scene%20of%20support%20and%20appreciation&width=1920&height=800&seq=donations-hero&orientation=landscape')`,
        }}
      >
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-white">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            소방관들에게<br />따뜻한 마음을 전해주세요
          </h1>
          <p className="text-xl md:text-2xl text-gray-200 mb-8">
            여러분의 작은 기부가 현장에서 힘쓰는 소방관들에게 큰 힘이 됩니다
          </p>
          <div className="flex items-center justify-center space-x-8 text-lg">
            <div className="flex items-center space-x-2">
              <i className="ri-cup-fill text-orange-400 text-2xl"></i>
              <span>따뜻한 커피</span>
            </div>
            <div className="flex items-center space-x-2">
              <i className="ri-heart-fill text-red-400 text-2xl"></i>
              <span>진심어린 마음</span>
            </div>
            <div className="flex items-center space-x-2">
              <i className="ri-shield-fill text-blue-400 text-2xl"></i>
              <span>안전한 사회</span>
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* 기부하기 폼 */}
          <div className="lg:col-span-2">
            <Card className="p-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
                기부하기
              </h2>

              {/* 기부 금액 선택 - custom 모드일 때 숨김 */}
              {!(donationMode === 'multiple' && multipleType === 'custom') && (
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-gray-900 mb-6">
                    1. 기부 금액 선택
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                    {amounts.map((amount) => (
                      <button
                        key={amount.value}
                        onClick={() => handleAmountSelect(amount.value)}
                        className={`p-4 rounded-xl border-2 transition-all duration-200 ${
                          selectedAmount === amount.value && !customAmount
                            ? 'border-red-500 bg-red-50 text-red-700 shadow-md'
                            : 'border-gray-200 hover:border-red-300 text-gray-700 hover:shadow-sm'
                        }`}
                      >
                        <div className="text-lg font-bold">
                          {amount.value.toLocaleString()}원
                        </div>
                        <div className="text-sm text-gray-500">{amount.label}</div>
                      </button>
                    ))}
                  </div>

                  {/* 직접 입력 */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      직접 입력하기
                    </label>
                    <div className="flex items-center space-x-3">
                      <input
                        type="text"
                        value={customAmount}
                        onChange={handleCustomAmountChange}
                        placeholder="원하는 금액을 입력하세요"
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
                      />
                      <span className="text-gray-500 font-medium">원</span>
                    </div>
                    {customAmount && (
                      <p className="text-sm text-gray-500 mt-2">
                        커피 {getCupCount(parseInt(customAmount))}잔에 해당합니다
                      </p>
                    )}
                  </div>

                  {/* 선택된 금액 표시 */}
                  <div className="bg-gradient-to-r from-red-50 to-orange-50 p-6 rounded-xl border border-red-100">
                    <div className="flex items-center justify-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <i className="ri-cup-fill text-orange-500 text-3xl"></i>
                        <span className="text-3xl font-bold text-gray-900">
                          {getCurrentAmount().toLocaleString()}원
                        </span>
                      </div>
                      <div className="text-gray-600 text-lg">
                        커피 {getCupCount(getCurrentAmount())}잔
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 기부할 소방서 선택 - 현재 버전의 모달 기능 적용 */}
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-6">
                  {!(donationMode === 'multiple' && multipleType === 'custom') ? '2. ' : '1. '}기부할 소방서 선택
                </h3>
                
                {/* 기부 방식 선택 */}
                <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-4">기부 방식 선택</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="flex items-center space-x-3 cursor-pointer p-3 border-2 border-blue-200 rounded-lg hover:bg-blue-100 transition-all duration-200">
                      <input
                        type="radio"
                        name="donationMode"
                        value="single"
                        checked={donationMode === 'single'}
                        onChange={(e) => setDonationMode(e.target.value as 'single' | 'multiple')}
                        className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                      />
                      <div>
                        <div className="font-medium text-blue-900">단일 소방서 기부</div>
                        <div className="text-sm text-blue-700">하나의 소방서에만 기부</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center space-x-3 cursor-pointer p-3 border-2 border-blue-200 rounded-lg hover:bg-blue-100 transition-all duration-200">
                      <input
                        type="radio"
                        name="donationMode"
                        value="multiple"
                        checked={donationMode === 'multiple'}
                        onChange={(e) => setDonationMode(e.target.value as 'single' | 'multiple')}
                        className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                      />
                      <div>
                        <div className="font-medium text-blue-900">복수 소방서 기부</div>
                        <div className="text-sm text-blue-700">여러 소방서에 동시 기부</div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* 복수 기부 방식 상세 선택 */}
                {donationMode === 'multiple' && (
                  <div className="mb-6 p-4 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-900 mb-4">복수 기부 방식</h4>
                    <div className="space-y-3">
                      <label className="flex items-start space-x-3 cursor-pointer">
                        <input
                          type="radio"
                          name="multipleType"
                          value="split"
                          checked={multipleType === 'split'}
                          onChange={(e) => setMultipleType(e.target.value as 'split' | 'each' | 'custom')}
                          className="w-4 h-4 text-green-600 border-gray-300 focus:ring-green-500 mt-0.5"
                        />
                        <div>
                          <div className="font-medium text-green-900">분할 기부</div>
                          <div className="text-sm text-green-700">선택한 금액을 소방서 수로 나누어 기부</div>
                          <div className="text-xs text-green-600 mt-1">예: 10,000원 → 5개 소방서 → 각각 2,000원</div>
                        </div>
                      </label>
                      
                      <label className="flex items-start space-x-3 cursor-pointer">
                        <input
                          type="radio"
                          name="multipleType"
                          value="each"
                          checked={multipleType === 'each'}
                          onChange={(e) => setMultipleType(e.target.value as 'split' | 'each' | 'custom')}
                          className="w-4 h-4 text-green-600 border-gray-300 focus:ring-green-500 mt-0.5"
                        />
                        <div>
                          <div className="font-medium text-green-900">각각 기부</div>
                          <div className="text-sm text-green-700">선택한 모든 소방서에 해당 금액씩 기부</div>
                          <div className="text-xs text-green-600 mt-1">예: 10,000원 → 5개 소방서 → 총 50,000원</div>
                        </div>
                      </label>
                      
                      <label className="flex items-start space-x-3 cursor-pointer">
                        <input
                          type="radio"
                          name="multipleType"
                          value="custom"
                          checked={multipleType === 'custom'}
                          onChange={(e) => setMultipleType(e.target.value as 'split' | 'each' | 'custom')}
                          className="w-4 h-4 text-green-600 border-gray-300 focus:ring-green-500 mt-0.5"
                        />
                        <div>
                          <div className="font-medium text-green-900">소방서별 다른 금액 기부</div>
                          <div className="text-sm text-green-700">각 소방서마다 원하는 금액을 개별 설정</div>
                          <div className="text-xs text-green-600 mt-1">예: A소방서 5,000원, B소방서 10,000원, C소방서 3,000원</div>
                        </div>
                      </label>
                    </div>
                  </div>
                )}

                {/* 단일 소방서 선택 */}
                {donationMode === 'single' && (
                  <div className="space-y-4">
                    {/* 검색 입력 */}
                    <div className="relative">
                      <input
                        type="text"
                        value={searchFireStation}
                        onChange={(e) => {
                          setSearchFireStation(e.target.value);
                          setShowFireStationList(true);
                        }}
                        placeholder="소방서명 또는 지역명을 입력하세요"
                        className="w-full px-4 py-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
                      />
                      <i className="ri-search-line absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
                    </div>

                    {/* 빠른 선택 버튼들 */}
                    <div className="flex flex-wrap gap-3">
                      <button
                        onClick={() => setShowRegionModal(true)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                      >
                        <i className="ri-map-pin-line mr-2"></i>지역별 선택
                      </button>
                      
                      <button
                        onClick={handleLocationSelect}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                      >
                        <i className="ri-navigation-line mr-2"></i>내 위치 주변
                      </button>
                    </div>

                    {/* 선택된 소방서 표시 */}
                    {selectedFireStation && (
                      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-green-900">선택된 소방서</div>
                            <div className="text-green-700">{getSelectedFireStationName()}</div>
                          </div>
                          <button
                            onClick={() => {
                              setSelectedFireStation('');
                              setSearchFireStation('');
                              setSelectedRegion('');
                            }}
                            className="text-green-600 hover:text-green-800"
                          >
                            <i className="ri-close-line text-xl"></i>
                          </button>
                        </div>
                      </div>
                    )}

                    {/* 소방서 목록 */}
                    {showFireStationList && (
                      <div className="border border-gray-200 rounded-lg max-h-64 overflow-y-auto">
                        {isLoadingStations ? (
                          <div className="p-4 text-center text-gray-500">
                            소방서 목록을 불러오는 중...
                          </div>
                        ) : getFilteredFireStations().length === 0 ? (
                          <div className="p-4 text-center text-gray-500">
                            검색 결과가 없습니다.
                          </div>
                        ) : getFilteredFireStations().map((station) => {
                          const todayDispatch = Math.floor(Math.random() * 15) + 1;
                          const todayFires = Math.floor(Math.random() * 5) + 1;
                          
                          return (
                            <button
                              key={station.id}
                              onClick={() => handleFireStationSelect(station.id, station.name)}
                              className="w-full p-4 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors duration-200"
                            >
                              <div className="flex justify-between items-center">
                                <div>
                                  <div className="font-medium text-gray-900">{station.name}</div>
                                  <div className="text-sm text-gray-500">{station.region} {station.district}</div>
                                </div>
                                <div className="text-right text-sm">
                                  <div className={getEmergencyColor(todayDispatch)}>
                                    출동 {todayDispatch}건
                                  </div>
                                  <div className={getFireColor(todayFires)}>
                                    화재 {todayFires}건
                                  </div>
                                </div>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* 복수 소방서 선택 */}
                {donationMode === 'multiple' && (
                  <div className="space-y-4">
                    {/* 검색 입력 */}
                    <div className="relative">
                      <input
                        type="text"
                        value={searchFireStation}
                        onChange={(e) => setSearchFireStation(e.target.value)}
                        placeholder="소방서명 또는 지역명을 입력하세요"
                        className="w-full px-4 py-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
                      />
                      <i className="ri-search-line absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
                    </div>

                    {/* 빠른 선택 버튼들 */}
                    <div className="flex flex-wrap gap-3">
                      <button
                        onClick={() => {
                          const currentStations = getFilteredFireStations();
                          if (selectedFireStations.length === currentStations.length) {
                            setSelectedFireStations([]);
                          } else {
                            setSelectedFireStations(currentStations.map(s => s.name));
                          }
                        }}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                      >
                        <i className="ri-checkbox-multiple-line mr-2"></i>
                        {selectedFireStations.length === getFilteredFireStations().length ? '전체 해제' : '전체 선택'}
                      </button>
                      
                      <button
                        onClick={() => setShowRegionModal(true)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                      >
                        <i className="ri-map-pin-line mr-2"></i>지역별 선택
                      </button>
                      
                      <button
                        onClick={handleLocationSelect}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                      >
                        <i className="ri-navigation-line mr-2"></i>내 위치 주변
                      </button>
                    </div>

                    {/* 선택된 소방서들 표시 */}
                    {selectedFireStations.length > 0 && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-blue-900">
                            선택된 소방서: {selectedFireStations.length}개
                          </span>
                          <button
                            onClick={() => {
                              setSelectedFireStations([]);
                              setSelectedRegion('');
                            }}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            전체 해제
                          </button>
                        </div>
                        <div className="flex flex-wrap gap-2 max-h-20 overflow-y-auto">
                          {selectedFireStations.map((station, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                            >
                              {station}
                              <button
                                onClick={() => setSelectedFireStations(prev => prev.filter(s => s !== station))}
                                className="ml-1 text-blue-600 hover:text-blue-800"
                              >
                                <i className="ri-close-line text-sm"></i>
                              </button>
                            </span>
                          ))}
                        </div>
                        
                        {/* 기부 금액 미리보기 */}
                        <div className="mt-4 p-3 bg-white rounded border">
                          <div className="text-sm font-medium text-gray-900 mb-2">기부 금액 미리보기</div>
                          {multipleType === 'split' && (
                            <div className="text-sm text-gray-600">
                              총 {getCurrentAmount().toLocaleString()}원 ÷ {selectedFireStations.length}개 소방서 = 
                              <span className="font-medium text-red-600 ml-1">
                                소방서당 {Math.floor(getCurrentAmount() / selectedFireStations.length).toLocaleString()}원
                              </span>
                            </div>
                          )}
                          {multipleType === 'each' && (
                            <div className="text-sm text-gray-600">
                              {getCurrentAmount().toLocaleString()}원 × {selectedFireStations.length}개 소방서 = 
                              <span className="font-medium text-red-600 ml-1">
                                총 {(getCurrentAmount() * selectedFireStations.length).toLocaleString()}원
                              </span>
                            </div>
                          )}
                          {multipleType === 'custom' && (
                            <div className="text-sm text-gray-600">
                              각 소방서별로 개별 금액을 설정해주세요
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* 소방서별 개별 금액 설정 (custom 모드일 때) */}
                    {multipleType === 'custom' && selectedFireStations.length > 0 && (
                      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <h4 className="font-medium text-yellow-900 mb-4">소방서별 기부 금액 설정</h4>
                        <div className="space-y-3 max-h-64 overflow-y-auto">
                          {selectedFireStations.map((station, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-white rounded border">
                              <div className="font-medium text-gray-900">{station}</div>
                              <div className="flex items-center space-x-2">
                                <input
                                  type="number"
                                  min="1000"
                                  step="1000"
                                  value={customAmounts[station] || ''}
                                  onChange={(e) => {
                                    const amount = parseInt(e.target.value) || 0;
                                    setCustomAmounts(prev => ({
                                      ...prev,
                                      [station]: amount
                                    }));
                                  }}
                                  placeholder="금액"
                                  className="w-24 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-yellow-500"
                                />
                                <span className="text-sm text-gray-500">원</span>
                              </div>
                            </div>
                          ))}
                        </div>
                        <div className="mt-3 p-2 bg-white rounded border">
                          <div className="text-sm font-medium text-gray-900">
                            총 기부 금액: 
                            <span className="text-red-600 ml-1">
                              {Object.values(customAmounts).reduce((sum, amount) => sum + (amount || 0), 0).toLocaleString()}원
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 소방서 목록 (체크박스 형태) */}
                    <div className="border border-gray-200 rounded-lg max-h-64 overflow-y-auto">
                      {getFilteredFireStations().map((station) => {
                        const todayDispatch = Math.floor(Math.random() * 15) + 1;
                        const todayFires = Math.floor(Math.random() * 5) + 1;
                        const isSelected = selectedFireStations.includes(station.name);
                        
                        return (
                          <div
                            key={station.id}
                            className={`p-4 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors duration-200 ${
                              isSelected ? 'bg-blue-50' : ''
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <input
                                  type="checkbox"
                                  checked={isSelected}
                                  onChange={() => {
                                    if (isSelected) {
                                      setSelectedFireStations(prev => prev.filter(s => s !== station.name));
                                      // custom 모드에서 해제 시 금액도 제거
                                      if (multipleType === 'custom') {
                                        setCustomAmounts(prev => {
                                          const newAmounts = { ...prev };
                                          delete newAmounts[station.name];
                                          return newAmounts;
                                        });
                                      }
                                    } else {
                                      setSelectedFireStations(prev => [...prev, station.name]);
                                    }
                                  }}
                                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                />
                                <div>
                                  <div className="font-medium text-gray-900">{station.name}</div>
                                  <div className="text-sm text-gray-500">{station.region} {station.district}</div>
                                </div>
                              </div>
                              <div className="text-right text-sm">
                                <div className={getEmergencyColor(todayDispatch)}>
                                  출동 {todayDispatch}건
                                </div>
                                <div className={getFireColor(todayFires)}>
                                  화재 {todayFires}건
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* 기부 정보 */}
              {/* 기존 코드 삽입 시작 */}
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-6">
                  {!(donationMode === 'multiple' && multipleType === 'custom') ? '3. ' : '2. '}기부 정보
                </h3>

                <div className="space-y-6">
                  {/* 정기 기부 옵션 추가 */}
                  <div className="bg-green-50 p-6 rounded-lg">
                    <div className="flex items-start space-x-3 mb-4">
                      <input
                        type="checkbox"
                        id="isRegularDonation"
                        checked={isRegularDonation}
                        onChange={(e) => setIsRegularDonation(e.target.checked)}
                        className="w-5 h-5 text-green-600 border-gray-300 rounded focus:ring-green-500 mt-0.5"
                      />
                      <div>
                        <label
                          htmlFor="isRegularDonation"
                          className="text-green-900 font-semibold text-lg cursor-pointer"
                        >
                          <i className="ri-calendar-check-line mr-2"></i>
                          정기 기부로 신청하기
                        </label>
                        <p className="text-green-700 mt-1">
                          매월/분기별/연간 자동으로 기부하여 지속적인 도움을 제공하세요
                        </p>
                      </div>
                    </div>

                    {/* 정기 기부 상세 설정 */}
                    {isRegularDonation && (
                      <div className="space-y-4 mt-6 border-t border-green-200 pt-4">
                        <div>
                          <label className="block text-sm font-medium text-green-800 mb-3">
                            기부 주기 선택
                          </label>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            {regularCycles.map((cycle) => (
                              <button
                                key={cycle.value}
                                onClick={() => setRegularCycle(cycle.value as any)}
                                className={`p-3 rounded-lg border-2 transition-all duration-200 text-left ${
                                  regularCycle === cycle.value
                                    ? 'border-green-500 bg-green-100 text-green-800'
                                    : 'border-green-200 hover:border-green-300 text-green-700'
                                }`}
                              >
                                <div className="font-medium">{cycle.label}</div>
                                <div className="text-sm text-green-600">{cycle.description}</div>
                              </button>
                            ))}
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-green-800 mb-2">
                            시작일 <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            min={new Date().toISOString().split('T')[0]}
                            className="w-full px-4 py-3 border border-green-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                          />
                          <p className="text-xs text-green-600 mt-1">
                            선택한 날짜부터 정기 기부가 시작됩니다
                          </p>
                        </div>

                        <div className="bg-green-100 p-4 rounded-lg">
                          <h4 className="text-sm font-semibold text-green-800 mb-2">
                            <i className="ri-information-line mr-1"></i>
                            정기 기부 안내
                          </h4>
                          <ul className="text-xs text-green-700 space-y-1">
                            <li>• 정기 기부는 언제든지 마이페이지에서 변경/취소할 수 있습니다</li>
                            <li>• 매회 결제 전 이메일로 안내 메시지를 보내드립니다</li>
                            <li>• 결제 실패 시 3회까지 재시도 후 자동 일시정지됩니다</li>
                            <li>• 기부금 영수증은 매회 자동으로 발급됩니다</li>
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 영수증 발급 여부 */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        id="needReceipt"
                        checked={needReceipt}
                        onChange={(e) => setNeedReceipt(e.target.checked)}
                        className="w-5 h-5 text-gray-600 border-gray-300 rounded focus:ring-gray-500 mt-0.5"
                      />
                      <div>
                        <label
                          htmlFor="needReceipt"
                          className="text-gray-700 font-medium cursor-pointer"
                        >
                          기부금 영수증 발급받기
                        </label>
                        <p className="text-sm text-gray-600 mt-1">
                          연말정산 소득공제를 받으시려면 체크해주세요
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 계정 정보 사용 여부 (로그인한 경우만) */}
                  {isLoggedIn && !false && (
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        id="useAccountInfo"
                        checked={useAccountInfo}
                        onChange={(e) =>
                          handleUseAccountInfo(e.target.checked)
                        }
                        className="w-5 h-5 text-red-600 border-gray-300 rounded focus:ring-red-500"
                      />
                      <label
                        htmlFor="useAccountInfo"
                        className="text-gray-700 font-medium"
                      >
                        계정 정보 사용하기 ({userInfo.name}, {userInfo.email})
                      </label>
                    </div>
                  )}

                  {/* 기부자명 입력 - 단체 기부가 아닌 경우에만 표시 */}
                  {!false && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        기부자명 {needReceipt && <span className="text-red-500">*</span>}
                      </label>
                      <input
                        type="text"
                        value={donorName}
                        onChange={(e) => setDonorName(e.target.value)}
                        placeholder="기부자명을 입력하세요"
                        disabled={useAccountInfo || isAnonymous}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm disabled:bg-gray-100 disabled:text-gray-500"
                      />
                      {needReceipt && (
                        <p className="text-xs text-gray-500 mt-1">
                          기부 영수증에 나올 기부자명이므로 정확하게 작성해주세요.
                        </p>
                      )}
                    </div>
                  )}

                  {/* 연락처 입력 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      연락처 {needReceipt && <span className="text-red-500">*</span>}
                    </label>
                    <input
                      type="tel"
                      value={donorPhone}
                      onChange={(e) => setDonorPhone(e.target.value)}
                      placeholder="연락처를 입력하세요 (예: 010-1234-5678)"
                      disabled={useAccountInfo}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm disabled:bg-gray-100 disabled:text-gray-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {needReceipt ? "영수증 발급을 위해 필요합니다." : "기부 확인 및 문의를 위해 필요합니다."}
                    </p>
                  </div>

                  {/* 주민등록번호 입력 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      주민등록번호 {needReceipt && <span className="text-red-500">*</span>}
                    </label>
                    <input
                      type="text"
                      value={donorIdNumber}
                      onChange={(e) => setDonorIdNumber(e.target.value)}
                      placeholder="주민등록번호를 입력하세요 (예: 123456-1234567)"
                      disabled={useAccountInfo}
                      maxLength={14}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm disabled:bg-gray-100 disabled:text-gray-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {needReceipt ? "영수증 발급을 위해 필요합니다." : "기부자 확인을 위해 필요합니다."}
                    </p>
                  </div>

                  {/* 이메일 입력 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      이메일 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="email"
                      value={donorEmail}
                      onChange={(e) => {
                        setDonorEmail(e.target.value);
                        if (!isLoggedIn) {
                          setIsGuestEmailVerified(false);
                          setIsGuestEmailVerificationSent(false);
                          setGuestEmailVerificationCode('');
                        }
                      }}
                      placeholder="이메일을 입력하세요"
                      disabled={useAccountInfo}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm disabled:bg-gray-100 disabled:text-gray-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {needReceipt ? "기부금 영수증이 이메일로 발송됩니다." : "알림 및 확인 메일을 받기 위해 필요합니다."}
                    </p>

                    {/* 비회원 이메일 인증 */}
                    {!isLoggedIn && donorEmail && (
                      <div className="mt-4 space-y-3">
                        {!isGuestEmailVerified && (
                          <div className="flex space-x-2">
                            <button
                              onClick={sendGuestEmailVerification}
                              disabled={isGuestEmailVerificationSent}
                              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors duration-200 whitespace-nowrap"
                            >
                              {isGuestEmailVerificationSent ? 
                                `재발송 (${formatTimer(guestVerificationTimer)})` : 
                                '이메일 인증'}
                            </button>
                            {isGuestEmailVerificationSent && (
                              <input
                                type="text"
                                value={guestEmailVerificationCode}
                                onChange={(e) => setGuestEmailVerificationCode(e.target.value)}
                                placeholder="인증번호 6자리"
                                maxLength={6}
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                              />
                            )}
                          </div>
                        )}

                        {isGuestEmailVerificationSent && !isGuestEmailVerified && (
                          <button
                            onClick={verifyGuestEmail}
                            className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors duration-200"
                          >
                            인증번호 확인
                          </button>
                        )}

                        {isGuestEmailVerified && (
                          <div className="flex items-center space-x-2 text-green-600 text-sm">
                            <i className="ri-check-circle-fill"></i>
                            <span>이메일 인증이 완료되었습니다.</span>
                          </div>
                        )}

                        {isGuestEmailVerificationSent && !isGuestEmailVerified && (
                          <p className="text-xs text-gray-500">
                            인증번호를 받지 못하셨나요? 스팸함을 확인해보세요.
                            <br />임시 인증번호: 123456 (테스트용)
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* 응원 메시지 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      응원 메시지 (선택사항)
                    </label>
                    <textarea
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="소방관들에게 전하고 싶은 응원의 메시지를 적어주세요"
                      rows={4}
                      maxLength={500}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 resize-none text-sm"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {message.length}/500자
                    </p>
                  </div>
                </div>
              </div>
              {/* 기존 코드 삽입 종료 */}

              {/* 기부하기 버튼 */}
              <div className="text-center">
                <Button
                  size="lg"
                  className="px-16 py-5 text-xl font-bold"
                  onClick={handleDonate}
                >
                  <i className="ri-heart-fill mr-2"></i>
                  기부하기
                </Button>
                <p className="text-sm text-gray-500 mt-4">
                  기부해주신 마음은 선택하신 소방서에 따뜻한 커피와 간식으로 전달됩니다
                </p>
              </div>
            </Card>
          </div>

          {/* 사이드바 */}
          {/* 기존 사이드바 코드 삽입 시작 */}
          <div className="space-y-8">
            {/* 실시간 기부 현황 */}
            <Card className="p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <i className="ri-live-line text-red-500 mr-2"></i>
                실시간 기부 현황
              </h3>
              <div className="space-y-4">
                {recentDonations.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    아직 기부 내역이 없습니다
                  </div>
                ) : (
                  recentDonations.map((donation, index) => (
                    <div
                      key={index}
                      className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <div className="font-medium text-gray-900">
                          {donation.donor}
                        </div>
                        <div className="text-sm text-gray-500">{donation.time}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-red-600">
                          {donation.amount.toLocaleString()}원
                        </div>
                        <div className="text-sm text-gray-500 flex items-center justify-end">
                          <i className="ri-cup-fill text-orange-500 mr-1"></i>
                          {donation.cups}잔
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>

            {/* 기부 특징 */}
            <Card className="p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">
                왜 우리와 함께해야 할까요?
              </h3>
              <div className="space-y-6">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <div className="w-12 h-12 flex items-center justify-center bg-red-100 rounded-full flex-shrink-0">
                      <i className={`${feature.icon} text-red-600 text-xl`}></i>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-1">
                        {feature.title}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* 기부 통계 */}
            <Card className="p-6 bg-gradient-to-br from-red-50 to-orange-50">
              <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">
                전체 기부 현황
              </h3>
              <div className="space-y-4">
                <div className="text-center p-4 bg-white rounded-lg shadow-sm">
                  <div className="text-2xl font-bold text-red-600 mb-1">
                    {donationStats.total_amount.toLocaleString()}원
                  </div>
                  <div className="text-sm text-gray-600">총 기부금액</div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className="text-lg font-bold text-orange-600 mb-1">
                      {donationStats.total_cups.toLocaleString()}잔
                    </div>
                    <div className="text-xs text-gray-600">전달된 커피</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className="text-lg font-bold text-blue-600 mb-1">
                      {donationStats.total_users.toLocaleString()}명
                    </div>
                    <div className="text-xs text-gray-600">참여 기부자</div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
          {/* 기존 사이드바 코드 삽입 종료 */}
        </div>
      </section>

      {/* 지역별 선택 모달 */}
      {showRegionModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-4xl mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">지역별 소방서 선택</h3>
                <p className="text-gray-600">지역을 선택하시면 해당 지역의 소방서 목록을 보여드립니다</p>
              </div>
              <button
                onClick={() => setShowRegionModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {regions.map((region) => {
                const regionStations = getFireStationsByRegion(region);
                
                return (
                  <button
                    key={region}
                    onClick={() => handleRegionSelect(region)}
                    className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 text-left"
                  >
                    <div className="font-medium text-gray-900 mb-1">{region}</div>
                    <div className="text-sm text-gray-500">
                      {regionStations.length}개 소방서
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="mt-6 flex justify-end">
              <Button
                variant="outline"
                onClick={() => setShowRegionModal(false)}
              >
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 기존 모달들 삽입 시작 */}
      {/* 위치 기반 선택 모달 */}
      {showLocationModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-navigation-line text-green-500 text-3xl animate-pulse"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                위치 확인 중
              </h3>
              <p className="text-gray-600 mb-6">
                현재 위치를 기반으로 주변 소방서를 찾고 있습니다...
              </p>
              
              {locationPermission === 'granted' && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900">주변 소방서</h4>
                  <div className="space-y-2">
                    {getNearbyFireStations().map((station) => (
                      <button
                        key={station.id}
                        onClick={() => {
                          if (donationMode === 'single') {
                            handleFireStationSelect(String(station.id), station.name);
                          } else {
                            setSelectedFireStations(prev => [...prev, station.name]);
                          }
                          setShowLocationModal(false);
                        }}
                        className="w-full p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <div className="font-medium text-gray-900">{station.name}</div>
                            <div className="text-sm text-gray-500">{station.distance}</div>
                          </div>
                          <div className="text-right text-sm">
                            <div className={getEmergencyColor(station.todayDispatch)}>
                              출동 {station.todayDispatch}건
                            </div>
                            <div className={getFireColor(station.todayFires)}>
                              화재 {station.todayFires}건
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {locationPermission === 'denied' && (
                <div className="text-red-600">
                  <p className="mb-4">위치 권한이 거부되었습니다.</p>
                  <p className="text-sm">브라우저 설정에서 위치 권한을 허용해주세요.</p>
                </div>
              )}

              <Button
                variant="outline"
                onClick={() => setShowLocationModal(false)}
                className="mt-6"
              >
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 기부 확인 모달 */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-2xl mx-4">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-heart-fill text-red-500 text-3xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">기부 확인</h3>
              <p className="text-gray-600">아래 내용을 확인하고 기부를 진행해주세요</p>
            </div>

            <div className="space-y-6">
              {/* 기부 정보 */}
              <div className="bg-gray-50 p-6 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">기부 정보</h4>
                <div className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">기부 방식</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {donationMode === 'single' ? '단일 소방서 기부' : 
                         `복수 소방서 기부 (${multipleType === 'split' ? '분할' : multipleType === 'each' ? '각각' : '개별'})`}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">총 기부 금액</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {donationMode === 'single' ? 
                          `${getCurrentAmount().toLocaleString()}원 (커피 ${getCupCount(getCurrentAmount())}잔)` :
                          multipleType === 'split' ? 
                            `${getCurrentAmount().toLocaleString()}원 (커피 ${getCupCount(getCurrentAmount())}잔)` :
                          multipleType === 'each' ? 
                            `${(getCurrentAmount() * selectedFireStations.length).toLocaleString()}원 (커피 ${getCupCount(getCurrentAmount() * selectedFireStations.length)}잔)` :
                            `${Object.values(customAmounts).reduce((sum, amount) => sum + (amount || 0), 0).toLocaleString()}원 (커피 ${getCupCount(Object.values(customAmounts).reduce((sum, amount) => sum + (amount || 0), 0))}잔)`
                        }
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-600">기부할 소방서</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {donationMode === 'single' ? 
                        selectedFireStation :
                        `${selectedFireStations.length}개 소방서`
                      }
                    </div>
                    {donationMode === 'multiple' && (
                      <div className="mt-2 max-h-32 overflow-y-auto">
                        {multipleType === 'custom' ? (
                          <div className="space-y-1">
                            {selectedFireStations.map(station => (
                              <div key={station} className="text-sm text-gray-600 flex justify-between">
                                <span>{station}</span>
                                <span className="font-medium">{(customAmounts[station] || 0).toLocaleString()}원</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-sm text-gray-600">
                            {selectedFireStations.join(', ')}
                            {multipleType === 'split' && (
                              <div className="mt-1 text-xs">
                                (각 소방서당 {Math.floor(getCurrentAmount() / selectedFireStations.length).toLocaleString()}원)
                              </div>
                            )}
                            {multipleType === 'each' && (
                              <div className="mt-1 text-xs">
                                (각 소방서에 {getCurrentAmount().toLocaleString()}원씩)
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {isRegularDonation && (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <div className="text-sm text-gray-600">기부 주기</div>
                          <div className="text-lg font-semibold text-gray-900">
                            {regularCycles.find(c => c.value === regularCycle)?.label}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">시작일</div>
                          <div className="text-lg font-semibold text-gray-900">{startDate}</div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* 기부자 정보 */}
              <div className="bg-gray-50 p-6 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">기부자 정보</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">기부자명</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {false 
                        ? (isAnonymous ? null?.name || '단체' : `${donorName} (${null?.name})`)
                        : (isAnonymous ? '익명' : donorName || '익명')
                      }
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">이메일</div>
                    <div className="text-lg font-semibold text-gray-900">{donorEmail}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">연락처</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {donorPhone || '미입력'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">주민등록번호</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {donorIdNumber ? donorIdNumber.replace(/(\d{6})-(\d{7})/, '$1-*******') : '미입력'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">영수증 발급</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {needReceipt ? '발급' : '발급 안함'}
                    </div>
                  </div>
                  {false && (
                    <div>
                      <div className="text-sm text-gray-600">단체 코드</div>
                      <div className="text-lg font-semibold text-gray-900">{null}</div>
                    </div>
                  )}
                </div>
              </div>

              {/* 응원 메시지 */}
              {message && (
                <div className="bg-blue-50 p-6 rounded-lg">
                  <h4 className="text-lg font-semibold text-blue-900 mb-2">응원 메시지</h4>
                  <p className="text-blue-800">{message}</p>
                </div>
              )}

              {/* 버튼 */}
              <div className="flex space-x-4">
                <Button
                  variant="outline"
                  onClick={handleCancelDonate}
                  className="flex-1"
                >
                  취소
                </Button>
                <Button
                  onClick={handleConfirmDonate}
                  className="flex-1"
                >
                  <i className="ri-heart-fill mr-2"></i>
                  {isRegularDonation ? '정기 기부 신청' : '기부하기'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 결제 방법 선택 모달 */}
      {showPaymentMethodModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-bank-card-line text-red-500 text-3xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">결제 방법 선택</h3>
              <p className="text-gray-600">원하시는 결제 방법을 선택해주세요</p>
            </div>

            <div className="space-y-3 mb-6">
              <button
                onClick={() => handlePaymentMethod('카드')}
                className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-red-400 hover:bg-red-50 transition-all duration-200 text-left"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                    <i className="ri-bank-card-line text-red-600 text-xl"></i>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">신용카드/체크카드</div>
                    <div className="text-sm text-gray-500">모든 카드사 이용 가능</div>
                  </div>
                </div>
              </button>

              <button
                onClick={() => handlePaymentMethod('계좌이체')}
                className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-green-400 hover:bg-green-50 transition-all duration-200 text-left"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                    <i className="ri-bank-line text-green-600 text-xl"></i>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">계좌이체</div>
                    <div className="text-sm text-gray-500">실시간 계좌이체로 안전하게</div>
                  </div>
                </div>
              </button>

              <button
                onClick={() => handlePaymentMethod('가상계좌')}
                className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-all duration-200 text-left"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                    <i className="ri-wallet-line text-purple-600 text-xl"></i>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">가상계좌</div>
                    <div className="text-sm text-gray-500">입금 계좌번호로 이체</div>
                  </div>
                </div>
              </button>

              <button
                onClick={() => handlePaymentMethod('토스페이')}
                className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-400 hover:bg-indigo-50 transition-all duration-200 text-left"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
                    <i className="ri-smartphone-line text-indigo-600 text-xl"></i>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">간편결제</div>
                    <div className="text-sm text-gray-500">토스페이, 페이코 등</div>
                  </div>
                </div>
              </button>
            </div>

            {/* 취소 버튼 */}
            <div className="text-center">
              <Button
                variant="outline"
                onClick={() => setShowPaymentMethodModal(false)}
                className="w-full"
              >
                취소
              </Button>
            </div>
          </div>
        </div>
      )}
      {/* 기존 모달들 삽입 종료 */}
    </div>
  );
}
