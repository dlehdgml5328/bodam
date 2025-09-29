import Image from 'next/image';

export default function Footer() {
  const quickLinks = [
    { name: '개인정보처리방침', href: '#' },
    { name: '이용약관', href: '#' },
    { name: '기부투명성 보고서', href: '#' },
    { name: '소방청 공식 사이트', href: 'https://www.nfa.go.kr' },
  ];

  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* 회사 정보 */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Image
                src="https://static.readdy.ai/image/a6fb1ef394d2037130d9baf3b5296fbe/f110ca539031b1c7ee3df39fb987a51f.png"
                alt="BoDam Logo"
                width={80}
                height={80}
                className="w-20 h-20 object-contain"
                priority
              />
            </div>
            <p className="text-gray-400 mb-4">
              24시간 우리를 지키는 소방관들에게
              <br />
              따뜻한 커피로 감사의 마음을 전합니다.
            </p>
          </div>

          {/* 연락처 */}
          <div>
            <h3 className="text-lg font-semibold mb-4">문의</h3>
            <div className="space-y-2 text-gray-400">
              <div className="flex items-center space-x-2">
                <i className="ri-mail-line"></i>
                <span>bodam@bodamto119.kr</span>
              </div>
              <div className="flex items-center space-x-2">
                <i className="ri-phone-line"></i>
                <span>02-1234-5678</span>
              </div>
            </div>
          </div>

          {/* 링크 */}
          <div>
            <h3 className="text-lg font-semibold mb-4">바로가기</h3>
            <div className="space-y-2">
              {quickLinks.map((link) => (
                <a
                  key={link.name}
                  href={link.href}
                  className="block text-gray-400 hover:text-white transition-colors duration-200"
                >
                  {link.name}
                </a>
              ))}
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 flex flex-col sm:flex-row justify-between items-center">
          <p className="text-gray-400 text-sm">© 2024 보담. All rights reserved.</p>
          <div className="mt-4 sm:mt-0">
            <a
              href="https://readdy.ai/?origin=logo"
              className="text-gray-400 hover:text-white text-sm transition-colors duration-200"
            >
              Made with Readdy
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
