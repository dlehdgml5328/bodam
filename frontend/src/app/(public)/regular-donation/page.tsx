'use client';

import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { ChangeEvent, useState } from 'react';
import { loadTossPayments } from '@tosspayments/payment-sdk';

export default function RegularDonationPage() {
  // 기존 상태
  const [selectedAmount, setSelectedAmount] = useState(30000);
  const [customAmount, setCustomAmount] = useState('');
  
  // 단체 기부 관련 상태
  const [groupName, setGroupName] = useState('');
  const [groupType, setGroupType] = useState<'company' | 'organization' | 'group'>('company');
  const [groupNumber, setGroupNumber] = useState(''); // 고유번호/사업자등록번호 추가
  const [managerName, setManagerName] = useState('');
  const [managerEmail, setManagerEmail] = useState('');
  const [managerPhone, setManagerPhone] = useState(''); // 담당자 연락처 추가
  const [isManagerEmailVerified, setIsManagerEmailVerified] = useState(false);
  const [emailVerificationCode, setEmailVerificationCode] = useState('');
  const [isEmailVerificationSent, setIsEmailVerificationSent] = useState(false);
  const [verificationTimer, setVerificationTimer] = useState(0);
  const [groupCode, setGroupCode] = useState('');
  const [showGroupCodeModal, setShowGroupCodeModal] = useState(false);
  const [isGroupAnonymous, setIsGroupAnonymous] = useState(false);
  
  // 기존 단체 추천 관련 상태 추가
  const [showRecommendedGroups, setShowRecommendedGroups] = useState(false);
  const [recommendedGroups, setRecommendedGroups] = useState<any[]>([]);

  // 정기 기부 관련 상태
  const [isRegularDonation, setIsRegularDonation] = useState(false);
  const [regularCycle, setRegularCycle] = useState<'monthly' | 'quarterly' | 'yearly'>('monthly');
  const [startDate, setStartDate] = useState('');

  // 소방서 선택 관련 상태 - 기부 페이지와 동일하게 추가
  const [donationMode, setDonationMode] = useState<'single' | 'multiple'>('single');
  const [multipleType, setMultipleType] = useState<'split' | 'each' | 'custom'>('split');
  const [selectedFireStation, setSelectedFireStation] = useState('');
  const [selectedFireStations, setSelectedFireStations] = useState<string[]>([]);
  const [customAmounts, setCustomAmounts] = useState<{[key: string]: number}>({});
  const [searchFireStation, setSearchFireStation] = useState('');
  const [showFireStationList, setShowFireStationList] = useState(false);
  const [showRegionModal, setShowRegionModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState('');
  const [locationPermission, setLocationPermission] = useState<'granted' | 'denied' | 'pending'>('pending');

  const [needReceipt, setNeedReceipt] = useState(true);

  // 결제 관련 상태 추가
  const [showPaymentMethodModal, setShowPaymentMethodModal] = useState(false);
  const [paymentData, setPaymentData] = useState<any>(null);

  // 응원 메시지 상태 추가 (누락된 부분)
  const [message, setMessage] = useState('');

  const amounts = [
    { value: 30000, cups: 10, label: '커피 10잔' },
    { value: 60000, cups: 20, label: '커피 20잔' },
    { value: 150000, cups: 50, label: '커피 50잔' },
    { value: 300000, cups: 100, label: '커피 100잔' },
    { value: 600000, cups: 200, label: '커피 200잔' },
    { value: 1500000, cups: 500, label: '커피 500잔' },
  ];

  const groupTypes = [
    { value: 'company', label: '기업' },
    { value: 'organization', label: '기관' },
    { value: 'group', label: '단체' }
  ];

  const regularCycles = [
    { value: 'monthly', label: '매월', description: '매월 정기적으로 기부' },
    { value: 'quarterly', label: '분기별', description: '3개월마다 기부' },
    { value: 'yearly', label: '연간', description: '1년마다 기부' }
  ];

  // 기존 등록 단체 데이터 (실제로는 서버에서 가져와야 함)
  const existingGroups = [
    {
      id: 1,
      name: '테크솔루션',
      type: 'company',
      number: '123-45-67890',
      managerName: '김철수',
      managerEmail: 'kim@techsolution.com',
      managerPhone: '010-1234-5678',
    },
    {
      id: 2,
      name: '서울시청',
      type: 'organization',
      number: '104-82-12345',
      managerName: '박영희',
      managerEmail: 'park@seoul.go.kr',
      managerPhone: '010-2345-6789',
    },
    {
      id: 3,
      name: '한국대학교',
      type: 'organization',
      number: '101-82-54321',
      managerName: '최교수',
      managerEmail: 'choi@korea.ac.kr',
      managerPhone: '010-3456-7890',
    },
    {
      id: 4,
      name: '강남FC축구회',
      type: 'group',
      number: '',
      managerName: '이감독',
      managerEmail: 'lee@gangnamfc.com',
      managerPhone: '010-4567-8901',
    },
    {
      id: 5,
      name: '봉사단체 나눔',
      type: 'group',
      number: 'REG-2024-001',
      managerName: '정대표',
      managerEmail: 'jung@nanum.org',
      managerPhone: '010-5678-9012',
    },
  ];

  // 지역 목록 추가
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

  // 소방서 목록 추가
  const fireStations = [
    { id: 1, name: '서울중부소방서', region: '서울특별시', district: '중구' },
    { id: 2, name: '서울강남소방서', region: '서울특별시', district: '강남구' },
    { id: 3, name: '서울서초소방서', region: '서울특별시', district: '서초구' },
    { id: 4, name: '서울용산소방서', region: '서울특별시', district: '용산구' },
    { id: 5, name: '서울마포소방서', region: '서울특별시', district: '마포구' },
    { id: 6, name: '부산해운대소방서', region: '부산광역시', district: '해운대구' },
    { id: 7, name: '부산중부소방서', region: '부산광역시', district: '중구' },
    { id: 8, name: '부산서부소방서', region: '부산광역시', district: '서구' },
    { id: 9, name: '부산동래소방서', region: '부산광역시', district: '동래구' },
    { id: 10, name: '인천계양소방서', region: '인천광역시', district: '계양구' },
    { id: 11, name: '인천중부소방서', region: '인천광역시', district: '중구' },
    { id: 12, name: '인천남동소방서', region: '인천광역시', district: '남동구' },
    { id: 13, name: '대구중구소방서', region: '대구광역시', district: '중구' },
    { id: 14, name: '대구수성소방서', region: '대구광역시', district: '수성구' },
    { id: 15, name: '광주서구소방서', region: '광주광역시', district: '서구' },
    { id: 16, name: '광주남구소방서', region: '광주광역시', district: '남구' },
    { id: 17, name: '대전유성소방서', region: '대전광역시', district: '유성구' },
    { id: 18, name: '대전서구소방서', region: '대전광역시', district: '서구' },
    { id: 19, name: '울산남구소방서', region: '울산광역시', district: '남구' },
    { id: 20, name: '울산중구소방서', region: '울산광역시', district: '중구' },
    { id: 21, name: '경기성남소방서', region: '경기도', district: '성남시' },
    { id: 22, name: '경기수원소방서', region: '경기도', district: '수원시' },
    { id: 23, name: '경기안양소방서', region: '경기도', district: '안양시' },
    { id: 24, name: '경기고양소방서', region: '경기도', district: '고양시' },
    { id: 25, name: '강원춘천소방서', region: '강원도', district: '춘천시' },
    { id: 26, name: '강원원주소방서', region: '강원도', district: '원주시' },
    { id: 27, name: '충북청주소방서', region: '충청북도', district: '청주시' },
    { id: 28, name: '충북충주소방서', region: '충청북도', district: '충주시' },
    { id: 29, name: '충남천안소방서', region: '충청남도', district: '천안시' },
    { id: 30, name: '충남아산소방서', region: '충청남도', district: '아산시' },
    { id: 31, name: '전북전주소방서', region: '전라북도', district: '전주시' },
    { id: 32, name: '전북익산소방서', region: '전라북도', district: '익산시' },
    { id: 33, name: '전남목포소방서', region: '전라남도', district: '목포시' },
    { id: 34, name: '전남순천소방서', region: '전라남도', district: '순천시' },
    { id: 35, name: '경북포항소방서', region: '경상북도', district: '포항시' },
    { id: 36, name: '경북구미소방서', region: '경상북도', district: '구미시' },
    { id: 37, name: '경남창원소방서', region: '경상남도', district: '창원시' },
    { id: 38, name: '경남김해소방서', region: '경상남도', district: '김해시' },
    { id: 39, name: '제주제주소방서', region: '제주특별자치도', district: '제주시' },
    { id: 40, name: '제주서귀포소방서', region: '제주특별자치도', district: '서귀포시' },
  ];

  // 지역별 소방서 필터링
  const getFireStationsByRegion = (region: string) => {
    return fireStations.filter((station) => station.region === region);
  };

  // 내 위치 기반 추천 소방서
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

  // 필터링된 소방서 목록
  const getFilteredFireStations = () => {
    let stations = fireStations;
    if (selectedRegion) {
      stations = getFireStationsByRegion(selectedRegion);
    }
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

  // 소방서 선택 핸들러
  const handleFireStationSelect = (stationName: string) => {
    if (donationMode === 'single') {
      setSelectedFireStation(stationName);
      setSearchFireStation(stationName);
      setShowFireStationList(false);
    } else {
      // 복수 모드에서는 체크박스 형태로 동작
      if (selectedFireStations.includes(stationName)) {
        setSelectedFireStations(prev => prev.filter(s => s !== stationName));
        // custom 모드에서 해제 시 금액도 제거
        if (multipleType === 'custom') {
          setCustomAmounts(prev => {
            const newAmounts = { ...prev };
            delete newAmounts[stationName];
            return newAmounts;
          });
        }
      } else {
        setSelectedFireStations(prev => [...prev, stationName]);
      }
    }
  };

  // 지역 선택 핸들러
  const handleRegionSelect = (region: string) => {
    setSelectedRegion(region);
    setShowRegionModal(false);
    setSearchFireStation('');
    setShowFireStationList(true);
  };

  // 위치 선택 핸들러
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

  // 기존 등록 단체 검색 및 추천
  const searchExistingGroups = (name: string, number: string) => {
    if (!name.trim() && !number.trim()) {
      setRecommendedGroups([]);
      setShowRecommendedGroups(false);
      return;
    }

    const filtered = existingGroups.filter(group => 
      group.name.toLowerCase().includes(name.toLowerCase()) ||
      (number && group.number.includes(number))
    );

    setRecommendedGroups(filtered);
    setShowRecommendedGroups(filtered.length > 0);
  };

  // 추천 단체 선택
  const selectRecommendedGroup = (group: any) => {
    setGroupName(group.name);
    setGroupType(group.type);
    setGroupNumber(group.number);
    setManagerName(group.managerName);
    setManagerEmail(group.managerEmail);
    setManagerPhone(group.managerPhone);
    setShowRecommendedGroups(false);
    setRecommendedGroups([]);
    
    setIsManagerEmailVerified(true);
    alert(`기존 등록 단체 "${group.name}"의 정보가 자동으로 입력되었습니다.`);
  };

  const handleGroupNameChange = (value: string) => {
    setGroupName(value);
    searchExistingGroups(value, groupNumber);
  };

  const handleGroupNumberChange = (value: string) => {
    setGroupNumber(value);
    searchExistingGroups(groupName, value);
  };

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

  // 이메일 인증 발송
  const sendEmailVerification = async () => {
    if (!managerEmail.trim()) {
      alert('담당자 이메일을 입력해주세요.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(managerEmail)) {
      alert('올바른 이메일 형식을 입력해주세요.');
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setIsEmailVerificationSent(true);
    setVerificationTimer(300);
    alert('인증번호가 이메일로 발송되었습니다. 5분 내에 입력해주세요.');

    const timer = setInterval(() => {
      setVerificationTimer(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          setIsEmailVerificationSent(false);
          setEmailVerificationCode('');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // 이메일 인증 확인
  const verifyEmail = async () => {
    if (!emailVerificationCode.trim()) {
      alert('인증번호를 입력해주세요.');
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 500));
    
    if (emailVerificationCode === '123456') {
      setIsManagerEmailVerified(true);
      setVerificationTimer(0);
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

  // 단체 기부 신청 함수 수정
  const handleGroupDonation = async () => {
    if (!groupName.trim()) {
      alert('단체명을 입력해주세요.');
      return;
    }

    if (!managerName.trim()) {
      alert('담당자명을 입력해주세요.');
      return;
    }

    if (!managerEmail.trim()) {
      alert('담당자 이메일을 입력해주세요.');
      return;
    }

    if (!managerPhone.trim()) {
      alert('담당자 연락처를 입력해주세요.');
      return;
    }

    if (!isManagerEmailVerified) {
      alert('이메일 인증을 완료해주세요.');
      return;
    }

    // 소방서 선택 검증
    if (donationMode === 'single') {
      if (!selectedFireStation) {
        alert('기부 대상 소방서를 선택해주세요.');
        return;
      }
    } else {
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

    // 정기 기부 선택 시 추가 검증
    if (isRegularDonation) {
      if (!startDate) {
        alert('시작일을 선택해주세요.');
        return;
      }

      try {
        const tossPayments = await loadTossPayments('test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq');

        const orderId = 'regular_' + Date.now();
        const orderName = donationMode === 'single' 
          ? `${selectedFireStation} 정기기부 (${regularCycles.find(c => c.value === regularCycle)?.label})`
          : `${selectedFireStations.length}개 소방서 정기기부 (${regularCycles.find(c => c.value === regularCycle)?.label})`;

        await tossPayments.requestBillingAuth('카드', {
          customerKey: 'customer_' + Date.now(),
          successUrl: `${window.location.origin}/payment/success?type=regular&orderId=${orderId}`,
          failUrl: `${window.location.origin}/payment/fail`,
        });

      } catch (error) {
        console.error('정기결제 등록 중 오류:', error);
        alert('정기결제 등록 중 오류가 발생했습니다. 다시 시도해주세요.');
      }
      return;
    }

    // 일반 단체 기부 - 토스페이먼트로 결제 처리
    try {
      let donationData;
      
      if (donationMode === 'single') {
        donationData = {
          mode: 'single',
          amount: getCurrentAmount(),
          cups: getCupCount(getCurrentAmount()),
          fireStation: selectedFireStation,
          groupName: groupName,
          groupType: groupType,
          groupNumber: groupNumber,
          managerName: managerName,
          managerEmail: managerEmail,
          managerPhone: managerPhone,
          message: message,
          needReceipt: needReceipt,
          isGroupAnonymous: isGroupAnonymous,
          donationType: 'group',
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
          groupName: groupName,
          groupType: groupType,
          groupNumber: groupNumber,
          managerName: managerName,
          managerEmail: managerEmail,
          managerPhone: managerPhone,
          message: message,
          needReceipt: needReceipt,
          isGroupAnonymous: isGroupAnonymous,
          donationType: 'group',
        };
      }

      console.log('단체 기부 데이터:', donationData);

      const tossPayments = await loadTossPayments('test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq');

      const orderId = 'group_' + Date.now();
      let orderName = '';
      
      if (donationMode === 'single') {
        orderName = `${selectedFireStation} 단체 기부 (${groupName}) - 커피 ${getCupCount(getCurrentAmount())}잔`;
      } else {
        orderName = `${selectedFireStations.length}개 소방서 ${multipleType === 'split' ? '분할' : multipleType === 'each' ? '각각' : '개별'} 단체 기부 (${groupName}) - 총 커피 ${getCupCount(donationData.amount)}잔`;
      }

      setShowPaymentMethodModal(true);

      setPaymentData({
        tossPayments,
        orderId,
        orderName,
        donationData,
      });
      
    } catch (error) {
      console.error('결제 요청 중 오류:', error);
      alert('결제 요청 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
  };

  // 결제 방법별 처리
  const handlePaymentMethod = async (method: string) => {
    try {
      const { tossPayments, orderId, orderName, donationData } = paymentData;

      const finalAmount = donationData.amount;
      const finalStationParam = donationMode === 'single' ? selectedFireStation : selectedFireStations.join(',');

      await tossPayments.requestPayment(method, {
        amount: finalAmount,
        orderId,
        orderName,
        customerName: donationData.managerName,
        customerEmail: donationData.managerEmail,
        successUrl: `${window.location.origin}/payment/success?type=group&orderId=${orderId}&amount=${finalAmount}&station=${encodeURIComponent(
          finalStationParam
        )}&groupName=${encodeURIComponent(donationData.groupName)}`,
        failUrl: `${window.location.origin}/payment/fail`,
        metadata: {
          fireStation: finalStationParam,
          groupName: donationData.groupName,
          groupType: donationData.groupType,
          groupNumber: donationData.groupNumber,
          managerName: donationData.managerName,
          managerEmail: donationData.managerEmail,
          managerPhone: donationData.managerPhone,
          message: message,
          needReceipt: needReceipt.toString(),
          cups: getCupCount(finalAmount).toString(),
          donationType: 'group',
          isGroupAnonymous: donationData.isGroupAnonymous.toString(),
          donationMode: donationMode,
          multipleType: donationMode === 'multiple' ? multipleType : '',
        },
      });
    } catch (error) {
      console.error('결제 요청 중 오류:', error);
      alert('결제 요청 중 오류가 발생했습니다. 다시 시도해주세요.');
    }

    setShowPaymentMethodModal(false);
  };

  return (
    <div className="bg-gray-50">
      {/* 히어로 섹션 */}
      <section
        className="relative h-[50vh] flex items-center justify-center bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.4)), url('https://readdy.ai/api/search-image?query=Corporate%20team%20donation%20concept%2C%20business%20partnership%20with%20firefighters%2C%20group%20giving%20and%20community%20support%2C%20professional%20office%20environment%20with%20donation%20documents%2C%20warm%20and%20trustworthy%20atmosphere%2C%20red%20and%20blue%20corporate%20colors&width=1920&height=800&seq=group-donation-hero&orientation=landscape')`,
        }}
      >
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-white">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            단체 기부 신청
          </h1>
          <p className="text-xl md:text-2xl text-gray-200 mb-8">
            기업, 기관, 단체에서 소방관들을 지원하는 기부를 신청하세요
          </p>
          <div className="flex items-center justify-center space-x-8 text-lg">
            <div className="flex items-center space-x-2">
              <i className="ri-building-fill text-blue-400 text-2xl"></i>
              <span>단체 기부</span>
            </div>
            <div className="flex items-center space-x-2">
              <i className="ri-calendar-check-fill text-green-400 text-2xl"></i>
              <span>정기 기부</span>
            </div>
            <div className="flex items-center space-x-2">
              <i className="ri-heart-fill text-red-400 text-2xl"></i>
              <span>지속적 나눔</span>
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="max-w-4xl mx-auto">
          <Card className="p-8">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-building-fill text-blue-600 text-3xl"></i>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">단체 기부 신청</h2>
              <p className="text-gray-600">
                기업, 기관, 단체에서 소방관들을 지원하는 기부를 신청하세요
              </p>
            </div>

            <div className="space-y-8">
              {/* 단체 정보 */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-6">단체 정보</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      단체 유형 <span className="text-red-500">*</span>
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {groupTypes.map((type) => (
                        <button
                          key={type.value}
                          onClick={() => setGroupType(type.value as any)}
                          className={`p-3 rounded-lg border-2 transition-all duration-200 ${
                            groupType === type.value
                              ? 'border-blue-500 bg-blue-50 text-blue-700'
                              : 'border-gray-200 hover:border-blue-300 text-gray-700'
                          }`}
                        >
                          {type.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="relative">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      단체명 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={groupName}
                      onChange={(e) => handleGroupNameChange(e.target.value)}
                      onFocus={() => {
                        if (recommendedGroups.length > 0) {
                          setShowRecommendedGroups(true);
                        }
                      }}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="단체명을 입력하세요"
                    />
                    
                    {/* 추천 단체 드롭다운 */}
                    {showRecommendedGroups && recommendedGroups.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                        <div className="px-4 py-2 bg-blue-50 border-b border-gray-100 text-sm font-medium text-blue-700">
                          <i className="ri-lightbulb-line mr-1"></i>
                          기존 등록 단체 (선택하면 정보가 자동 입력됩니다)
                        </div>
                        {recommendedGroups.map((group) => (
                          <button
                            key={group.id}
                            onClick={() => selectRecommendedGroup(group)}
                            className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors duration-200"
                          >
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="font-medium text-gray-900">{group.name}</div>
                                <div className="text-sm text-gray-500">
                                  {groupTypes.find(t => t.value === group.type)?.label}
                                  {group.number && ` • ${group.number}`}
                                </div>
                              </div>
                              <div className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                기존 등록
                              </div>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* 고유번호/사업자등록번호 입력 필드 추가 */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    고유번호/사업자등록번호 (선택사항)
                  </label>
                  <input
                    type="text"
                    value={groupNumber}
                    onChange={(e) => handleGroupNumberChange(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="사업자등록번호, 고유번호, 단체등록번호 등 (선택사항)"
                  />
                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-gray-500">
                      {groupType === 'company' && '사업자등록번호 (예: 123-45-67890)'}
                      {groupType === 'organization' && '고유번호 (예: 104-82-12345)'}
                      {groupType === 'group' && '단체등록번호나 고유식별번호 (없으면 비워두세요)'}
                    </p>
                    <div className="bg-amber-50 border border-amber-200 rounded p-3">
                      <div className="flex items-start space-x-2">
                        <i className="ri-alert-line text-amber-600 text-sm mt-0.5"></i>
                        <div className="text-xs text-amber-700">
                          <div className="font-medium mb-1">📋 세무상 중요한 안내사항</div>
                          <div className="space-y-1">
                            <div>• <strong>고유번호/사업자등록번호가 공란인 경우, 영수증을 발급받아도 국세청 신고 시 효력이 없습니다</strong></div>
                            <div>• 법인세법 및 소득세법에 따라 정확한 등록번호가 필요합니다</div>
                            <div>• 연말정산이나 종합소득세 신고 시 공제 불가능합니다</div>
                            <div>• 세무 문제 방지를 위해 정확한 번호 입력을 권장합니다</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 단체 익명 기부 옵션 */}
                <div className="bg-gray-50 p-4 rounded-lg mb-6">
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      id="isGroupAnonymous"
                      checked={isGroupAnonymous}
                      onChange={(e) => setIsGroupAnonymous(e.target.checked)}
                      className="w-5 h-5 text-gray-600 border-gray-300 rounded focus:ring-gray-500 mt-0.5"
                    />
                    <div>
                      <label
                        htmlFor="isGroupAnonymous"
                        className="text-gray-700 font-medium cursor-pointer"
                      >
                        익명으로 단체 기부하기
                      </label>
                      <p className="text-sm text-gray-600 mt-1">
                        체크 시 기부 랭킹과 화면에는 &quot;익명 단체&quot;로 표시되나, 영수증 발급 시에는 실제 단체명이 사용됩니다.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      담당자명 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={managerName}
                      onChange={(e) => setManagerName(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="담당자의 이름을 입력하세요"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      담당자 연락처 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="tel"
                      value={managerPhone}
                      onChange={(e) => setManagerPhone(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="연락가능한 전화번호를 입력하세요"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      담당자 이메일 <span className="text-red-500">*</span>
                    </label>
                    <div className="flex space-x-2">
                      <input
                        type="email"
                        value={managerEmail}
                        onChange={(e) => setManagerEmail(e.target.value)}
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="담당자의 이메일 주소를 입력하세요"
                      />
                      <Button
                        variant="primary"
                        size="medium"
                        onClick={sendEmailVerification}
                        disabled={isEmailVerificationSent || !managerEmail.trim()}
                      >
                        인증번호 발송
                      </Button>
                    </div>
                    
                    {/* 인증번호 입력 영역 */}
                    {(isEmailVerificationSent || isManagerEmailVerified) && (
                      <div className="mt-3">
                        <div className="flex space-x-2">
                          <input
                            type="text"
                            value={emailVerificationCode}
                            onChange={(e) => setEmailVerificationCode(e.target.value)}
                            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="받은 인증번호를 입력하세요"
                            disabled={isManagerEmailVerified}
                          />
                          {isEmailVerificationSent && !isManagerEmailVerified && (
                            <Button
                              variant="secondary"
                              size="medium"
                              onClick={verifyEmail}
                            >
                              확인
                            </Button>
                          )}
                        </div>
                        
                        {/* 인증 타이머 */}
                        {isEmailVerificationSent && !isManagerEmailVerified && (
                          <div className="mt-2 text-sm text-gray-600">
                            <span>인증 시간:</span>
                            <span className="ml-2 font-mono text-red-600">
                              {formatTimer(verificationTimer)}
                            </span>
                            {verificationTimer <= 0 && (
                              <span className="ml-2 text-red-500">
                                인증 시간이 만료되었습니다
                              </span>
                            )}
                          </div>
                        )}
                        
                        {/* 인증 완료 표시 */}
                        {isManagerEmailVerified && (
                          <div className="mt-2 flex items-center text-sm text-green-600">
                            <i className="ri-checkbox-circle-fill mr-1"></i>
                            이메일 인증이 완료되었습니다
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 기부 대상 소방서 선택 - 기부 페이지와 동일하게 수정 */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-6">기부 대상 소방서 선택</h3>
                
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
                          <div className="text-xs text-green-600 mt-1">예: 100,000원 → 5개 소방서 → 각각 20,000원</div>
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
                          <div className="text-xs text-green-600 mt-1">예: 100,000원 → 5개 소방서 → 총 500,000원</div>
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
                          <div className="text-xs text-green-600 mt-1">예: A소방서 50,000원, B소방서 100,000원, C소방서 30,000원</div>
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
                            <div className="text-green-700">{selectedFireStation}</div>
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
                        {getFilteredFireStations().map((station) => {
                          const todayDispatch = Math.floor(Math.random() * 15) + 1;
                          const todayFires = Math.floor(Math.random() * 5) + 1;
                          
                          return (
                            <button
                              key={station.id}
                              onClick={() => handleFireStationSelect(station.name)}
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
                                  min="3000"
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
                                  className="w-32 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-yellow-500"
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
                                  onChange={() => handleFireStationSelect(station.name)}
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

              {/* 기부 금액 선택 - custom 모드일 때 숨김 */}
              {!(donationMode === 'multiple' && multipleType === 'custom') && (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-6">기부 금액 선택</h3>
                  
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 mb-6">
                    {amounts.map((amount) => (
                      <button
                        key={amount.value}
                        onClick={() => handleAmountSelect(amount.value)}
                        className={`p-4 rounded-lg border-2 transition-all duration-200 text-center ${
                          selectedAmount === amount.value && !customAmount
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-blue-300'
                        }`}
                      >
                        <div className="text-lg font-semibold text-gray-900">
                          ₩{amount.value.toLocaleString()}
                        </div>
                        <div className="mt-1 text-sm text-gray-600">
                          {amount.label}
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          ☕ {amount.cups}잔
                        </div>
                      </button>
                    ))}
                  </div>

                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      직접 금액 입력
                    </label>
                    <div className="flex items-center space-x-3">
                      <input
                        type="text"
                        value={customAmount}
                        onChange={handleCustomAmountChange}
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="기부할 금액을 직접 입력하세요"
                      />
                      <div className="text-lg font-medium text-gray-900 whitespace-nowrap">
                        ☕ {getCupCount(getCurrentAmount())}잔 기부
                      </div>
                    </div>
                    <p className="mt-2 text-xs text-gray-500">
                      최소 기부 금액은 ₩3,000입니다.
                    </p>
                  </div>
                </div>
              )}

              {/* 정기 기부 설정 */}
              <div className="bg-blue-50 p-6 rounded-xl">
                <div className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    id="isRegularDonation"
                    checked={isRegularDonation}
                    onChange={(e) => setIsRegularDonation(e.target.checked)}
                    className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5"
                  />
                  <div className="flex-1">
                    <label
                      htmlFor="isRegularDonation"
                      className="text-gray-900 font-semibold cursor-pointer"
                    >
                      정기 기부를 원하시나요?
                    </label>
                    <p className="text-sm text-gray-600 mt-1">
                      동일한 금액을 정해진 주기로 자동으로 기부할 수 있습니다.
                    </p>
                    
                    {isRegularDonation && (
                      <div className="mt-4 space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            기부 주기
                          </label>
                          <div className="grid grid-cols-3 gap-2">
                            {regularCycles.map((cycle) => (
                              <button
                                key={cycle.value}
                                onClick={() => setRegularCycle(cycle.value as any)}
                                className={`p-3 rounded-lg border-2 transition-all duration-200 text-center ${
                                  regularCycle === cycle.value
                                    ? 'border-blue-500 bg-blue-500 text-white'
                                    : 'border-gray-200 hover:border-blue-300'
                                }`}
                              >
                                <div className="font-medium">{cycle.label}</div>
                                <div className="text-xs mt-1">{cycle.description}</div>
                              </button>
                            ))}
                          </div>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            시작일
                          </label>
                          <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            min={new Date().toISOString().split('T')[0]}
                            className="w-full md:w-auto px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <p className="mt-1 text-xs text-gray-500">
                            선택한 날짜부터 정기 기부가 시작됩니다
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 응원 메시지 */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-6">응원 메시지</h3>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="소방관들에게 전하고 싶은 응원 메시지를 입력하세요 (선택사항)"
                ></textarea>
                <p className="mt-1 text-xs text-gray-500">
                  응원 메시지는 기부 내역과 함께 소방관들에게 전달됩니다
                </p>
              </div>

              {/* 영수증 발급 여부 */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-6">영수증 발급</h3>
                
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">기부 영수증 발급 신청</div>
                      <div className="text-sm text-gray-600 mt-1">
                        기부 영수증은 다음 날 자동으로 발급됩니다.
                        {!needReceipt && (
                          <div className="mt-1 text-gray-500">
                            <span className="font-medium text-amber-600">⚠️ 경고:</span>&nbsp;
                            영수증 발급을 해제하면 국세청 신고 시 세금 공제가 불가능합니다.
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <button
                      onClick={() => setNeedReceipt(!needReceipt)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        needReceipt ? 'bg-blue-600' : 'bg-gray-300'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          needReceipt ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>

              {/* 기부 신청 버튼 */}
              <div className="pt-8">
                <Button
                  variant="primary"
                  size="large"
                  onClick={handleGroupDonation}
                  className="w-full py-4 text-lg font-semibold"
                  disabled={!groupName.trim() || !managerName.trim() || !managerEmail.trim() || !managerPhone.trim() || !isManagerEmailVerified || (donationMode === 'single' ? !selectedFireStation : selectedFireStations.length === 0)}
                >
                  기부 신청하기
                </Button>
                
                <p className="text-center text-sm text-gray-500 mt-4">
                  기부를 진행하시면{' '}
                  <a href="#" className="text-blue-600 hover:underline">
                    개인정보 수집 및 이용
                  </a>
                  에 동의하는 것으로 간주됩니다.
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* 소비자의 선택 방법 */}
        {showPaymentMethodModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <div className="text-center mb-6">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <i className="ri-credit-card-fill text-blue-600 text-xl"></i>
                </div>
                <h3 className="text-xl font-bold text-gray-900">결제 수단 선택</h3>
                <p className="text-gray-600 mt-1">
                  아래 결제 수단 중 하나를 선택해주세요
                </p>
              </div>

              <div className="space-y-3">
                <Button
                  variant="secondary"
                  size="large"
                  onClick={() => handlePaymentMethod('카드')}
                  className="w-full py-3 flex items-center justify-between"
                >
                  <div className="flex items-center space-x-2">
                    <i className="ri-bank-card-2-line text-blue-600 text-lg"></i>
                    <span>신용/체크카드</span>
                  </div>
                  <i className="ri-arrow-right-s-line text-gray-500"></i>
                </Button>

                <Button
                  variant="secondary"
                  size="large"
                  onClick={() => handlePaymentMethod('계좌이체')}
                  className="w-full py-3 flex items-center justify-between"
                >
                  <div className="flex items-center space-x-2">
                    <i className="ri-bank-line text-green-600 text-lg"></i>
                    <span>계좌이체</span>
                  </div>
                  <i className="ri-arrow-right-s-line text-gray-500"></i>
                </Button>
              </div>

              <Button
                variant="secondary"
                size="medium"
                onClick={() => setShowPaymentMethodModal(false)}
                className="w-full mt-6"
              >
                취소
              </Button>
            </div>
          </div>
        )}

        {/* 지역 선택 모달 */}
        {showRegionModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 w-full max-w-md max-h-[80vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-900">지역 선택</h3>
                <button
                  onClick={() => setShowRegionModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <i className="ri-close-line text-xl"></i>
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {regions.map((region) => (
                  <button
                    key={region}
                    onClick={() => handleRegionSelect(region)}
                    className={`p-3 rounded-lg border-2 transition-colors ${
                      selectedRegion === region
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-blue-300 text-gray-700'
                    }`}
                  >
                    {region}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 위치 기반 선택 모달 */}
        {showLocationModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <i className="ri-navigation-line text-green-500 text-3xl animate-pulse"></i>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">위치 확인 중</h3>
                <p className="text-gray-600 mb-6">현재 위치를 기반으로 주변 소방서를 찾고 있습니다...</p>
                
                {locationPermission === 'granted' && (
                  <div className="space-y-4">
                    <h4 className="font-semibold text-gray-900">주변 소방서</h4>
                    <div className="space-y-2">
                      {getNearbyFireStations().map((station) => (
                        <button
                          key={station.id}
                          onClick={() => {
                            handleFireStationSelect(station.name);
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
      </section>
    </div>
  );
}
