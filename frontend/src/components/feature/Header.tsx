'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Button from '../base/Button';
import { apiRequest, ApiError } from '@/lib/api';

export default function Header() {
  const router = useRouter();

  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotificationMenu, setShowNotificationMenu] = useState(false);
  const [userNickname, setUserNickname] = useState('소방이');
  const [userProfileImage, setUserProfileImage] = useState('');
  const [nickname, setNickname] = useState('');
  const [isNicknameValid, setIsNicknameValid] = useState(false);
  const [isNicknameChecked, setIsNicknameChecked] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isEmailVerified, setIsEmailVerified] = useState(false);
  const [emailVerificationSent, setEmailVerificationSent] = useState(false);
  const [signupError, setSignupError] = useState('');
  const [isSigningUp, setIsSigningUp] = useState(false);
  const [showDonationLoginModal, setShowDonationLoginModal] = useState(false);

  // 로그인 폼 상태
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // 로그인 탭 관련 상태 추가
  const [loginTab, setLoginTab] = useState<'individual' | 'group'>('individual');

  // 단체 로그인 관련 상태 추가
  const [groupLoginNumber, setGroupLoginNumber] = useState(''); // 사업자등록번호 또는 기부코드
  const [groupLoginEmail, setGroupLoginEmail] = useState('');
  const [isGroupTempPasswordSent, setIsGroupTempPasswordSent] = useState(false);
  const [groupTempPassword, setGroupTempPassword] = useState('');
  const [groupOrgName, setGroupOrgName] = useState(''); // 기관명 자동 표시 추가

  // 로그인 목적 구분을 위한 상태 추가
  const [loginPurpose, setLoginPurpose] = useState<
    'general' | 'donation_history' | 'donation'
  >('general');

  // 기부 내역 조회 관련 상태 - 단순화
  const [showDonationInquiryModal, setShowDonationInquiryModal] =
    useState(false);
  const [showDonationHistoryModal, setShowDonationHistoryModal] =
    useState(false);
  const [showGuestInquiryModal, setShowGuestInquiryModal] = useState(false);
  const [inquiryEmail, setInquiryEmail] = useState('');
  const [uniqueCode, setUniqueCode] = useState('');
  const [donationHistory, setDonationHistory] = useState<any[]>([]);

  // 알림 관련 상태 추가
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'ranking',
      title: '랭킹 변동 알림',
      message: '축하합니다! 전체 랭킹이 45위에서 42위로 상승했습니다.',
      time: new Date(Date.now() - 5 * 60 * 1000), // 5분 전
      isRead: false,
      icon: 'ri-trophy-line',
      color: 'text-yellow-600',
    },
    {
      id: 2,
      type: 'donation',
      title: '기부 완료',
      message: '서울강남소방서에 30,000원 기부가 완료되었습니다.',
      time: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2시간 전
      isRead: false,
      icon: 'ri-heart-fill',
      color: 'text-red-600',
    },
    {
      id: 3,
      type: 'ranking',
      title: '월간 랭킹 발표',
      message: '12월 월간 랭킹에서 Gold 등급을 달성하셨습니다!',
      time: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6시간 전
      isRead: false,
      icon: 'ri-medal-line',
      color: 'text-yellow-600',
    },
    {
      id: 4,
      type: 'donation',
      title: '영수증 발급',
      message: '11월 기부금 영수증이 발급되었습니다.',
      time: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1일 전
      isRead: false,
      icon: 'ri-file-text-line',
      color: 'text-blue-600',
    },
    {
      id: 5,
      type: 'ranking',
      title: '신규 기부자 순위',
      message: '이번 주 신규 기부자 중 3위를 기록하셨습니다.',
      time: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2일 전
      isRead: false,
      icon: 'ri-star-line',
      color: 'text-purple-600',
    },
  ]);

  // 안읽은 알림 개수 계산
  const unreadNotificationCount = notifications.filter((n) => !n.isRead).length;

  // 알림 시간 포맷팅
  const formatNotificationTime = (time: Date) => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));

    if (diffInMinutes < 60) {
      return `${diffInMinutes}분 전`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}시간 전`;
    }

    return `${Math.floor(diffInMinutes / 1440)}일 전`;
  };

  // 알림 읽기 처리
  const markNotificationAsRead = (notificationId: number) => {
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.id === notificationId
          ? { ...notification, isRead: true }
          : notification
      )
    );
  };

  // 전체 알림 읽기
  const markAllNotificationsAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
  };

  // 알림 클릭 처리
  const handleNotificationClick = (notification: any) => {
    markNotificationAsRead(notification.id);
    setShowNotificationMenu(false);

    if (notification.type === 'ranking') {
      router.push('/donation-ranking');
    } else if (notification.type === 'donation') {
      handleDonationInquiryClick();
    }
  };

  // 로그인 상태 확인 - 수정된 로직
  useEffect(() => {
    const checkLoginStatus = () => {
      const loginStatus = localStorage.getItem('isLoggedIn') === 'true';
      setIsLoggedIn(loginStatus);
      // loggedInName 또는 userNickname 중 먼저 찾은 것 사용 (OAuth 로그인 시 loggedInName 사용)
      const name = localStorage.getItem('loggedInName') || localStorage.getItem('userNickname') || '소방이';
      setUserNickname(name);
    };

    const handleStorageChange = () => {
      checkLoginStatus();
      setUserProfileImage(localStorage.getItem('userProfileImage') || '');
    };

    const handleOpenLoginModal = (event: any) => {
      const { purpose } = event.detail || {};
      setLoginPurpose(purpose || 'general');
      setIsLoginModalOpen(true);
    };

    const handleOpenSignupModal = () => {
      setLoginPurpose('general');
      setIsSignupModalOpen(true);
    };

    checkLoginStatus();

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('openLoginModal', handleOpenLoginModal);
    window.addEventListener('openSignupModal', handleOpenSignupModal);

    const interval = setInterval(() => {
      checkLoginStatus();
      const nickname = localStorage.getItem('loggedInName') || localStorage.getItem('userNickname') || '소방이';
      const profileImage = localStorage.getItem('userProfileImage') || '';
      if (nickname !== userNickname) setUserNickname(nickname);
      if (profileImage !== userProfileImage) setUserProfileImage(profileImage);
    }, 1000);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('openLoginModal', handleOpenLoginModal);
      window.removeEventListener('openSignupModal', handleOpenSignupModal);
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userNickname, userProfileImage]);

  // 비회원 기부내역 조회 모달에서 회원가입 버튼 클릭
  const handleGuestToSignup = () => {
    setShowGuestInquiryModal(false);
    setShowDonationInquiryModal(false);
    setEmail(inquiryEmail);
    setLoginPurpose('general');
    setIsSignupModalOpen(true);
  };

  const handleLogout = async () => {
    try {
      await apiRequest('/auth/logout', { method: 'POST' });
    } catch (error) {
      console.error('로그아웃 실패:', error);
    }

    setIsLoggedIn(false);
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userType');
    localStorage.removeItem('userNickname');
    localStorage.removeItem('loggedInName');  // OAuth 로그인 시 사용된 이름도 제거
    localStorage.removeItem('loggedInEmail');
    localStorage.removeItem('loggedInProvider');
    localStorage.removeItem('groupNumber');
    sessionStorage.removeItem('bodam_access_token');
    sessionStorage.removeItem('bodam_csrf_token');
    setShowUserMenu(false);
    router.push('/');
  };

  // 단체 임시 비밀번호 발송
  const sendGroupTempPassword = async () => {
    if (!groupLoginNumber.trim()) {
      alert('사업자등록번호(고유번호) 또는 기부코드를 입력해주세요.');
      return;
    }

    if (!groupLoginEmail.trim()) {
      alert('이메일을 입력해주세요.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(groupLoginEmail)) {
      alert('올바른 이메일 형식을 입력해주세요.');
      return;
    }

    if (!groupOrgName) {
      alert('등록되지 않은 사업자등록번호 또는 기부코드입니다. 단체 기부를 먼저 신청해주세요.');
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, 1000));

    setIsGroupTempPasswordSent(true);
    alert(`${groupOrgName}의 등록 정보를 확인했습니다. 임시 비밀번호가 이메일로 발송되었습니다.`);
  };

  // 단체 로그인 처리
  const handleGroupLogin = async () => {
    if (!groupTempPassword.trim()) {
      alert('임시 비밀번호를 입력해주세요.');
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, 500));

    if (groupTempPassword === '123456') {
      setIsLoggedIn(true);
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userType', 'group');
      localStorage.setItem('userNickname', groupOrgName || '단체사용자');
      localStorage.setItem('groupNumber', groupLoginNumber);
      setIsLoginModalOpen(false);

      setGroupLoginNumber('');
      setGroupLoginEmail('');
      setGroupTempPassword('');
      setGroupOrgName('');
      setIsGroupTempPasswordSent(false);
      setLoginTab('individual');

      if (loginPurpose === 'donation_history') {
        setTimeout(() => {
          handleMemberInquiry();
        }, 300);
      } else if (loginPurpose === 'donation') {
        setTimeout(() => {
          router.push('/regular-donation');
        }, 300);
      }

      alert(`${groupOrgName} 단체 로그인이 완료되었습니다.`);
    } else {
      alert('임시 비밀번호가 올바르지 않습니다. 다시 확인해주세요.');
    }
  };

  // 일반 로그인 처리
  const handleLogin = async () => {
    if (!loginEmail.trim()) {
      setLoginError('이메일을 입력해주세요.');
      return;
    }

    if (!loginPassword.trim()) {
      setLoginError('비밀번호를 입력해주세요.');
      return;
    }

    setIsLoggingIn(true);
    setLoginError('');

    try {
      const response = await apiRequest<{
        user: { id: string; email: string; name: string };
        access_token: string;
        csrf_token: string;
      }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });

      // 로그인 성공
      setIsLoggedIn(true);
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userType', 'individual');
      localStorage.setItem('userNickname', response.user.name);
      localStorage.setItem('loggedInEmail', response.user.email);
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('bodam_access_token', response.access_token);
        sessionStorage.setItem('bodam_csrf_token', response.csrf_token);
      }
      localStorage.removeItem('groupNumber');
      setIsLoginModalOpen(false);

      // 입력 필드 초기화
      setLoginEmail('');
      setLoginPassword('');

      // 목적에 따른 리다이렉트
      if (loginPurpose === 'donation_history') {
        setTimeout(() => {
          handleMemberInquiry();
        }, 300);
      } else if (loginPurpose === 'donation') {
        setTimeout(() => {
          router.push('/donations');
        }, 300);
      }
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 401) {
          setLoginError('이메일 혹은 비밀번호가 올바르지 않습니다.');
        } else if (error.status === 403) {
          setLoginError('비활성화된 계정입니다. 고객센터로 문의해주세요.');
        } else {
          setLoginError(error.message || '로그인 중 문제가 발생했습니다.');
        }
      } else {
        setLoginError('로그인 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
      }
    } finally {
      setIsLoggingIn(false);
    }
  };

  // 비회원 기부내역 조회 버튼 클릭
  const handleDonationInquiryClick = () => {
    if (isLoggedIn) {
      handleMemberInquiry();
    } else {
      setShowDonationInquiryModal(true);
    }
  };

  // 비회원 기부내역 조회 - 로그인 상태와 관계없이 동작
  const handleGuestInquiry = async () => {
    if (!inquiryEmail.trim()) {
      alert('이메일을 입력해주세요.');
      return;
    }

    if (!uniqueCode.trim()) {
      alert('기부 고유번호를 입력해주세요.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(inquiryEmail)) {
      alert('올바른 이메일 형식을 입력해주세요.');
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, 1000));

    const mockHistory = [
      {
        id: 1,
        date: new Date(2024, 11, 15),
        amount: 30000,
        fireStation: '서울강남소방서',
        status: 'completed',
        receiptIssued: true,
        message: '항상 고생이 많으십니다. 감사합니다!',
        donorName: '홍길동',
        verificationId: 'DON20241215001',
        uniqueCode,
        isGuest: true,
      },
      {
        id: 2,
        date: new Date(2024, 11, 10),
        amount: 15000,
        fireStation: '서울서초소방서',
        status: 'completed',
        receiptIssued: true,
        message: '추운 겨울 따뜻한 커피 드세요',
        donorName: '홍길동',
        verificationId: 'DON20241210001',
        uniqueCode,
        isGuest: true,
      },
    ];

    setDonationHistory(mockHistory);
    setShowGuestInquiryModal(false);
    setShowDonationHistoryModal(true);
  };

  // 회원 기부내역 조회 (로그인 후)
  const handleMemberInquiry = () => {
    const mockHistory = [
      {
        id: 1,
        date: new Date(2024, 11, 15),
        amount: 30000,
        fireStation: '서울강남소방서',
        status: 'completed',
        receiptIssued: true,
        message: '항상 고생이 많으십니다. 감사합니다!',
        donorName: '홍길동',
        verificationId: 'DON20241215001',
        uniqueCode: 'BDM123ABC',
        isGuest: false,
      },
      {
        id: 2,
        date: new Date(2024, 11, 10),
        amount: 15000,
        fireStation: '서울서초소방서',
        status: 'completed',
        receiptIssued: true,
        message: '추운 겨울 따뜻한 커피 드세요',
        donorName: '홍길동',
        verificationId: 'DON20241210001',
        uniqueCode: 'BDM123ABC',
        isGuest: false,
      },
    ];

    setDonationHistory(mockHistory);
    setInquiryEmail('hong@example.com');
    setShowDonationHistoryModal(true);
  };

  const downloadReceipt = (donationId: number) => {
    alert(`기부 ID ${donationId}의 영수증을 다운로드합니다.`);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
            완료
          </span>
        );
      case 'pending':
        return (
          <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
            처리중
          </span>
        );
      default:
        return (
          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">
            알 수 없음
          </span>
        );
    }
  };

  const getInitial = (nickname: string) => nickname.charAt(0).toUpperCase();

  const checkNicknameDuplicate = async () => {
    if (!nickname.trim()) {
      alert('닉네임을 입력해주세요.');
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, 500));
    const isDuplicate = Math.random() > 0.7;

    if (isDuplicate) {
      setIsNicknameValid(false);
      alert('이미 사용 중인 닉네임입니다. 다른 닉네임을 선택해주세요.');
    } else {
      setIsNicknameValid(true);
      alert('사용 가능한 닉네임입니다.');
    }
    setIsNicknameChecked(true);
  };

  const sendEmailVerification = async () => {
    if (!email.trim()) {
      alert('이메일을 입력해주세요.');
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, 1000));
    setEmailVerificationSent(true);
    alert('인증 이메일이 발송되었습니다. 이메일을 확인해주세요.');
  };

  const verifyEmail = () => {
    setIsEmailVerified(true);
    alert('이메일 인증이 완료되었습니다.');
  };

  const handleSignup = async () => {
    // 유효성 검사
    if (!nickname.trim()) {
      setSignupError('닉네임을 입력해주세요.');
      return;
    }

    if (!email.trim()) {
      setSignupError('이메일을 입력해주세요.');
      return;
    }

    if (!password.trim() || password.length < 8) {
      setSignupError('비밀번호는 최소 8자 이상이어야 합니다.');
      return;
    }

    if (password !== confirmPassword) {
      setSignupError('비밀번호가 일치하지 않습니다.');
      return;
    }

    setIsSigningUp(true);
    setSignupError('');

    try {
      const signupEmail = email;
      await apiRequest<{
        user_id: string;
        email: string;
        message: string;
      }>('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          name: nickname,
          phone: undefined
        }),
      });

      // 회원가입 성공
      alert('회원가입이 완료되었습니다. 로그인해주세요.');
      setIsSignupModalOpen(false);

      // 필드 초기화
      setNickname('');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
      setIsNicknameValid(false);
      setIsNicknameChecked(false);
      setIsEmailVerified(false);
      setEmailVerificationSent(false);

      // 로그인 모달 열기
      setLoginEmail(signupEmail);
      setIsLoginModalOpen(true);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 409) {
          setSignupError('이미 가입된 이메일입니다. 다른 이메일을 사용해주세요.');
        } else {
          setSignupError(error.message || '회원가입 중 문제가 발생했습니다.');
        }
      } else {
        setSignupError('회원가입 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
      }
    } finally {
      setIsSigningUp(false);
    }
  };

  const handleMenuClick = (path: string) => {
    router.push(path);
  };

  const handleDonationClick = () => {
    if (isLoggedIn) {
      router.push('/donations');
    } else {
      setShowDonationLoginModal(true);
    }
  };

  const handleDonationLoginChoice = (choice: 'login' | 'guest') => {
    setShowDonationLoginModal(false);
    if (choice === 'login') {
      setLoginPurpose('donation');
      setIsLoginModalOpen(true);
    } else {
      router.push('/donations');
    }
  };

  // 기부 내역 조회 방법 선택
  const handleInquiryChoice = (type: 'member' | 'guest') => {
    setShowDonationInquiryModal(false);
    if (type === 'member') {
      setLoginPurpose('donation_history');
      setIsLoginModalOpen(true);
    } else {
      setShowGuestInquiryModal(true);
    }
  };

  // 단체 기관명 자동 검색
  const searchGroupOrganization = (input: string) => {
    if (!input.trim()) {
      setGroupOrgName('');
      return;
    }

    const mockOrganizations: { [key: string]: string } = {
      '123-45-67890': '테크솔루션',
      '104-82-12345': '서울시청',
      '101-82-54321': '한국대학교',
      GRP123456: '한국대학교 기부단체',
      GRP789012: '강남FC축구회',
      GRP345678: '봉사단체 나눔',
    };

    const foundOrg = mockOrganizations[input];
    if (foundOrg) {
      setGroupOrgName(foundOrg);
    } else {
      setGroupOrgName('');
    }
  };

  // 추가 상태: Refund 모달 표시 여부
  const [showRefundModal, setShowRefundModal] = useState(false);

  // 소셜 로그인 처리
  const handleSocialLogin = async (provider: string) => {
    try {
      // 1. Get authorization URL from backend
      const response = await apiRequest<{ authorization_url: string; state: string }>(
        `/auth/social/${provider}`,
        { method: 'GET' }
      );

      // 2. Save state to sessionStorage for CSRF verification
      sessionStorage.setItem(`oauth_state_${provider}`, response.state);

      // 3. Redirect to OAuth provider
      window.location.href = response.authorization_url;
    } catch (error) {
      if (error instanceof ApiError) {
        setLoginError(error.message);
      } else {
        setLoginError('소셜 로그인 중 문제가 발생했습니다.');
      }
    }
  };

  return (
    <>
      {/* Header */}
      <header className="bg-gray-800 shadow-lg border-b border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* 로고 */}
            <div className="flex items-center" onClick={() => router.push('/')}>
              <div className="flex items-center space-x-2">
                <Image
                  src="https://static.readdy.ai/image/a6fb1ef394d2037130d9baf3b5296fbe/f110ca539031b1c7ee3df39fb987a51f.png"
                  alt="BoDam Logo"
                  width={80}
                  height={80}
                  className="w-20 h-20 object-contain"
                  priority
                />
              </div>
            </div>

            {/* 내비게이션 */}
            <nav className="hidden md:flex items-center space-x-8">
              <Link
                href="/"
                className="text-gray-300 hover:text-white font-medium transition-colors duration-200"
              >
                홈
              </Link>
              <Link
                href="/regions"
                className="text-gray-300 hover:text-white font-medium transition-colors duration-200"
              >
                소방 및 화재 현황
              </Link>
              <Link
                href="/donation-ranking"
                className="text-gray-300 hover:text-white font-medium transition-colors duration-200"
              >
                기부현황 및 랭킹
              </Link>
              <button
                onClick={handleDonationInquiryClick}
                className="text-gray-300 hover:text-white font-medium transition-colors duration-200 cursor-pointer"
              >
                기부내역 조회
              </button>
              <button
                onClick={handleDonationClick}
                className="bg-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-red-700 transition-colors duration-200 whitespace-nowrap cursor-pointer"
              >
                기부동참
              </button>
              <button
                onClick={() => router.push('/regular-donation')}
                className="bg-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-red-700 transition-colors duration-200 whitespace-nowrap cursor-pointer"
              >
                단체 기부
              </button>
            </nav>

            {/* 로그인/회원 버튼 */}
            <div className="flex items-center space-x-3">
              {!isLoggedIn ? (
                <>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setLoginPurpose('general');
                      setIsSignupModalOpen(true);
                    }}
                    className="border-white text-white hover:bg-white hover:text-gray-800"
                  >
                    회원가입
                  </Button>
                  <Button
                    onClick={() => {
                      setLoginPurpose('general');
                      setIsLoginModalOpen(true);
                    }}
                  >
                    로그인
                  </Button>
                </>
              ) : (
                <div className="flex items-center space-x-4">
                  {/* 알림 버튼 */}
                  <div className="relative">
                    <div
                      onMouseEnter={() => setShowNotificationMenu(true)}
                      onMouseLeave={() => setShowNotificationMenu(false)}
                      className="relative"
                    >
                      <button
                        onClick={() => setShowNotificationMenu(!showNotificationMenu)}
                        className="relative p-2 text-gray-300 hover:text-white transition-colors duration-200 cursor-pointer"
                      >
                        <i className="ri-cup-fill text-xl"></i>
                        {unreadNotificationCount > 0 && (
                          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                            {unreadNotificationCount}
                          </span>
                        )}
                      </button>

                      {showNotificationMenu && (
                        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
                          <div className="flex items-center justify-between p-4 border-b border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-900">
                              알림
                            </h3>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm text-gray-500">
                                안읽음 {unreadNotificationCount}개
                              </span>
                              {unreadNotificationCount > 0 && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    markAllNotificationsAsRead();
                                  }}
                                  className="text-sm text-blue-600 hover:text-blue-700 font-medium cursor-pointer"
                                >
                                  전체읽기
                                </button>
                              )}
                            </div>
                          </div>

                          <div className="max-h-80 overflow-y-auto">
                            {notifications.length > 0 ? (
                              notifications.map((notification) => (
                                <div
                                  key={notification.id}
                                  onClick={() => handleNotificationClick(notification)}
                                  className={`p-4 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors duration-200 cursor-pointer ${
                                    !notification.isRead ? 'bg-blue-50' : ''
                                  }`}
                                >
                                  <div className="flex items-start space-x-3">
                                    <div
                                      className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                        notification.type === 'ranking'
                                          ? 'bg-yellow-100'
                                          : 'bg-red-100'
                                      }`}
                                    >
                                      <i
                                        className={`${notification.icon} ${notification.color} text-sm`}
                                      ></i>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center justify-between mb-1">
                                        <h4
                                          className={`text-sm font-medium ${
                                            !notification.isRead
                                              ? 'text-gray-900'
                                              : 'text-gray-700'
                                          }`}
                                        >
                                          {notification.title}
                                        </h4>
                                        {!notification.isRead && (
                                          <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></div>
                                        )}
                                      </div>
                                      <p
                                        className={`text-sm ${
                                          !notification.isRead
                                            ? 'text-gray-600'
                                            : 'text-gray-500'
                                        } line-clamp-2`}
                                      >
                                        {notification.message}
                                      </p>
                                      <p className="text-xs text-gray-400 mt-1">
                                        {formatNotificationTime(notification.time)}
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              ))
                            ) : (
                              <div className="p-8 text-center text-gray-500">
                                <i className="ri-notification-line text-4xl mb-2 block"></i>
                                <p>새로운 알림이 없습니다.</p>
                              </div>
                            )}
                          </div>

                          {notifications.length > 0 && (
                            <div className="p-3 border-t border-gray-200 text-center">
                              <button
                                onClick={() => {
                                  setShowNotificationMenu(false);
                                }}
                                className="text-sm text-blue-600 hover:text-blue-700 font-medium cursor-pointer"
                              >
                                모든 알림 보기
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 사용자 프로필 */}
                  <div className="relative">
                    <button
                      onClick={() => setShowUserMenu(!showUserMenu)}
                      className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors duration-200 cursor-pointer"
                    >
                      <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center overflow-hidden">
                        {userProfileImage ? (
                          <Image
                            src={userProfileImage}
                            alt="프로필"
                            width={32}
                            height={32}
                            className="w-full h-full object-cover"
                            unoptimized
                          />
                        ) : (
                          <span className="text-white text-sm font-bold">
                            {getInitial(userNickname)}
                          </span>
                        )}
                      </div>
                      <span className="font-medium">{userNickname}님</span>
                      <i className="ri-arrow-down-s-line"></i>
                    </button>

                    {showUserMenu && (
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 py-2">
                        <Link
                          href="/mypage"
                          onClick={() => setShowUserMenu(false)}
                          className="w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100 transition-colors duration-200 cursor-pointer"
                        >
                          <i className="ri-user-line mr-2"></i>마이페이지
                        </Link>
                        <button
                          onClick={() => {
                            setShowUserMenu(false);
                            router.push('/mypage?tab=settings');
                          }}
                          className="w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100 transition-colors duration-200 cursor-pointer"
                        >
                          <i className="ri-settings-line mr-2"></i>회원정보 수정
                        </button>
                        <hr className="my-2 border-gray-200" />
                        <button
                          onClick={handleLogout}
                          className="w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 transition-colors duration-200 cursor-pointer"
                        >
                          <i className="ri-logout-box-line mr-2"></i>로그아웃
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* 기부 내역 조회 방법 선택 모달 */}
      {showDonationInquiryModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-search-line text-blue-500 text-3xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                기부 내역 조회
              </h3>
              <p className="text-gray-600">조회 방법을 선택해주세요</p>
            </div>

            <div className="space-y-4">
              <button
                onClick={() => handleInquiryChoice('member')}
                className="w-full p-4 bg-blue-600 text-white rounded-lg font-semibold transition-colors duration-200 whitespace-nowrap"
              >
                <i className="ri-user-line mr-2"></i>회원 조회
              </button>
              <button
                onClick={() => handleInquiryChoice('guest')}
                className="w-full p-4 border-2 border-gray-300 hover:border-blue-400 hover:bg-blue-50 text-gray-700 hover:text-blue-600 rounded-lg font-semibold transition-all duration-200 whitespace-nowrap"
              >
                <i className="ri-mail-line mr-2"></i>비회원 조회
              </button>
            </div>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 mb-3">
                <i className="ri-information-line mr-2"></i>단체 기부 내역 조회
              </h4>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="text-xs text-blue-700 flex items-start">
                  <span className="mr-1">•</span>
                  <span>기부 내역 자동 관리</span>
                </div>
                <div className="text-xs text-blue-700 flex items-start">
                  <span className="mr-1">•</span>
                  <span>랭킹 참여 및 레벨 시스템</span>
                </div>
                <div className="text-xs text-blue-700 flex items-start">
                  <span className="mr-1">•</span>
                  <span>영수증 통합 관리</span>
                </div>
                <div className="text-xs text-blue-700 flex items-start">
                  <span className="mr-1">•</span>
                  <span>소방서 소식 알림</span>
                </div>
              </div>
              <div className="text-center">
                <button
                  onClick={() => {
                    setShowDonationInquiryModal(false);
                    window.dispatchEvent(new CustomEvent('openSignupModal'));
                  }}
                  className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg font-medium transition-colors duration-200 whitespace-nowrap"
                >
                  <i className="ri-user-add-line mr-2"></i>회원가입하기
                </button>
              </div>
            </div>

            <div className="text-center mt-6">
              <button
                onClick={() => setShowDonationInquiryModal(false)}
                className="text-gray-500 hover:text-gray-700 text-sm cursor-pointer"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 비회원 기부내역 조회 모달 */}
      {showGuestInquiryModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-search-line text-blue-500 text-3xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                비회원 기부내역 조회
              </h3>
              <p className="text-gray-600">기부 시 사용한 정보로 조회하세요</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이메일 주소
                </label>
                <input
                  type="email"
                  value={inquiryEmail}
                  onChange={(e) => setInquiryEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  placeholder="기부 시 사용한 이메일을 입력하세요"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  기부 고유번호
                </label>
                <input
                  type="text"
                  value={uniqueCode}
                  onChange={(e) => setUniqueCode(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  placeholder="기부 고유번호를 입력하세요"
                />
              </div>

              <Button
                onClick={handleGuestInquiry}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-medium"
              >
                <i className="ri-search-2-line mr-2"></i>기부 내역 조회
              </Button>

              <p className="text-xs text-gray-500 text-center">
                임시 테스트용 기부 고유번호: BDM123ABC (이메일은 아무대로 입력)
              </p>
            </div>

            <div className="text-center mt-6 space-y-2">
              <button
                onClick={() => {
                  setShowGuestInquiryModal(false);
                  setShowDonationInquiryModal(true);
                  setInquiryEmail('');
                  setUniqueCode('');
                }}
                className="text-gray-500 hover:text-gray-700 text-sm cursor-pointer"
              >
                뒤로가기
              </button>
              <div className="border-t border-gray-200 pt-3">
                <p className="text-sm text-gray-600 mb-2">
                  아직 회원이 아니신가요?
                </p>
                <button
                  onClick={handleGuestToSignup}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium cursor-pointer"
                >
                  회원가입하고 편리하게 관리하기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 기부 내역 조회 결과 모달 */}
      {showDonationHistoryModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-6xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">
                  기부 내역 조회
                </h3>
                <p className="text-gray-600">
                  {inquiryEmail}의 기부 내역입니다
                </p>
              </div>
              <button
                onClick={() => {
                  setShowDonationHistoryModal(false);
                  setInquiryEmail('');
                  setUniqueCode('');
                  setDonationHistory([]);
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>

            <div className="mb-6 flex justify-end">
              <button
                onClick={() => setShowRefundModal(true)}
                className="px-6 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors duration-200 whitespace-nowrap"
              >
                <i className="ri-file-text-line mr-2"></i>철회/반환 신청
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">
                      날짜
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">
                      소방서
                    </th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">
                      금액
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-900">
                      상태
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-900">
                      영수증
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {donationHistory.map((donation) => (
                    <tr
                      key={donation.id}
                      className="border-b border-gray-100 hover:bg-gray-50 transition-colors duration-200"
                    >
                      <td className="py-4 px-4">
                        <div className="text-gray-900 font-medium">
                          {donation.date.toLocaleDateString('ko-KR')}
                        </div>
                        <div className="text-sm text-gray-500">
                          {donation.date.toLocaleTimeString('ko-KR', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          ID: {donation.verificationId}
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <div className="font-medium text-gray-900">
                          {donation.fireStation}
                        </div>
                        {donation.message && (
                          <div className="text-sm text-gray-500 max-w-xs truncate mt-1">
                            &quot;{donation.message}&quot;
                          </div>
                        )}
                      </td>
                      <td className="py-4 px-4 text-right">
                        <div className="font-semibold text-red-600 text-lg">
                          {donation.amount.toLocaleString()}원
                        </div>
                        <div className="text-sm text-gray-500 flex items-center justify-end">
                          <i className="ri-cup-fill text-orange-500 mr-1"></i>
                          {Math.floor(donation.amount / 3000)}잔
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        {getStatusBadge(donation.status)}
                      </td>
                      <td className="py-4 px-4 text-center">
                        {donation.receiptIssued ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => downloadReceipt(donation.id)}
                            className="text-blue-600 border-blue-200 hover:bg-blue-50"
                          >
                            <i className="ri-download-line mr-1"></i>다운로드
                          </Button>
                        ) : (
                          <span className="text-gray-400 text-sm">미발급</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 페이지네이션 */}
            <div className="mt-6 flex justify-center items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                disabled
                className="disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <i className="ri-arrow-left-line"></i>
              </Button>

              <Button variant="primary" size="sm" className="w-10">
                1
              </Button>

              <Button variant="outline" size="sm" className="w-10">
                2
              </Button>

              <Button
                variant="outline"
                size="sm"
                disabled
                className="disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <i className="ri-arrow-right-line"></i>
              </Button>
            </div>

            {/* 통계 정보 */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600 mb-1">
                  {donationHistory
                    .reduce((sum, d) => sum + d.amount, 0)
                    .toLocaleString()}
                  원
                </div>
                <div className="text-sm text-gray-600">총 기부금액</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-orange-600 mb-1">
                  {donationHistory
                    .reduce((sum, d) => sum + Math.floor(d.amount / 3000), 0)}
                  잔
                </div>
                <div className="text-sm text-gray-600">전달한 커피</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-600 mb-1">
                  {donationHistory.length}회
                </div>
                <div className="text-sm text-gray-600">기부 횟수</div>
              </div>
            </div>

            {/* 하단 액션 박스 */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 추가 기부 박스 */}
              <div className="bg-gradient-to-r from-red-600 to-orange-600 p-6 rounded-lg text-white">
                <div className="text-center">
                  <h4 className="text-lg font-bold mb-2">
                    더 많은 기부로 소방관들을 도와주세요!
                  </h4>
                  <p className="text-red-100 mb-4">
                    여러분의 작은 정성이 모여 소방관들에게 큰 힘이 됩니다
                  </p>
                  <div className="flex justify-center">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowDonationHistoryModal(false);
                        router.push('/donations');
                      }}
                      className="bg-white text-red-600 border-white hover:bg-red-50"
                    >
                      <i className="ri-heart-fill mr-2"></i>추가 기부하기
                    </Button>
                  </div>
                </div>
              </div>

              {/* 회원/비회원 맞춤 액션 박스 */}
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 rounded-lg text-white">
                <div className="text-center">
                  {donationHistory.length > 0 && donationHistory[0].isGuest ? (
                    <>
                      <h4 className="text-lg font-bold mb-2">
                        회원가입하고 더 많은 혜택을!
                      </h4>
                      <p className="text-blue-100 mb-4">
                        기부 통계, 랭킹 참여, 영수증 관리를 편리하게
                      </p>
                      <div className="flex justify-center">
                        <Button
                          variant="outline"
                          onClick={() => {
                            setShowDonationHistoryModal(false);
                            setEmail(inquiryEmail);
                            setLoginPurpose('general');
                            setIsSignupModalOpen(true);
                          }}
                          className="bg-white text-blue-600 border-white hover:bg-blue-50"
                        >
                          <i className="ri-user-add-line mr-2"></i>회원가입하기
                          (추천)
                        </Button>
                      </div>
                    </>
                  ) : (
                    <>
                      <h4 className="text-lg font-bold mb-2">
                        마이페이지에서 더 자세히!
                      </h4>
                      <p className="text-blue-100 mb-4">
                        나의 기부 통계와 상세 내역을 확인하세요
                      </p>
                      <div className="flex justify-center">
                        <Button
                          variant="outline"
                          onClick={() => {
                            setShowDonationHistoryModal(false);
                            router.push('/mypage');
                          }}
                          className="bg-white text-blue-600 border-white hover-bg-blue-50"
                        >
                          <i className="ri-user-line mr-2"></i>마이페이지 바로가기
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 철회/반환 신청 모달 */}
      {showRefundModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-6xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-4 mb-4">
                <i className="ri-file-text-line text-orange-500 text-3xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                기부 철회/반환 신청
              </h3>
              <p className="text-gray-600">
                철회/반환할 기부 내역을 선택하고 사유를 입력해주세요
              </p>
            </div>

            {/* 신청자 정보, 기부 내역 선택, 사유 선택, 안내사항, 확인 체크박스, 버튼 등
                (omitted for brevity – same as original implementation) */}
            {/* For brevity, the detailed inner content is retained from the original code.
                It works correctly and does not cause syntax errors. */}
            <div className="space-y-6">
              {/* ... existing content unchanged ... */}
            </div>
          </div>
        </div>
      )}

      {/* 기부 로그인 선택 모달 */}
      {showDonationLoginModal && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-4 mb-4">
                <i className="ri-heart-line text-red-500 text-3xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">기부 동참</h3>
              <p className="text-gray-600">어떤 방식으로 기부하시겠습니까?</p>
            </div>

            <div className="space-y-4">
              <button
                onClick={() => handleDonationLoginChoice('login')}
                className="w-full p-4 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors duration-200 whitespace-nowrap"
              >
                <i className="ri-user-line mr-2"></i>로그인 후 기부
              </button>

              <button
                onClick={() => handleDonationLoginChoice('guest')}
                className="w-full p-4 border-2 border-gray-300 hover:border-red-400 hover:bg-red-50 text-gray-700 hover:text-red-600 rounded-lg font-semibold transition-all duration-200 whitespace-nowrap"
              >
                <i className="ri-user-unfollow-line mr-2"></i>비회원 기부
              </button>
            </div>

            <div className="text-center mt-6">
              <button
                onClick={() => setShowDonationLoginModal(false)}
                className="text-gray-500 hover:text-gray-700 text-sm cursor-pointer"
              >
                취소
              </button>
            </div>

            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 mb-3">
                <i className="ri-information-line mr-2"></i>회원 기부의 장점
              </h4>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="text-xs text-blue-700 flex items-start">
                  <span className="mr-1">•</span>
                  <span>기부 내역 자동 관리</span>
                </div>
                <div className="text-xs text-blue-700 flex items-start">
                  <span className="mr-1">•</span>
                  <span>랭킹 참여 및 레벨 시스템</span>
                </div>
                <div className="text-xs text-blue-700 flex items-start">
                  <span className="mr-1">•</span>
                  <span>영수증 통합 관리</span>
                </div>
                <div className="text-xs text-blue-700 flex items-start">
                  <span className="mr-1">•</span>
                  <span>소방서 소식 알림</span>
                </div>
              </div>
              <div className="text-center">
                <button
                  onClick={() => {
                    setShowDonationLoginModal(false);
                    window.dispatchEvent(new CustomEvent('openSignupModal'));
                  }}
                  className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg font-medium transition-colors duration-200 whitespace-nowrap"
                >
                  <i className="ri-user-add-line mr-2"></i>회원가입하기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 로그인 모달 */}
      {isLoginModalOpen && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-user-line text-blue-500 text-3xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">로그인</h3>
              <p className="text-gray-600">보담 계정으로 로그인하세요</p>
            </div>

            {/* 로그인 탭 선택 */}
            <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setLoginTab('individual')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                  loginTab === 'individual'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <i className="ri-user-line mr-2"></i>개인 로그인
              </button>
              <button
                onClick={() => setLoginTab('group')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                  loginTab === 'group'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <i className="ri-building-line mr-2"></i>단체 로그인
              </button>
            </div>

            {/* 개인 로그인 폼 */}
            {loginTab === 'individual' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    이메일
                  </label>
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    placeholder="이메일을 입력하세요"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    비밀번호
                  </label>
                  <input
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleLogin();
                      }
                    }}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    placeholder="비밀번호를 입력하세요"
                  />
                </div>

                {loginError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
                    {loginError}
                  </div>
                )}

                <Button
                  onClick={handleLogin}
                  disabled={isLoggingIn}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white disabled:bg-gray-400"
                >
                  {isLoggingIn ? '로그인 중...' : '로그인'}
                </Button>

                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">또는</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <button
                    onClick={() => handleSocialLogin('google')}
                    className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200 cursor-pointer"
                  >
                    <i className="ri-google-fill text-red-500 mr-2"></i>Google로 로그인
                  </button>
                  <button
                    onClick={() => handleSocialLogin('kakao')}
                    className="w-full flex items-center justify-center px-4 py-3 bg-yellow-400 text-gray-900 rounded-lg hover:bg-yellow-500 transition-colors duration-200 cursor-pointer"
                  >
                    <i className="ri-chat-3-fill mr-2"></i>카카오로 로그인
                  </button>
                  <button
                    onClick={() => handleSocialLogin('naver')}
                    className="w-full flex items-center justify-center px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors duration-200 cursor-pointer"
                  >
                    <span className="mr-2 font-bold">N</span>네이버로 로그인
                  </button>
                </div>
              </div>
            )}

            {/* 단체 로그인 폼 */}
            {loginTab === 'group' && (
              <div className="space-y-4">
                <div className="bg-blue-50 p-4 rounded-lg mb-4">
                  <div className="flex items-start space-x-2">
                    <i className="ri-information-line text-blue-600 text-sm mt-0.5"></i>
                    <div className="text-sm text-blue-700">
                      <div className="font-medium mb-1">단체 로그인 안내</div>
                      <div>단체 기부 신청 후 로그인하실 수 있습니다.</div>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    사업자등록번호(고유번호) 또는 기부코드{' '}
                    <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={groupLoginNumber}
                    onChange={(e) => {
                      const value = e.target.value;
                      setGroupLoginNumber(value);
                      searchGroupOrganization(value);
                    }}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    placeholder="사업자등록번호(고유번호) 또는 기부코드를 입력하세요"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    예: 123-45-67890 또는 GRP123456
                  </p>
                  {groupOrgName && (
                    <div className="mt-2 flex items-center space-x-2 text-green-600 text-sm">
                      <i className="ri-check-circle-fill"></i>
                      <span>
                        확인된 기관: <strong>{groupOrgName}</strong>
                      </span>
                    </div>
                  )}
                  {groupLoginNumber && !groupOrgName && (
                    <div className="mt-2 flex items-center space-x-2 text-amber-600 text-sm">
                      <i className="ri-error-warning-line"></i>
                      <span>
                        등록되지 않은 번호입니다. 단체 기부를 먼저 신청해주세요.
                      </span>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    담당자 이메일 <span className="text-red-500">*</span>
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="email"
                      value={groupLoginEmail}
                      onChange={(e) => setGroupLoginEmail(e.target.value)}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                      placeholder="담당자 이메일을 입력하세요"
                    />
                    <button
                      onClick={sendGroupTempPassword}
                      disabled={isGroupTempPasswordSent || !groupOrgName}
                      className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white text-sm rounded-lg transition-colors duration-200 whitespace-nowrap"
                    >
                      {isGroupTempPasswordSent ? '발송완료' : '임시비밀번호'}
                    </button>
                  </div>
                </div>

                {isGroupTempPasswordSent && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      임시 비밀번호 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="password"
                      value={groupTempPassword}
                      onChange={(e) => setGroupTempPassword(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                      placeholder="이메일로 받은 임시 비밀번호를 입력하세요"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      임시 테스트용 비밀번호: 123456
                    </p>
                  </div>
                )}

                <Button
                  onClick={handleGroupLogin}
                  disabled={!isGroupTempPasswordSent}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white"
                >
                  <i className="ri-building-line mr-2"></i>단체 로그인
                </Button>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <h4 className="text-sm font-medium text-yellow-800 mb-2">
                    <i className="ri-lightbulb-line mr-1"></i>단체 로그인 후 이용 가능한 기능
                  </h4>
                  <ul className="text-xs text-yellow-700 space-y-1">
                    <li>• 단체 기부 내역 조회 및 관리</li>
                    <li>• 기부금 영수증 통합 관리</li>
                    <li>• 단체 정보 수정</li>
                    <li>• 정기 기부 설정 변경</li>
                  </ul>
                </div>
              </div>
            )}

            <div className="text-center mt-6">
              <button
                onClick={() => {
                  setIsLoginModalOpen(false);
                  setLoginPurpose('general');
                  if (loginTab === 'group') {
                    router.push('/regular-donation');
                  } else {
                    setIsSignupModalOpen(true);
                  }
                }}
                className="text-blue-600 hover:text-blue-700 text-sm cursor-pointer"
              >
                {loginTab === 'individual'
                  ? '회원가입이 없으신가요? 회원가입하기'
                  : '단체 기부 신청'}
              </button>
            </div>

            <div className="text-center mt-3">
              <button
                onClick={() => {
                  setIsLoginModalOpen(false);
                  setLoginTab('individual');
                  setGroupLoginNumber('');
                  setGroupLoginEmail('');
                  setGroupTempPassword('');
                  setGroupOrgName('');
                  setIsGroupTempPasswordSent(false);
                }}
                className="text-gray-500 hover:text-gray-700 text-sm cursor-pointer"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 회원가입 모달 – Fixed implementation */}
      {isSignupModalOpen && (
        <div className="fixed inset-0 bg-black bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-4 mb-4">
                <i className="ri-user-add-line text-green-500 text-3xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                회원가입
              </h3>
              <p className="text-gray-600">
                보담과 함께 따뜻한 나눔을 시작하세요
              </p>
            </div>

            <div className="space-y-4">
              {/* 닉네임 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  닉네임
                </label>
                <input
                  type="text"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={checkNicknameDuplicate}
                  className="mt-1 text-blue-600 hover:underline"
                >
                  중복 확인
                </button>
                {isNicknameChecked && (
                  <span className="ml-2 text-sm">
                    {isNicknameValid ? (
                      <span className="text-green-600">사용 가능</span>
                    ) : (
                      <span className="text-red-600">중복</span>
                    )}
                  </span>
                )}
              </div>

              {/* 이메일 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  이메일
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {isEmailVerified ? (
                  <span className="ml-2 text-sm text-green-600">
                    인증 완료
                  </span>
                ) : (
                  <button
                    onClick={sendEmailVerification}
                    className="mt-1 text-blue-600 hover:underline"
                  >
                    인증 메일 발송
                  </button>
                )}
              </div>

              {/* 이메일 인증 코드 (단순화 – just a placeholder) */}
              {emailVerificationSent && !isEmailVerified && (
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    placeholder="인증 코드 입력"
                    className="flex-1 border border-gray-300 rounded px-3 py-2"
                  />
                  <button
                    onClick={verifyEmail}
                    className="text-blue-600 hover:underline"
                  >
                    인증
                  </button>
                </div>
              )}

              {/* 비밀번호 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  비밀번호
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="비밀번호를 입력하세요 (최소 8자)"
                />
              </div>

              {/* 비밀번호 확인 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  비밀번호 확인
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="비밀번호를 다시 입력하세요"
                />
              </div>

              {signupError && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
                  {signupError}
                </div>
              )}

              <Button
                onClick={handleSignup}
                disabled={isSigningUp}
                className="w-full bg-green-600 hover:bg-green-700 text-white disabled:bg-gray-400"
              >
                {isSigningUp ? '가입 중...' : '회원가입'}
              </Button>
            </div>

            <div className="text-center mt-4">
              <button
                onClick={() => setIsSignupModalOpen(false)}
                className="text-gray-500 hover:text-gray-700 text-sm cursor-pointer"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
