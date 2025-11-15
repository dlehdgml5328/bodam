'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiRequest, ApiError } from '@/lib/api';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';

interface Donation {
  id: string;
  mode: 'single' | 'multiple';
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  message: string | null;
  is_anonymous: boolean;
  needs_receipt: boolean;
  created_at: string;
  completed_at: string | null;
  fire_station: {
    id: string;
    name: string;
    region: string;
    district: string;
  };
  payment: {
    method: string | null;
    toss_order_id: string | null;
    toss_payment_key: string | null;
  };
  regular: {
    subscription_id: string | null;
    status: string | null;
    cycle: string | null;
    next_billing_at: string | null;
  } | null;
  refund_status?: 'pending' | 'approved' | 'rejected' | null;
  refund_requested_at?: string | null;
  refund_id?: string | null;
}

export default function DonationHistoryPage() {
  const router = useRouter();
  const [donations, setDonations] = useState<Donation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showRefundModal, setShowRefundModal] = useState(false);
  const [selectedDonation, setSelectedDonation] = useState<Donation | null>(null);
  const [refundReason, setRefundReason] = useState('');

  useEffect(() => {
    const fetchDonations = async () => {
      const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
      if (!isLoggedIn) {
        router.push('/login?redirect=/donations/history');
        return;
      }

      try {
        // 서버에서 사용자 정보 가져오기
        const userData = await apiRequest<{
          id: string;
          email: string;
          name: string;
        }>('/auth/me');

        console.log('✅ 사용자 정보:', userData);

        // 기부 내역 조회
        const data = await apiRequest<{ donations: Donation[]; total: number }>(
          `/donations?donor_email=${encodeURIComponent(userData.email)}&limit=50`
        );

        console.log('✅ 기부 내역:', data.donations.length, '개');
        setDonations(data.donations);
        setLoading(false);
      } catch (err: any) {
        console.error('❌ 기부 내역 조회 실패:', err);
        if (err instanceof ApiError) {
          if (err.message.includes('NOT_AUTHENTICATED') || err.message.includes('401')) {
            // 인증 실패 시 로그인 페이지로
            localStorage.removeItem('isLoggedIn');
            router.push('/login?redirect=/donations/history');
          } else {
            setError(err.message);
          }
        } else {
          setError('기부 내역을 불러오는 중 오류가 발생했습니다.');
        }
        setLoading(false);
      }
    };

    void fetchDonations();
  }, [router]);

  const getStatusBadge = (donation: Donation) => {
    const refundStatus = donation.refund_status;
    if (refundStatus === 'pending') {
      return (
        <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
          환불 요청 중
        </span>
      );
    }
    if (refundStatus === 'approved') {
      return (
        <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
          환불 승인
        </span>
      );
    }
    if (refundStatus === 'rejected') {
      return (
        <span className="px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800">
          환불 거절
        </span>
      );
    }

    const badges: Record<string, { color: string; text: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-800', text: '대기 중' },
      completed: { color: 'bg-green-100 text-green-800', text: '완료' },
      failed: { color: 'bg-red-100 text-red-800', text: '실패' },
      refunded: { color: 'bg-gray-100 text-gray-800', text: '환불됨' },
    };
    const badge = badges[donation.status] || { color: 'bg-gray-100 text-gray-800', text: donation.status };
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${badge.color}`}>
        {badge.text}
      </span>
    );
  };

  const handleRefundRequest = async () => {
    if (!selectedDonation || !refundReason.trim()) {
      alert('환불 사유를 입력해주세요.');
      return;
    }

    try {
      await apiRequest(`/donations/${selectedDonation.id}/refund`, {
        method: 'POST',
        body: JSON.stringify({ reason: refundReason }),
      });

      alert('환불 요청이 접수되었습니다.');
      const nowIso = new Date().toISOString();
      setDonations((prev) =>
        prev.map((donation) =>
          donation.id === selectedDonation.id
            ? {
                ...donation,
                refund_status: 'pending',
                refund_requested_at: nowIso,
              }
            : donation
        )
      );
      setSelectedDonation((prev) =>
        prev
          ? {
              ...prev,
              refund_status: 'pending',
              refund_requested_at: nowIso,
            }
          : prev
      );
      setShowRefundModal(false);
      setRefundReason('');
    } catch (err: any) {
      alert(err.message || '환불 요청 중 오류가 발생했습니다.');
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Seoul',
    });
  };

  const formatAmount = (amount: number) => {
    return amount.toLocaleString('ko-KR');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">기부 내역을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="max-w-md mx-auto p-6">
          <div className="text-center">
            <i className="ri-error-warning-line text-4xl text-red-500 mb-4"></i>
            <h2 className="text-xl font-bold mb-2">오류 발생</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={() => router.push('/donations')}>
              기부하기
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">기부 내역</h1>
            <p className="text-gray-600">나의 기부 내역을 확인하세요</p>
          </div>
          <Button onClick={() => router.push('/')}>
            <i className="ri-home-line mr-2"></i>
            홈으로
          </Button>
        </div>

        {donations.length === 0 ? (
          <Card className="p-8 text-center">
            <i className="ri-inbox-line text-6xl text-gray-300 mb-4"></i>
            <h3 className="text-xl font-semibold mb-2">기부 내역이 없습니다</h3>
            <p className="text-gray-600 mb-4">
              소방관님들을 위한 첫 기부를 시작해보세요
            </p>
            <Button onClick={() => router.push('/donations')}>
              기부하기
            </Button>
          </Card>
        ) : (
          <div className="space-y-4">
            {donations.map((donation) => (
              <Card key={donation.id} className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-bold mb-1">
                      {donation.fire_station.name}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {donation.fire_station.region} · {donation.fire_station.district}
                    </p>
                  </div>
                  <div className="text-right">
                    {getStatusBadge(donation)}
                    {donation.regular && (
                      <div className="mt-2">
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium">
                          정기기부
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">기부 금액</p>
                    <p className="font-bold text-lg">
                      {formatAmount(donation.amount)}원
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">기부일</p>
                    <p className="text-sm">{formatDate(donation.created_at)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">결제 방법</p>
                    <p className="text-sm">{donation.payment.method || '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">익명 여부</p>
                    <p className="text-sm">{donation.is_anonymous ? '익명' : '공개'}</p>
                  </div>
                </div>

                {donation.message && (
                  <div className="mb-4 p-3 bg-gray-50 rounded">
                    <p className="text-sm text-gray-700">
                      💌 {donation.message}
                    </p>
                  </div>
                )}

                {donation.regular && donation.regular.next_billing_at && (
                  <div className="mb-4 p-3 bg-purple-50 rounded">
                    <p className="text-sm text-purple-900">
                      <i className="ri-calendar-line mr-1"></i>
                      다음 결제일: {formatDate(donation.regular.next_billing_at)}
                      <span className="ml-2 text-xs">
                        ({donation.regular.cycle})
                      </span>
                    </p>
                  </div>
                )}

                {donation.refund_status === 'pending' && (
                  <div className="mb-3 p-3 bg-yellow-50 rounded text-sm text-yellow-800">
                    <p>환불 요청이 접수되어 처리 중입니다.</p>
                    {donation.refund_requested_at && (
                      <p className="mt-1 text-xs">
                        요청일: {formatDate(donation.refund_requested_at)}
                      </p>
                    )}
                  </div>
                )}
                {donation.refund_status === 'approved' && (
                  <div className="mb-3 p-3 bg-blue-50 rounded text-sm text-blue-800">
                    환불이 승인되었습니다.
                  </div>
                )}
                {donation.refund_status === 'rejected' && (
                  <div className="mb-3 p-3 bg-orange-50 rounded text-sm text-orange-800">
                    환불 요청이 거절되었습니다.
                  </div>
                )}

                <div className="flex gap-2">
                  {donation.status === 'completed' && (!donation.refund_status || donation.refund_status === 'rejected') && (
                    <>
                      {donation.needs_receipt && (
                        <button
                          onClick={() => {
                            const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://api.bodam.website';
                            window.open(`${apiBaseUrl}/donations/${donation.id}/receipt`, '_blank');
                          }}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          <i className="ri-file-download-line mr-1"></i>
                          영수증 다운로드
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setSelectedDonation(donation);
                          setShowRefundModal(true);
                        }}
                        className="text-sm text-gray-600 hover:underline"
                      >
                        <i className="ri-refund-line mr-1"></i>
                        환불 요청
                      </button>
                    </>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* 환불 요청 모달 */}
        {showRefundModal && selectedDonation && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <Card className="max-w-md w-full p-6">
              <h3 className="text-xl font-bold mb-4">환불 요청</h3>
              <p className="text-sm text-gray-600 mb-4">
                {selectedDonation.fire_station.name} · {formatAmount(selectedDonation.amount)}원
              </p>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  환불 사유 <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={refundReason}
                  onChange={(e) => setRefundReason(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-3 h-24"
                  placeholder="환불 사유를 입력해주세요"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleRefundRequest}
                  variant="primary"
                  className="flex-1"
                >
                  환불 요청
                </Button>
                <Button
                  onClick={() => {
                    setShowRefundModal(false);
                    setRefundReason('');
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  취소
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
