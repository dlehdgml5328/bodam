const NAVER_MAPS_KEY = process.env.NEXT_PUBLIC_NAVER_MAPS_KEY ?? '';

declare global {
  interface Window {
    naver?: unknown;
  }
}

export function loadNaverMapsScript(): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.resolve();
  }

  if (window.naver) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = `https://openapi.map.naver.com/openapi/v3/maps.js?ncpClientId=${NAVER_MAPS_KEY}`;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('네이버 지도 스크립트를 불러오지 못했습니다'));
    document.body.appendChild(script);
  });
}
