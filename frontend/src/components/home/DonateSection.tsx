'use client';

import { ChangeEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import Button from '../base/Button';
import Card from '../base/Card';

export default function DonateSection() {
  const [selectedAmount, setSelectedAmount] = useState(3000);
  const [customAmount, setCustomAmount] = useState('');
  const router = useRouter();
  
  const amounts = [
    { value: 3000, cups: 1, label: '커피 1잔' },
    { value: 6000, cups: 2, label: '커피 2잔' },
    { value: 15000, cups: 5, label: '커피 5잔' },
    { value: 30000, cups: 10, label: '커피 10잔' },
    { value: 60000, cups: 20, label: '커피 20잔' },
    { value: 150000, cups: 50, label: '커피 50잔' }
  ];

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
    return customAmount ? parseInt(customAmount) : selectedAmount;
  };

  const getCupCount = (amount: number) => {
    return Math.floor(amount / 3000);
  };

  const handleDonateClick = () => {
    const amount = getCurrentAmount();
    router.push(`/donations?amount=${amount}`);
  };

  return (
    <section 
      className="py-16 bg-cover bg-center bg-no-repeat relative"
      style={{
        backgroundImage: `linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.95)), url('https://readdy.ai/api/search-image?query=Warm%20coffee%20cup%20with%20steam%20rising%2C%20cozy%20firefighter%20station%20background%2C%20warm%20orange%20and%20red%20tones%2C%20soft%20lighting%2C%20heartwarming%20atmosphere%2C%20coffee%20beans%20scattered%20around%2C%20donation%20and%20support%20theme%2C%20professional%20photography%2C%20inspiring%20and%20welcoming%20mood&width=1920&height=800&seq=donate-section-bg&orientation=landscape')`
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            소방관들에게 따뜻한 커피 한 잔을
          </h2>
          <p className="text-lg text-gray-600 mb-12">
            여러분의 작은 마음이 현장에서 힘쓰는 소방관들에게 큰 힘이 됩니다
          </p>

          <Card className="p-8 bg-white/95 backdrop-blur-sm shadow-xl">
            {/* 기부 금액 선택 */}
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">기부 금액 선택</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                {amounts.map((amount) => (
                  <button
                    key={amount.value}
                    onClick={() => handleAmountSelect(amount.value)}
                    className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                      selectedAmount === amount.value && !customAmount
                        ? 'border-red-500 bg-red-50 text-red-700'
                        : 'border-gray-200 hover:border-red-300 text-gray-700'
                    }`}
                  >
                    <div className="text-lg font-bold">{amount.value.toLocaleString()}원</div>
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
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                  <span className="text-gray-500 font-medium">원</span>
                </div>
                {customAmount && (
                  <p className="text-sm text-gray-500 mt-2">
                    커피 {getCupCount(parseInt(customAmount))}잔에 해당합니다
                  </p>
                )}
              </div>
            </div>

            {/* 선택된 금액 표시 */}
            <div className="bg-red-50 p-6 rounded-lg mb-8">
              <div className="flex items-center justify-center space-x-4">
                <div className="flex items-center space-x-2">
                  <i className="ri-cup-fill text-orange-500 text-2xl"></i>
                  <span className="text-2xl font-bold text-gray-900">
                    {getCurrentAmount().toLocaleString()}원
                  </span>
                </div>
                <div className="text-gray-600">
                  커피 {getCupCount(getCurrentAmount())}잔
                </div>
              </div>
            </div>

            {/* 기부하기 버튼 - 중앙 배치 */}
            <div className="flex justify-center">
              <Button 
                size="lg" 
                className="px-12 py-4 text-lg font-semibold"
                onClick={handleDonateClick}
              >
                <i className="ri-heart-fill mr-2"></i>
                지금 기부하기
              </Button>
            </div>

            {/* 안내 텍스트 */}
            <p className="text-sm text-gray-500 text-center mt-6">
              기부해주신 마음은 전국 소방서에 따뜻한 커피와 간식으로 전달됩니다
            </p>
          </Card>
        </div>
      </div>
    </section>
  );
}
