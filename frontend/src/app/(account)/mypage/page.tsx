'use client';

import { ChangeEvent, useEffect, useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';
import { apiRequest, ApiError } from '@/lib/api';

export default function MyPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'donations' | 'regular' | 'profile' | 'settings'>('donations');
  const [currentPage, setCurrentPage] = useState(1);
  const [showWithdrawalModal, setShowWithdrawalModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showProfileEditModal, setShowProfileEditModal] = useState(false);
  const [showDonationHistoryModal, setShowDonationHistoryModal] = useState(false);
  const [showRegularCancelModal, setShowRegularCancelModal] = useState(false);
  const [selectedRegularDonation, setSelectedRegularDonation] = useState<any>(null);
  const [withdrawalReason, setWithdrawalReason] = useState('');
  const [withdrawalCategory, setWithdrawalCategory] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState<'individual' | 'group'>('individual');
  const [groupNumber, setGroupNumber] = useState('');
  // 철회/반환 신청 관련 상태 추가
  const [showRefundModal, setShowRefundModal] = useState(false);
  const [refundReason, setRefundReason] = useState('');
  const [refundCategory, setRefundCategory] = useState('');
  const [refundCustomReason, setRefundCustomReason] = useState('');
  const [isRefundConfirmed, setIsRefundConfirmed] = useState(false);
  const [showRefundCompleteModal, setShowRefundCompleteModal] = useState(false);
  // 기부 내역 선택 관련 상태 추가
  const [selectedDonations, setSelectedDonations] = useState<Set<number>>(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '홍길동',
    nickname: '소방이',
    email: 'hong@example.com',
    phone: '010-1234-5678',
    idNumber: '',
    newEmail: '',
    newPhone: '',
    newIdNumber: '',
    verificationCode: '',
    isCodeSent: false,
    isVerified: false
  });
  const [profileImage, setProfileImage] = useState<File | null>(null);
  const [profileImagePreview, setProfileImagePreview] = useState<string>('');
  const [itemsPerPage] = useState(10);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [selectedDonation, setSelectedDonation] = useState<any>(null);
  const [selectedWithdrawType, setSelectedWithdrawType] = useState<'individual' | 'group'>('individual');

  // 철회/반환 모달 상태 추가
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);

  // API 데이터 상태
  const [donationHistory, setDonationHistory] = useState<any[]>([]);
  const [regularDonations, setRegularDonations] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 월별 통계 계산
  const monthlyStats = donationHistory.reduce((acc: any[], donation) => {
    const month = new Date(donation.created_at || donation.date).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long' });
    const existing = acc.find(s => s.month === month);
    const amount = Number(donation.amount) || 0;

    if (existing) {
      existing.amount += amount;
      existing.count += 1;
      existing.cups += Math.floor(amount / 3000);
    } else {
      acc.push({
        month,
        amount: amount,
        count: 1,
        cups: Math.floor(amount / 3000)
      });
    }

    return acc;
  }, []).slice(0, 10);

  // URL 파라미터 확인하여 기부내역 모달 표시
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('showDonationHistory') === 'true') {
      setShowDonationHistoryModal(true);
      // URL에서 파라미터 제거
      window.history.replaceState({}, '', '/mypage');
    }
    
    // 프로필 관리 탭으로 직접 이동하는 경우
    if (urlParams.get('tab') === 'settings') {
      setActiveTab('settings');
      // URL에서 파라미터 제거
      window.history.replaceState({}, '', '/mypage');
    }

    // 사용자 타입과 단체 정보 업데이트
    const storedUserTypeRaw = localStorage.getItem('userType');
    const storedUserType: 'individual' | 'group' =
      storedUserTypeRaw === 'group' ? 'group' : 'individual';
    const storedGroupNumber = localStorage.getItem('groupNumber') || '';
    const storedUserNickname = localStorage.getItem('userNickname') || '소방이';

    setUserType(storedUserType);
    setGroupNumber(storedGroupNumber);
    
    // 단체 로그인인 경우 사용자 정보를 단체 정보로 업데이트
    if (storedUserType === 'group') {
      setUserInfo(prev => ({
        ...prev,
        name: storedUserNickname, // 단체명으로 설정
        nickname: storedUserNickname,
        profileImage: '' // 단체는 프로필 이미지 없음
      }));
    }
  }, []);

  const withdrawalOptions = [
    { value: 'low_usage', label: '서비스 이용 빈도 낮음' },
    { value: 'other_platform', label: '다른 기부 플랫폼 이용' },
    { value: 'privacy_concern', label: '개인정보 보호 우려' },
    { value: 'service_quality', label: '서비스 품질 불만족' },
    { value: 'donation_method', label: '기부 방식의 변화' },
    { value: 'financial_reason', label: '경제적 사정 변화' },
    { value: 'other', label: '기타' }
  ];

  // 철회/반환 사유 옵션 - 개인용과 단체용으로 분리
  const individualRefundReasons = [
    { value: 'personal_circumstance', label: '개인 사정 변화' },
    { value: 'donation_mistake', label: '잘못된 기부 (실수로 잘못 기부한 경우)' },
    { value: 'duplicate_donation', label: '중복 기부' },
    { value: 'family_objection', label: '가족 반대' },
    { value: 'economic_difficulty', label: '경제적 어려움' },
    { value: 'service_dissatisfaction', label: '서비스 불만족' },
    { value: 'medical_emergency', label: '의료비 등 긴급 상황' },
    { value: 'other', label: '기타' }
  ];

  const groupRefundReasons = [
    { value: 'budget_change', label: '단체 예산 변경' },
    { value: 'policy_change', label: '단체 기부 정책 변경' },
    { value: 'management_decision', label: '경영진/이사회 결정' },
    { value: 'donation_mistake', label: '잘못된 기부 (실수로 잘못 기부한 경우)' },
    { value: 'duplicate_donation', label: '중복 기부' },
    { value: 'financial_difficulty', label: '단체 재정상황 악화' },
    { value: 'project_cancellation', label: '관련 프로젝트 취소' },
    { value: 'legal_issue', label: '법적 문제 발생' },
    { value: 'audit_requirement', label: '감사 요구사항' },
    { value: 'service_dissatisfaction', label: '서비스 불만족' },
    { value: 'other', label: '기타' }
  ];

  // 사용자 정보 (API에서 계산)
  const [userInfo, setUserInfo] = useState({
    name: '',
    nickname: '',
    email: '',
    phone: '',
    joinDate: '',
    totalDonations: 0,
    totalCups: 0,
    totalCount: 0,
    rank: 0,
    level: '',
    badge: '',
    profileImage: localStorage.getItem('userProfileImage') || ''
  });

  // 데이터 로딩 - API에서 기부 내역과 정기 기부 가져오기
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // 로그인한 사용자 이메일 가져오기
        const userEmail = localStorage.getItem('loggedInEmail');

        if (!userEmail) {
          console.warn('로그인 정보가 없습니다. 로그인 페이지로 이동해주세요.');
          setDonationHistory([]);
          setRegularDonations([]);
          return;
        }

        // 기부 내역 가져오기
        const donations = await apiRequest<any>(`/donations?donor_email=${encodeURIComponent(userEmail)}`, {
          method: 'GET',
        });
        const donationList = donations.donations || [];
        setDonationHistory(donationList);

        // 정기 기부 가져오기
        const subscriptions = await apiRequest<any>(`/subscriptions?donor_email=${encodeURIComponent(userEmail)}`, {
          method: 'GET',
        });
        setRegularDonations(subscriptions.subscriptions || []);

        // 통계 계산
        const totalAmount = donationList.reduce((sum: number, d: any) => {
          const amount = Number(d.amount) || 0;
          return sum + amount;
        }, 0);
        const totalCups = Math.floor(totalAmount / 3000);
        const totalCount = donationList.length;

        setUserInfo(prev => ({
          ...prev,
          totalDonations: totalAmount,
          totalCups: totalCups || 0,
          totalCount: totalCount || 0,
        }));
      } catch (error) {
        console.error('데이터 로딩 실패:', error);
        setDonationHistory([]);
        setRegularDonations([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // 사용자 정보 로딩
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const userData = await apiRequest<any>('/auth/me', {
          method: 'GET',
        });

        setEditForm(prev => ({
          ...prev,
          name: userData.name || '소방이',
          nickname: userData.name || '소방이',
          email: userData.email || '',
          phone: userData.phone || '',
          idNumber: userData.id_number || '',
        }));

        setUserInfo(prev => ({
          ...prev,
          name: userData.name || '소방이',
          nickname: userData.name || '소방이',
          email: userData.email || '',
          phone: userData.phone || '',
          joinDate: userData.created_at || '',
        }));
      } catch (error) {
        console.error('사용자 정보 로딩 실패:', error);
        // Fallback to localStorage
        const userNickname = localStorage.getItem('userNickname') || '소방이';
        const userEmail = localStorage.getItem('loggedInEmail') || '';

        setEditForm(prev => ({
          ...prev,
          name: userNickname,
          nickname: userNickname,
          email: userEmail,
        }));

        setUserInfo(prev => ({
          ...prev,
          name: userNickname,
          nickname: userNickname,
          email: userEmail,
        }));
      }
    };

    fetchUserInfo();
  }, []);


  // 기존 코드에서 가져온 핸들러 및 상태
  const handleDonationClick = (donation: any) => {
    setSelectedDonation(donation);
    setShowDonationHistoryModal(true);
  };

  const handleWithdrawClick = (donation: any) => {
    setSelectedDonation(donation);
    setShowWithdrawModal(true);
  };

  // 철회/반환 사유 옵션
  const withdrawReasons = {
    individual: [
      '실수로 중복 기부함',
      '기부 금액을 잘못 입력함',
      '가족이나 지인이 실수로 기부함',
      '카드 도난/분실로 인한 부정 사용',
      '개인적인 사정으로 기부 취소',
      '기타'
    ],
    group: [
      '단체 승인 없이 개인이 기부함',
      '단체 예산 변경으로 인한 취소',
      '단체 기부 정책 변경',
      '담당자 변경으로 인한 재검토',
      '회계 처리 오류',
      '기타'
    ]
  };

  const [withdrawReasonLocal, setWithdrawReasonLocal] = useState('');
  const [withdrawDescription, setWithdrawDescription] = useState('');

  const handleWithdrawSubmit = () => {
    if (!withdrawReasonLocal) {
      alert('철회/반환 사유를 선택해주세요.');
      return;
    }

    if (withdrawReasonLocal === '기타' && !withdrawDescription.trim()) {
      alert('기타 사유를 입력해주세요.');
      return;
    }

    // 실제로는 API 호출
    alert('철회/반환 신청이 접수되었습니다. 영업일 기준 3-5일 내에 처리됩니다.');
    setShowWithdrawModal(false);
    setWithdrawReasonLocal('');
    setWithdrawDescription('');
  };

  // 정기 기부 상태별 색상 및 텍스트
  const getRegularStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <span className="px-3 py-1 text-xs bg-green-100 text-green-800 rounded-full font-medium">진행중</span>;
      case 'paused':
        return <span className="px-3 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full font-medium">일시정지</span>;
      case 'cancelled':
        return <span className="px-3 py-1 text-xs bg-red-100 text-red-800 rounded-full font-medium">취소됨</span>;
      default:
        return <span className="px-3 py-1 text-xs bg-gray-100 text-gray-800 rounded-full font-medium">알 수 없음</span>;
    }
  };

  // 주기별 텍스트
  const getCycleText = (cycle: string) => {
    switch (cycle) {
      case 'monthly':
        return '매월';
      case 'quarterly':
        return '분기별';
      case 'yearly':
        return '연간';
      default:
        return cycle;
      }
  };

  // 정기 기부 취소
  const handleRegularCancel = (regularDonation: any) => {
    setSelectedRegularDonation(regularDonation);
    setShowRegularCancelModal(true);
  };

  // 정기 기부 취소 확인
  const confirmRegularCancel = async () => {
    if (selectedRegularDonation) {
      try {
        await apiRequest(`/subscriptions/${selectedRegularDonation.id}/cancel`, {
          method: 'POST',
        });
        alert(`${selectedRegularDonation.fireStation}의 정기 기부가 취소되었습니다.`);
        setShowRegularCancelModal(false);
        setSelectedRegularDonation(null);
        // 데이터 리프레시
        window.location.reload();
      } catch (error) {
        console.error('정기 기부 취소 실패:', error);
        alert('정기 기부 취소 중 오류가 발생했습니다.');
      }
    }
  };

  // 정기 기부 재개
  const handleRegularResume = async (regularDonation: any) => {
    try {
      await apiRequest(`/subscriptions/${regularDonation.id}/resume`, {
        method: 'POST',
      });
      alert(`${regularDonation.fireStation}의 정기 기부가 재개되었습니다.`);
      // 데이터 리프레시
      window.location.reload();
    } catch (error) {
      console.error('정기 기부 재개 실패:', error);
      alert('정기 기부 재개 중 오류가 발생했습니다.');
    }
  };

  // 정기 기부 일시정지
  const handleRegularPause = async (regularDonation: any) => {
    try {
      await apiRequest(`/subscriptions/${regularDonation.id}/pause`, {
        method: 'POST',
      });
      alert(`${regularDonation.fireStation}의 정기 기부가 일시정지되었습니다.`);
      // 데이터 리프레시
      window.location.reload();
    } catch (error) {
      console.error('정기 기부 일시정지 실패:', error);
      alert('정기 기부 일시정지 중 오류가 발생했습니다.');
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

  const getDonationDate = (donation: any) => {
    if (!donation) return null;
    const raw = donation.created_at || donation.date;
    if (!raw) return null;
    const date = raw instanceof Date ? raw : new Date(raw);
    return Number.isNaN(date.getTime()) ? null : date;
  };

  const getStatusBadge = (donation: any) => {
    const refundStatus = donation.refund_status;

    if (refundStatus === 'pending') {
      return (
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
          환불 요청 중
        </span>
      );
    }

    if (refundStatus === 'approved') {
      return (
        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
          환불 승인
        </span>
      );
    }

    if (refundStatus === 'rejected') {
      return (
        <span className="px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded-full">
          환불 거절
        </span>
      );
    }

    switch (donation.status) {
      case 'completed':
        return <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">완료</span>;
      case 'pending':
        return <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">처리중</span>;
      case 'refunded':
        return <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">환불완료</span>;
      case 'failed':
        return <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">실패</span>;
      default:
        return <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">알 수 없음</span>;
    }
  };

  const downloadReceipt = (donationId: string) => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    window.open(`${apiBaseUrl}/donations/${donationId}/receipt`, '_blank');
  };

  const handleDonateClick = () => {
    router.push('/donations');
  };

  const handleWithdrawal = () => {
    if (!withdrawalCategory) {
      alert('탈퇴 사유를 선택해주세요.');
      return;
    }

    if (withdrawalCategory === 'other' && !withdrawalReason.trim()) {
      alert('기타 사유를 입력해주세요.');
      return;
    }

    // 실제 탈퇴 처리 로직
    alert('회원 탈퇴가 완료되었습니다.');
    setShowWithdrawalModal(false);
    // 로그아웃 처리 및 홈으로 이동
    router.push('/');
  };

  const handlePasswordConfirm = () => {
    if (!password.trim()) {
      alert('비밀번호를 입력해주세요.');
      return;
    }
    
    // 실제 비밀번호 확인 로직
    setShowPasswordModal(false);
    setPassword('');
    setShowProfileEditModal(true);
  };

  const sendEmailVerification = () => {
    if (!editForm.newEmail.trim()) {
      alert('새 이메일을 입력해주세요.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(editForm.newEmail)) {
      alert('올바른 이메일 형식을 입력해주세요.');
      return;
    }

    // 실제 인증번호 발송 로직
    setEditForm(prev => ({ ...prev, isCodeSent: true }));
    alert('인증번호가 새 이메일로 발송되었습니다.');
  };

  const verifyEmailCode = () => {
    if (!editForm.verificationCode.trim()) {
      alert('인증번호를 입력해주세요.');
      return;
    }

    // 실제 인증번호 확인 로직 (임시로 123456을 올바른 인증번호로 설정)
    if (editForm.verificationCode === '123456') {
      setEditForm(prev => ({ ...prev, isVerified: true }));
      alert('이메일 인증이 완료되었습니다.');
    } else {
      alert('인증번호가 올바르지 않습니다. 다시 확인해주세요.');
    }
  };

  const handleProfileUpdate = async () => {
    try {
      // 변경된 필드만 포함
      const updateData: any = {};

      if (editForm.name && editForm.name !== userInfo.name) {
        updateData.name = editForm.name;
      }

      if (editForm.newPhone && editForm.newPhone !== editForm.phone) {
        if (!/^01[0-9]{8,9}$/.test(editForm.newPhone)) {
          alert('휴대폰 번호 형식이 올바르지 않습니다. (예: 01012345678)');
          return;
        }
        updateData.phone = editForm.newPhone;
      }

      if (editForm.newIdNumber && editForm.newIdNumber !== editForm.idNumber) {
        if (!/^\d{6}-?\d{7}$/.test(editForm.newIdNumber)) {
          alert('주민등록번호 형식이 올바르지 않습니다. (예: 123456-1234567)');
          return;
        }
        updateData.id_number = editForm.newIdNumber;
      }

      // API 호출
      if (Object.keys(updateData).length > 0) {
        const updatedUser = await apiRequest('/auth/me', {
          method: 'PATCH',
          body: JSON.stringify(updateData),
        });

        // 상태 업데이트
        setUserInfo(prev => ({
          ...prev,
          name: updatedUser.name,
          phone: updatedUser.phone,
        }));

        setEditForm(prev => ({
          ...prev,
          name: updatedUser.name,
          phone: updatedUser.phone,
          idNumber: updatedUser.id_number,
          newPhone: '',
          newIdNumber: '',
        }));

        alert('프로필이 성공적으로 업데이트되었습니다.');
      } else {
        alert('변경된 정보가 없습니다.');
      }

      setShowProfileEditModal(false);
    } catch (error) {
      console.error('프로필 업데이트 실패:', error);
      alert('프로필 업데이트 중 오류가 발생했습니다.');
    }
  };

  const handleProfileImageChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // 파일 크기 체크 (5MB 제한)
      if (file.size > 5 * 1024 * 1024) {
        alert('파일 크기는 5MB 이하만 업로드 가능합니다.');
        return;
      }

      // 파일 형식 체크
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
      if (!allowedTypes.includes(file.type)) {
        alert('JPG, PNG, GIF 형식의 이미지만 업로드 가능합니다.');
        return;
      }

      setProfileImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setProfileImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleProfileImageClick = () => {
    document.getElementById('profile-image-input')?.click();
  };

  // 기부 내역 선택 처리
  const handleDonationSelect = (donationId: number) => {
    const newSelected = new Set(selectedDonations);
    if (newSelected.has(donationId)) {
      newSelected.delete(donationId);
    } else {
      newSelected.add(donationId);
    }
    setSelectedDonations(newSelected);
    setSelectAll(newSelected.size === selectableDonations.length);
  };

  // 전체 선택/해제 처리
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedDonations(new Set());
      setSelectAll(false);
    } else {
      const allSelectableIds = new Set(selectableDonations.map(d => d.id));
      setSelectedDonations(allSelectableIds);
      setSelectAll(true);
    }
  };

  // 선택 가능한 기부 내역 (완료되고 영수증 미발급된 것만)
  const selectableDonations = donationHistory.filter((donation) =>
    donation.status === 'completed'
    && !donation.receiptIssued
    && (!donation.refund_status || donation.refund_status === 'rejected')
  );

  // 선택된 기부 내역의 총액 계산
  const selectedDonationsAmount = Array.from(selectedDonations)
    .map((id) => donationHistory.find((d) => d.id === id))
    .filter(Boolean)
    .reduce((sum, donation) => sum + Number(donation?.amount || 0), 0);

  // 철회/반환 신청 처리 (수정)
  const handleRefundSubmit = async () => {
    if (selectedDonations.size === 0) {
      alert('철회/반환할 기부 내역을 선택해주세요.');
      return;
    }

    if (!refundCategory) {
      alert('철회/반환 사유를 선택해주세요.');
      return;
    }

    if (refundCategory === 'other' && !refundCustomReason.trim()) {
      alert('기타 사유를 입력해주세요.');
      return;
    }

    if (!isRefundConfirmed) {
      alert('안내사항을 확인하고 동의해주세요.');
      return;
    }

    // 선택된 기부 내역 정보
    const selectedDonationItems = Array.from(selectedDonations)
      .map(id => donationHistory.find(d => d.id === id))
      .filter(Boolean);
    const selectedIds = selectedDonationItems.map((donation) => donation!.id);

    try {
      // 각 선택된 기부에 대해 환불 요청
      const refundPromises = selectedDonationItems.map(async (donation) => {
        if (!donation) return;

        const reason = refundCategory === 'other'
          ? refundCustomReason
          : (userType === 'group' ? groupRefundReasons : individualRefundReasons)
              .find(r => r.value === refundCategory)?.label || refundCategory;

        return await apiRequest(`/donations/${donation.id}/refund`, {
          method: 'POST',
          body: JSON.stringify({ reason })
        });
      });

      await Promise.all(refundPromises);

      const nowIso = new Date().toISOString();
      setDonationHistory(prev => prev.map(donation => (
        selectedIds.includes(donation.id)
          ? {
              ...donation,
              refund_status: 'pending',
              refund_requested_at: nowIso,
            }
          : donation
      )));

      setShowRefundModal(false);
      setShowRefundCompleteModal(true);

      // 상태 초기화
      setSelectedDonations(new Set());
      setSelectAll(false);
      setRefundCategory('');
      setRefundCustomReason('');
      setIsRefundConfirmed(false);

      // 기부 내역 새로고침 (실제로는 API에서 다시 불러와야 함)
      // TODO: 기부 내역 API 재호출
    } catch (error) {
      console.error('환불 처리 중 오류:', error);
      alert(error instanceof Error ? error.message : '환불 처리 중 오류가 발생했습니다.');
    }
  };

  const currentDonations = donationHistory.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  const totalPages = Math.ceil(donationHistory.length / itemsPerPage);

  return (
    <div className="bg-gray-50">
      {/* 프로필 헤더 */}
      <section className="bg-gradient-to-r from-red-600 to-orange-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center space-y-6 md:space-y-0 md:space-x-8">
            <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-white/20">
              {userType === 'group' ? (
                <div className="w-full h-full bg-blue-600 flex items-center justify-center">
                  <i className="ri-building-fill text-white text-5xl"></i>
                </div>
              ) : userInfo.profileImage ? (
                <Image
                  src={userInfo.profileImage}
                  alt="프로필 사진"
                  width={128}
                  height={128}
                  className="w-full h-full object-cover"
                  unoptimized
                />
              ) : (
                <div className="w-full h-full bg-red-600 flex items-center justify-center">
                  <span className="text-white text-4xl font-bold">{userInfo.nickname.charAt(0)}</span>
                </div>
              )}
            </div>
            <div className="text-center md:text-left">
              <h1 className="text-3xl font-bold mb-2">
                {userType === 'group' ? `${userInfo.name}` : `${userInfo.name}님`}
              </h1>
              <p className="text-xl text-red-100 mb-4">
                {userType === 'group' ? '단체 계정' : `@${userInfo.nickname}`}
              </p>
              <div className="flex flex-wrap justify-center md:justify-start items-center space-x-4">
                <span className={`px-3 py-1 text-sm rounded-full font-medium ${getLevelBadgeColor(userInfo.level)} bg-white/20 text-white`}>
                  {userType === 'group' ? '단체 기부자' : `${userInfo.level} 기부자`}
                </span>
                {userType !== 'group' && (
                  <span className="text-red-100">전체 {userInfo.rank}위</span>
                )}
                <span className="text-red-100">
                  {userType === 'group' ? '등록일' : '가입일'}: {userInfo.joinDate}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 사용자 요약 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <Card className="p-6 text-center bg-gradient-to-br from-green-50 to-green-100">
            <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <i className="ri-money-dollar-circle-fill text-white text-xl"></i>
            </div>
            <div className="text-3xl font-bold text-green-600 mb-2">
              {userInfo.totalDonations.toLocaleString()}원
            </div>
            <div className="text-gray-600">총 기부금액</div>
          </Card>
          <Card className="p-6 text-center bg-gradient-to-br from-orange-50 to-orange-100">
            <div className="w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <i className="ri-cup-fill text-white text-xl"></i>
            </div>
            <div className="text-3xl font-bold text-orange-600 mb-2">
              {userInfo.totalCups}잔
            </div>
            <div className="text-gray-600">전달한 커피</div>
          </Card>
          <Card className="p-6 text-center bg-gradient-to-br from-blue-50 to-blue-100">
            <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <i className="ri-heart-fill text-white text-xl"></i>
            </div>
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {userInfo.totalCount}회
            </div>
            <div className="text-gray-600">기부 횟수</div>
          </Card>
        </div>

        {/* 탭 메뉴 */}
        <div className="flex justify-center mb-8">
          <div className="bg-white shadow-sm p-1 rounded-full border">
            <button
              onClick={() => setActiveTab('donations')}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'donations'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              기부 내역
            </button>
            <button
              onClick={() => setActiveTab('regular')}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'regular'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              정기 기부
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'profile'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {userType === 'group' ? '단체 정보' : '프로필 보기'}
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'settings'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {userType === 'group' ? '단체 관리' : '프로필 관리'}
            </button>
          </div>
        </div>

        {/* 탭 콘텐츠 */}
        {activeTab === 'donations' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 기부 내역 목록 */}
            <div className="lg:col-span-2">
              <Card className="overflow-hidden">
                <div className="p-4 bg-gray-50 border-b flex justify-between items-center">
                  <h3 className="font-semibold text-gray-900">
                    기부 내역 ({donationHistory.length}건)
                  </h3>
                  {/* 철회/반환 신청 버튼 */}
                  <button
                    onClick={() => setShowRefundModal(true)}
                    className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors duration-200"
                  >
                    철회/반환 신청
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="w-12 px-4 py-3 text-left">
                          <input
                            type="checkbox"
                            checked={selectAll}
                            onChange={handleSelectAll}
                            className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                          />
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">날짜</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">소방서</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">금액</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">상태</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">영수증</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {currentDonations.map(donation => (
                        <tr key={donation.id} className="hover:bg-gray-50 transition-colors duration-150">
                          <td className="px-4 py-3">
                            {donation.status === 'completed' && !donation.receiptIssued && (!donation.refund_status || donation.refund_status === 'rejected') && (
                              <input
                                type="checkbox"
                                checked={selectedDonations.has(donation.id)}
                                onChange={() => handleDonationSelect(donation.id)}
                                className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                              />
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {(() => {
                              const date = getDonationDate(donation);
                              return date ? date.toLocaleDateString('ko-KR') : '날짜 미확인';
                            })()}
                          </td>
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {donation.fire_station?.name || donation.fireStation || '알 수 없음'}
                          </td>
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {Number(donation.amount).toLocaleString()}원
                          </td>
                          <td className="px-4 py-3">
                    {getStatusBadge(donation)}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {donation.needs_receipt && donation.status === 'completed' ? (
                              <button
                                onClick={() => downloadReceipt(donation.id)}
                                className="text-orange-600 hover:text-orange-800 font-medium transition-colors duration-200"
                              >
                                <i className="ri-download-2-line"></i> 다운로드
                              </button>
                            ) : (
                              <span className="text-gray-400">미신청</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* 페이지네이션 */}
                <div className="p-4 bg-gray-50 border-t flex justify-between items-center">
                  <div className="text-sm text-gray-700">
                    전체 {donationHistory.length}건 중 {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, donationHistory.length)}건 표시
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                    >
                      <i className="ri-arrow-left-s-line"></i>
                    </button>
                    <div className="flex space-x-1">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          className={`w-10 h-10 rounded-lg font-medium transition-colors duration-200 ${
                            page === currentPage
                              ? 'bg-orange-600 text-white'
                              : 'bg-white text-gray-700 hover:bg-orange-50 border border-gray-300'
                          }`}
                        >
                          {page}
                        </button>
                      ))}
                    </div>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                    >
                      <i className="ri-arrow-right-s-line"></i>
                    </button>
                  </div>
                </div>
              </Card>
            </div>

            {/* 기부 통계 */}
            <div>
              <Card className="p-6">
                <h3 className="font-semibold text-lg text-gray-900 mb-4">기부 통계</h3>
                <div className="space-y-4">
                  {monthlyStats.map((stat, index) => (
                    <div key={index} className="flex justify-between items-center pb-4 border-b border-gray-100 last:border-b-0 last:pb-0">
                      <div className="text-gray-600">{stat.month}</div>
                      <div className="text-right">
                        <div className="font-medium text-gray-900">{stat.amount.toLocaleString()}원</div>
                        <div className="text-sm text-gray-500">{stat.count}회 / {stat.cups}잔</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              <div className="mt-6">
                <Button
                  onClick={handleDonateClick}
                  className="w-full py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors duration-200"
                >
                  <i className="ri-add-line mr-2"></i>
                  기부하기
                </Button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'regular' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <Card className="overflow-hidden">
                <div className="p-4 bg-gray-50 border-b">
                  <h3 className="font-semibold text-gray-900">
                    정기 기부 내역 ({regularDonations.length}건)
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">소방서</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">주기</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">금액</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">상태</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">관리</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {regularDonations.map(regular => (
                        <tr key={regular.id} className="hover:bg-gray-50 transition-colors duration-150">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {regular.fireStation}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {getCycleText(regular.cycle)}
                          </td>
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {Number(regular.amount).toLocaleString()}원
                          </td>
                          <td className="px-4 py-3">
                            {getRegularStatusBadge(regular.status)}
                          </td>
                          <td className="px-4 py-3 text-sm text-right">
                            {regular.status === 'active' ? (
                              <button
                                onClick={() => handleRegularCancel(regular)}
                                className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded font-medium transition-colors duration-200"
                              >
                                취소하기
                              </button>
                            ) : regular.status === 'paused' ? (
                              <div className="flex space-x-2 justify-end">
                                <button
                                  onClick={() => handleRegularResume(regular)}
                                  className="px-3 py-1 bg-green-100 hover:bg-green-200 text-green-700 rounded font-medium transition-colors duration-200"
                                >
                                  재개하기
                                </button>
                                <button
                                  onClick={() => handleRegularCancel(regular)}
                                  className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded font-medium transition-colors duration-200"
                                >
                                  취소하기
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() => handleRegularPause(regular)}
                                className="px-3 py-1 bg-yellow-100 hover:bg-yellow-200 text-yellow-700 rounded font-medium transition-colors duration-200"
                              >
                                일시정지하기
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>

              <div className="mt-6">
                <Button
                  onClick={handleDonateClick}
                  className="w-full py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors duration-200"
                >
                  <i className="ri-add-line mr-2"></i>
                  정기 기부하기
                </Button>
              </div>
            </div>

            <div>
              <Card className="p-6">
                <h3 className="font-semibold text-lg text-gray-900 mb-4">정기 기부 설명</h3>
                <div className="space-y-4 text-sm text-gray-600">
                  <p>정기 기부는 매월 또는 일정 주기마다 자동으로 기부금이 결제되는 기부 방식입니다.</p>
                  <p>• <span className="font-medium">진행중</span>: 정기 결제가 활성화되어 다음 기부가 예정된 상태</p>
                  <p>• <span className="font-medium">일시정지</span>: 결제가 일시적으로 중단된 상태</p>
                  <p>• <span className="font-medium">취소됨</span>: 정기 기부가 완전히 종료된 상태</p>
                  <div className="mt-6 p-4 bg-orange-50 rounded-lg">
                    <p className="text-orange-800 font-medium">정기 기부는 기부자님의 지속적인 관심과 나눔을 가능하게 합니다. 불편사항이나 변경사항이 있으시면 언제든지 상태 변경이 가능합니다.</p>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'profile' && (
          <div className="max-w-2xl mx-auto">
            <Card className="p-8">
              <div className="flex flex-col items-center mb-8">
                <div className="relative mb-6">
                  {userType === 'group' ? (
                    <div className="w-24 h-24 rounded-full overflow-hidden border-4 border-orange-100">
                      <div className="w-full h-full bg-blue-600 flex items-center justify-center">
                        <i className="ri-building-fill text-white text-4xl"></i>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="w-24 h-24 rounded-full overflow-hidden border-4 border-orange-100 mb-4">
                        {userInfo.profileImage ? (
                          <Image
                            src={userInfo.profileImage}
                            alt="프로필 사진"
                            width={96}
                            height={96}
                            className="w-full h-full object-cover"
                            unoptimized
                          />
                        ) : (
                          <div className="w-full h-full bg-red-600 flex items-center justify-center">
                            <span className="text-white text-3xl font-bold">{userInfo.nickname.charAt(0)}</span>
                          </div>
                        )}
                      </div>
                      <p className="text-gray-600 text-sm">등록된 프로필 사진이 없습니다.</p>
                    </>
                  )}
                </div>

                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {userInfo.name} {userType !== 'group' ? '님' : ''}
                  </h2>
                  <p className="text-gray-600 mb-4">@{userInfo.nickname}</p>
                  <div className="flex flex-wrap justify-center items-center gap-2">
                    <span className={`px-3 py-1 text-sm rounded-full font-medium ${getLevelBadgeColor(userInfo.level)}`}>
                      {userType === 'group' ? '단체 기부자' : `${userInfo.level} 기부자`}
                    </span>
                    {userType !== 'group' && (
                      <span className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full">
                        전체 {userInfo.rank}위
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        이메일
                      </label>
                      <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                        {userInfo.email}
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        전화번호
                      </label>
                      <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                        {userInfo.phone}
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        가입일
                      </label>
                      <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                        {userInfo.joinDate}
                      </div>
                      {userType === 'group' && groupNumber && (
                        <div className="mt-2">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            단체 번호
                          </label>
                          <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                            {groupNumber}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        기부자 뱃지
                      </label>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">{userInfo.badge}</span>
                        <span className="text-gray-700">{userInfo.level} 기부자</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-8 w-full">
                  <button
                    onClick={() => setShowProfileModal(true)}
                    className="w-full py-3 px-4 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors duration-200"
                  >
                    프로필 정보 확인하기
                  </button>
                </div>
              </div>
            </Card>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="max-w-2xl mx-auto">
            <Card className="p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-8">
                {userType === 'group' ? '단체 계정 관리' : '계정 관리'}
              </h2>
              
              <div className="space-y-6">
                <div className="border-b border-gray-200 pb-6">
                  <h3 className="font-semibold text-lg text-gray-900 mb-4">프로필 수정</h3>
                  <p className="text-gray-600 mb-4">기부자님의 프로필 정보를 수정할 수 있습니다.</p>
                  <button
                    onClick={() => setShowPasswordModal(true)}
                    className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors duration-200"
                  >
                    프로필 수정하기
                  </button>
                </div>
                
                <div>
                  <h3 className="font-semibold text-lg text-gray-900 mb-4">회원 탈퇴</h3>
                  <p className="text-gray-600 mb-4">
                    계정을 영구적으로 삭제하고 서비스 이용을 중단합니다. 개인정보는 모두 삭제되며 복구할 수 없습니다.
                  </p>
                  <button
                    onClick={() => setShowWithdrawalModal(true)}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors duration-200"
                  >
                    탈퇴하기
                  </button>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* 모든 모달들 - 기존 코드와 동일하게 유지 */}
        {showProfileModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">프로필 정보</h3>
              <button
                onClick={() => setShowProfileModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>

            <div className="text-center mb-8">
              <div className="w-20 h-20 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                {userInfo.name.charAt(0)}
              </div>
              <h4 className="text-xl font-bold text-gray-900">{userInfo.name}</h4>
              <p className="text-gray-600">@{userInfo.nickname}</p>
            </div>
            
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    이름
                  </label>
                  <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                    {userInfo.name.replace(/(.{1})(.*)/, '$1***')}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    닉네임
                  </label>
                  <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                    {userInfo.nickname}
                  </div>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이메일
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  {userInfo.email.replace(/(.{2}).*(@.*)/, '$1***$2')}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  전화번호
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  {userInfo.phone.replace(/(\d{3})-(\d{4})-(\d{4})/, '$1-****-****')}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  주민등록번호
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  123456-*******
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  가입일
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  {userInfo.joinDate}
                </div>
              </div>
            </div>

            <div className="mt-8 text-center">
              <Button
                variant="outline"
                onClick={() => setShowProfileModal(false)}
                className="w-full"
              >
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}
      
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">비밀번호 확인</h3>
              <button
                onClick={() => setShowPasswordModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>
            
            <div className="space-y-6">
              <p className="text-gray-600">
                회원님의 정보를 안전하게 보호하기 위해 비밀번호를 다시 한 번 확인합니다.
              </p>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  비밀번호
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                  placeholder="비밀번호를 입력해주세요"
                />
              </div>
              
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowPasswordModal(false)}
                  className="flex-1"
                >
                  취소
                </Button>
                <Button
                  onClick={handlePasswordConfirm}
                  className="flex-1 bg-orange-600 hover:bg-orange-700 text-white"
                >
                  확인
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {showProfileEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">프로필 수정</h3>
              <button
                onClick={() => setShowProfileEditModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>
            
            <div className="space-y-6">
              {/* 프로필 사진 */}
              <div className="text-center">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  프로필 사진
                </label>
                <div className="flex justify-center">
                  <div className="relative">
                    {profileImagePreview ? (
                      <Image
                        src={profileImagePreview}
                        alt="미리보기"
                        width={96}
                        height={96}
                        className="w-24 h-24 rounded-full object-cover border-4 border-orange-100"
                        unoptimized
                      />
                    ) : userInfo.profileImage ? (
                      <Image
                        src={userInfo.profileImage}
                        alt="프로필"
                        width={96}
                        height={96}
                        className="w-24 h-24 rounded-full object-cover border-4 border-orange-100"
                        unoptimized
                      />
                    ) : (
                      <div className="w-24 h-24 rounded-full bg-gray-200 border-4 border-orange-100 flex items-center justify-center">
                        <i className="ri-user-fill text-gray-400 text-2xl"></i>
                      </div>
                    )}
                    <button
                      onClick={handleProfileImageClick}
                      className="absolute bottom-0 right-0 w-8 h-8 bg-orange-600 rounded-full flex items-center justify-center text-white hover:bg-orange-700 transition-colors duration-200"
                    >
                      <i className="ri-camera-fill text-sm"></i>
                    </button>
                    <input
                      id="profile-image-input"
                      type="file"
                      accept="image/*"
                      onChange={handleProfileImageChange}
                      className="hidden"
                    />
                  </div>
                </div>
              </div>
              
              {/* 이름 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이름
                </label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                />
              </div>
              
              {/* 닉네임 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  닉네임
                </label>
                <input
                  type="text"
                  value={editForm.nickname}
                  onChange={(e) => setEditForm(prev => ({ ...prev, nickname: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                />
              </div>
              
              {/* 이메일 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이메일
                </label>
                <input
                  type="email"
                  value={editForm.newEmail || editForm.email}
                  onChange={(e) => setEditForm(prev => ({ ...prev, newEmail: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                  placeholder="새 이메일 주소를 입력해주세요"
                />
                {editForm.newEmail && (
                  <div className="mt-3 space-y-3">
                    <button
                      onClick={sendEmailVerification}
                      className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors duration-200"
                    >
                      인증번호 받기
                    </button>
                    {editForm.isCodeSent && (
                      <div className="mt-3 space-y-3">
                        <input
                          type="text"
                          value={editForm.verificationCode}
                          onChange={(e) => setEditForm(prev => ({ ...prev, verificationCode: e.target.value }))}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                          placeholder="인증번호를 입력해주세요"
                        />
                        <button
                          onClick={verifyEmailCode}
                          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors duration-200"
                        >
                          인증하기
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              {/* 전화번호 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  전화번호
                </label>
                <input
                  type="tel"
                  value={editForm.newPhone || editForm.phone}
                  onChange={(e) => setEditForm(prev => ({ ...prev, newPhone: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                  placeholder="새 전화번호를 입력해주세요 (예: 01012345678)"
                />
                <p className="text-xs text-gray-500 mt-1">하이픈(-) 없이 숫자만 입력해주세요.</p>
              </div>

              {/* 주민등록번호 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  주민등록번호
                </label>
                <input
                  type="text"
                  value={editForm.newIdNumber || editForm.idNumber}
                  onChange={(e) => setEditForm(prev => ({ ...prev, newIdNumber: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                  placeholder="새 주민등록번호를 입력해주세요 (예: 123456-1234567)"
                  maxLength={14}
                />
                <p className="text-xs text-gray-500 mt-1">영수증 발급을 위해 필요합니다. 안전하게 보관됩니다.</p>
              </div>
            </div>
            
            <div className="mt-8 flex space-x-3">
              <Button
                variant="outline"
                onClick={() => setShowProfileEditModal(false)}
                className="flex-1"
              >
                취소
              </Button>
              <Button
                onClick={handleProfileUpdate}
                className="flex-1 bg-orange-600 hover:bg-orange-700 text-white"
              >
                저장
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 기부 내역 상세 모달 */}
      {showDonationHistoryModal && selectedDonation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">기부 상세 정보</h3>
              <button
                onClick={() => setShowDonationHistoryModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  기부 날짜
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  {(() => {
                    const date = getDonationDate(selectedDonation);
                    return date ? date.toLocaleDateString('ko-KR') : '날짜 미확인';
                  })()}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  기부 소방서
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  {selectedDonation.fireStation}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  기부 금액
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  {selectedDonation.amount.toLocaleString()}원
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  기부자 이름
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  {selectedDonation.donorName}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  기부자 구분
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  {selectedDonation.donorCategory}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  기부 인증번호
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                  {selectedDonation.verificationId}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  응원 메시지
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900 min-h-[60px]">
                  {selectedDonation.message || '없음'}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  상태
                </label>
                <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg">
                  {getStatusBadge(selectedDonation)}
                </div>
              </div>
              
              {selectedDonation.refund_status === 'pending' && (
                <div className="p-3 bg-yellow-50 border border-yellow-100 rounded text-sm text-yellow-800">
                  <p>환불 요청이 접수되어 처리 중입니다.</p>
                  {selectedDonation.refund_requested_at && (
                    <p className="mt-1 text-xs">
                      요청일: {new Date(selectedDonation.refund_requested_at).toLocaleString('ko-KR')}
                    </p>
                  )}
                </div>
              )}
              {selectedDonation.refund_status === 'approved' && (
                <div className="p-3 bg-blue-50 border border-blue-100 rounded text-sm text-blue-800">
                  환불이 승인되었습니다.
                </div>
              )}
              {selectedDonation.refund_status === 'rejected' && (
                <div className="p-3 bg-orange-50 border border-orange-100 rounded text-sm text-orange-800">
                  환불 요청이 거절되었습니다.
                </div>
              )}
              
              {selectedDonation.status === 'completed' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    영수증
                  </label>
                  <div className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                    {selectedDonation.receiptIssued ? (
                      <div className="flex justify-between items-center">
                        <span>발급 완료</span>
                        <button
                          onClick={() => downloadReceipt(selectedDonation.id)}
                          className="px-3 py-1 bg-green-100 hover:bg-green-200 text-green-700 rounded font-medium transition-colors duration-200"
                        >
                          다운로드
                        </button>
                      </div>
                    ) : (
                      <span className="text-gray-500">미발급</span>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-8 text-center">
              <Button
                variant="outline"
                onClick={() => setShowDonationHistoryModal(false)}
                className="w-full"
              >
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}
      
      {/* 철회/반환 신청 모달 */}
      {showRefundModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">철회/반환 신청</h3>
              <button
                onClick={() => setShowRefundModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>

            {/* 신청 안내문 */}
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
              <p className="text-orange-800 text-sm">
                • 철회/반환은 영수증이 미발급된 기부금만 신청 가능합니다.<br/>
                • 신청 후 영업일 기준 3-5일 내에 처리됩니다.<br/>
                • 기부자 정보, 기부금액, 기부 방식 등이 반환 신청 정보에 포함됩니다.
              </p>
            </div>

            <div className="space-y-6">
              {/* 선택된 기부 내역들 */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">선택된 기부 내역</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {Array.from(selectedDonations).map((id) => {
                    const donation = donationHistory.find((d) => d.id === id);
                    if (!donation) {
                      return null;
                    }

                    const donationDate = donation.created_at
                      ? new Date(donation.created_at)
                      : donation.date
                      ? new Date(donation.date)
                      : null;
                    const fireStationName =
                      donation.fire_station?.name || donation.fireStation || '알 수 없음';
                    const amountValue =
                      typeof donation.amount === 'number'
                        ? donation.amount
                        : Number(donation.amount || 0);

                    return (
                      <div
                        key={id}
                        className="px-4 py-2 bg-gray-50 border border-gray-200 rounded text-sm text-gray-700"
                      >
                        <span className="font-medium">
                          {donationDate ? donationDate.toLocaleDateString('ko-KR') : '날짜 미확인'}
                        </span>{' '}
                        - <span className="mx-2">{fireStationName}</span> -{' '}
                        <span>{amountValue.toLocaleString()}원</span>
                      </div>
                    );
                  })}
                </div>
                
                {selectedDonations.size > 0 && (
                  <div className="mt-3 p-3 bg-orange-100 rounded-lg text-center">
                    <p className="text-orange-800 font-medium">
                      선택된 기부 내역 총액: {selectedDonationsAmount.toLocaleString()}원
                    </p>
                  </div>
                )}
              </div>
              
              {/* 철회/반환 사유 선택 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  철회/반환 사유
                </label>
                <select
                  value={refundCategory}
                  onChange={(e) => setRefundCategory(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                >
                  <option value="">선택해주세요</option>
                  {(userType === 'group' ? groupRefundReasons : individualRefundReasons).map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                
                {refundCategory === 'other' && (
                  <div className="mt-3">
                    <textarea
                      value={refundCustomReason}
                      onChange={(e) => setRefundCustomReason(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                      placeholder="기타 사유를 입력해주세요"
                      rows={3}
                    />
                  </div>
                )}
              </div>
              
              {/* 안내사항 확인 */}
              <div>
                <label className="flex items-start space-x-2">
                  <input
                    type="checkbox"
                    checked={isRefundConfirmed}
                    onChange={(e) => setIsRefundConfirmed(e.target.checked)}
                    className="mt-1 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                  />
                  <span className="text-sm text-gray-700">
                    위 기부금 철회/반환 신청에 동의합니다. 동의 후 신청이 진행됩니다.
                  </span>
                </label>
              </div>
              
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowRefundModal(false)}
                  className="flex-1"
                >
                  취소
                </Button>
                <Button
                  onClick={handleRefundSubmit}
                  className="flex-1 bg-orange-600 hover:bg-orange-700 text-white"
                  disabled={selectedDonations.size === 0 || !refundCategory || !isRefundConfirmed}
                >
                  신청하기
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* 철회/반환 완료 모달 */}
      {showRefundCompleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-check-line text-green-600 text-2xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">철회/반환 신청 완료</h3>
              <p className="text-gray-600 mb-6">
                정상적으로 철회/반환 신청이 완료되었습니다.<br/>
                영업일 기준 3-5일 내에 처리됩니다.
              </p>
              <Button
                onClick={() => setShowRefundCompleteModal(false)}
                className="w-full bg-orange-600 hover:bg-orange-700 text-white"
              >
                확인
              </Button>
            </div>
          </div>
        </div>
      )}
      
      {/* 정기 기부 취소 확인 모달 */}
      {showRegularCancelModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="ri-alert-line text-red-600 text-2xl"></i>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">정기 기부 취소</h3>
              <p className="text-gray-600 mb-6">
                {selectedRegularDonation?.fireStation}의 정기 기부를 정말 취소하시겠습니까?
              </p>
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowRegularCancelModal(false)}
                  className="flex-1"
                >
                  취소
                </Button>
                <Button
                  onClick={confirmRegularCancel}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                >
                  확인
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* 회원 탈퇴 모달 */}
      {showWithdrawalModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">회원 탈퇴</h3>
              <button
                onClick={() => setShowWithdrawalModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>
            
            <div className="space-y-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800 text-sm">
                  정말 탈퇴하시겠습니까? 탈퇴 후에는 모든 기부 정보가 삭제되며 복구할 수 없습니다.
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  탈퇴 사유
                </label>
                <select
                  value={withdrawalCategory}
                  onChange={(e) => setWithdrawalCategory(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                >
                  <option value="">선택해주세요</option>
                  {withdrawalOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                
                {withdrawalCategory === 'other' && (
                  <div className="mt-3">
                    <input
                      type="text"
                      value={withdrawalReason}
                      onChange={(e) => setWithdrawalReason(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                      placeholder="기타 사유를 입력해주세요"
                    />
                  </div>
                )}
              </div>
              
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowWithdrawalModal(false)}
                  className="flex-1"
                >
                  취소
                </Button>
                <Button
                  onClick={handleWithdrawal}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                >
                  탈퇴하기
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 철회/반환 모달 (개별 기부 내역에서 접근) */}
      {showWithdrawModal && selectedDonation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">철회/반환 신청</h3>
              <button
                onClick={() => setShowWithdrawModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <i className="ri-close-line text-2xl"></i>
              </button>
            </div>
            
            <div className="space-y-6">
              <div className="bg-orange-50 rounded-lg p-4">
                <p className="text-orange-800 text-sm">
                  선택한 기부 내역을 철회하거나 반환 신청을 하시겠습니까?<br/>
                  신청 후 영업일 기준 3-5일 내에 처리됩니다.
                </p>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    기부 소방서
                  </label>
                  <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                    {selectedDonation.fireStation}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    기부 금액
                  </label>
                  <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                    {selectedDonation.amount.toLocaleString()}원
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    기부자 구분
                  </label>
                  <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
                    {selectedDonation.donorCategory}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    철회/반환 사유
                  </label>
                  <select
                    value={withdrawReasonLocal}
                    onChange={(e) => setWithdrawReasonLocal(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                  >
                    <option value="">선택해주세요</option>
                    {withdrawReasons[userType as 'individual' | 'group'].map((reason, index) => (
                      <option key={index} value={reason}>
                        {reason}
                      </option>
                    ))}
                  </select>
                  
                  {withdrawReasonLocal === '기타' && (
                    <div className="mt-3">
                      <textarea
                        value={withdrawDescription}
                        onChange={(e) => setWithdrawDescription(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200"
                        placeholder="기타 사유를 입력해주세요"
                        rows={3}
                      />
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowWithdrawModal(false)}
                  className="flex-1"
                >
                  취소
                </Button>
                <Button
                  onClick={handleWithdrawSubmit}
                  className="flex-1 bg-orange-600 hover:bg-orange-700 text-white"
                >
                  신청하기
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      </section>
    </div>
  );
}
