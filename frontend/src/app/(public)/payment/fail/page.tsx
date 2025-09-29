'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import Card from '@/components/base/Card';
import Button from '@/components/base/Button';

export default function PaymentFailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const code = searchParams.get('code');
  const message = searchParams.get('message');

  const handleRetryPayment = () => {
    router.push('/donations');
  };

  const handleGoHome = () => {
    router.push('/');
  };

  const getErrorMessage = (code: string | null) => {
    switch (code) {
      case 'PAY_PROCESS_CANCELED':
        return '사용자가 결제를 취소했습니다.';
      case 'PAY_PROCESS_ABORTED':
        return '결제 진행 중 오류가 발생했습니다.';
      case 'REJECT_CARD_COMPANY':
        return '카드사에서 결제를 거절했습니다.';
      default:
        return message || '결제 중 오류가 발생했습니다.';
    }
  };

  return (
    <div className="bg-gray-50">
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <i className="ri-close-line text-red-600 text-4xl"></i>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            결제가 실패했습니다
          </h1>
          <p className="text-lg text-gray-600">
            결제 진행 중 문제가 발생했습니다. 다시 시도해주세요.
          </p>
        </div>

        <Card className="p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            오류 정보
          </h2>
          
          <div className="bg-red-50 p-6 rounded-lg border border-red-200 mb-6">
            <div className="flex items-start space-x-3">
              <i className="ri-error-warning-line text-red-600 text-xl mt-0.5"></i>
              <div>
                <h4 className="font-medium text-red-900 mb-2">결제 실패 사유</h4>
                <p className="text-red-700">
                  {getErrorMessage(code)}
                </p>
                {code && (
                  <p className="text-sm text-red-600 mt-2">
                    오류 코드: {code}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* 해결 방법 안내 */}
          <div className="bg-blue-50 p-6 rounded-lg border border-blue-200 mb-6">
            <h4 className="font-medium text-blue-900 mb-3">해결 방법</h4>
            <ul className="text-sm text-blue-700 space-y-2">
              <li className="flex items-start space-x-2">
                <i className="ri-check-line text-blue-600 mt-0.5"></i>
                <span>카드 정보가 정확한지 확인해주세요</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="ri-check-line text-blue-600 mt-0.5"></i>
                <span>카드 한도가 충분한지 확인해주세요</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="ri-check-line text-blue-600 mt-0.5"></i>
                <span>다른 결제 수단을 이용해보세요</span>
              </li>
              <li className="flex items-start space-x-2">
                <i className="ri-check-line text-blue-600 mt-0.5"></i>
                <span>잠시 후 다시 시도해주세요</span>
              </li>
            </ul>
          </div>

          {/* 액션 버튼들 */}
          <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
            <Button 
              variant="outline" 
              size="lg" 
              className="flex-1"
              onClick={handleGoHome}
            >
              <i className="ri-home-line mr-2"></i>
              홈으로 돌아가기
            </Button>
            <Button 
              variant="primary"
              size="lg" 
              className="flex-1 bg-red-600 hover:bg-red-700"
              onClick={handleRetryPayment}
            >
              <i className="ri-refresh-line mr-2"></i>
              다시 기부하기
            </Button>
          </div>
        </Card>

        {/* 고객센터 안내 */}
        <Card className="p-6 bg-gray-50">
          <div className="text-center">
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              문제가 지속된다면?
            </h3>
            <p className="text-gray-700 mb-4">
              계속해서 결제에 문제가 발생한다면 고객센터로 문의해주세요
            </p>
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <i className="ri-phone-line text-blue-600"></i>
                <span>1588-0000</span>
              </div>
              <div className="flex items-center space-x-2">
                <i className="ri-mail-line text-blue-600"></i>
                <span>support@example.com</span>
              </div>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
