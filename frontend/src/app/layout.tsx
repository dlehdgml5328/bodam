import type { Metadata } from 'next';
import '../styles/globals.css';

export const metadata: Metadata = {
  title: '보담 - 소방관 기부 플랫폼',
  description: '소방관들에게 따뜻한 커피와 마음을 전해주세요',
  icons: {
    icon: 'https://static.readdy.ai/image/a6fb1ef394d2037130d9baf3b5296fbe/f110ca539031b1c7ee3df39fb987a51f.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <head>
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
        />
        <link
          href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css"
          rel="stylesheet"
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Pacifico&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
