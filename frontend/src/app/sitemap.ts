import { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://bodam.example';

  // 정적 페이지
  const staticPages = [
    '',
    '/donations',
    '/regions',
    '/donation-ranking',
  ].map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: route === '' ? 1 : 0.8,
  }));

  // TODO: DB에서 동적 페이지 (예: 소방서 상세) 목록 가져오기
  // const fireStations = await fetch('.../api/fire-stations').then(res => res.json());
  const fireStations = [{ id: 1 }, { id: 2 }, { id: 3 }]; // 예시 데이터
  const dynamicPages = fireStations.map((station) => ({
    url: `${baseUrl}/fire-station-detail/${station.id}`,
    lastModified: new Date(),
    changeFrequency: 'weekly' as const,
    priority: 0.6,
  }));

  return [...staticPages, ...dynamicPages];
}