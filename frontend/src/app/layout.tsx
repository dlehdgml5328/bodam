import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import '../styles/globals.css';

export const metadata: Metadata = {
  title: 'BoDam',
  description: '커피 기부 플랫폼 보담(BoDam) - 소방대원 지원 서비스'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
