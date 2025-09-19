'use client';

import { useMemo, useState } from 'react';
import { StationMap, StationCoordinate } from '../components/map/StationMap';

const MOCK_STATIONS: StationCoordinate[] = [
  {
    id: 'station-1',
    name: '강남소방서',
    latitude: 37.498,
    longitude: 127.028,
    donationStatus: '긴급 지원 필요',
  },
  {
    id: 'station-2',
    name: '서초소방서',
    latitude: 37.487,
    longitude: 127.015,
    donationStatus: '정기 후원 진행 중',
  },
];

export default function HomePage() {
  const [keyword, setKeyword] = useState('');
  const filteredStations = useMemo(
    () =>
      MOCK_STATIONS.filter((station) =>
        station.name.toLowerCase().includes(keyword.toLowerCase())
      ),
    [keyword]
  );

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-4 py-12">
      <section className="text-center">
        <h1 className="text-4xl font-bold text-slate-900 sm:text-5xl">
          소방대원에게 커피 한 잔의 따뜻함을 전하세요
        </h1>
        <p className="mt-4 text-lg text-slate-600">
          주변 소방서를 찾아 기부 현황을 확인하고, 일시 또는 정기 기부로 응원할 수 있습니다.
        </p>
      </section>

      <section className="grid gap-6">
        <div className="flex flex-col gap-4 rounded-lg bg-white p-6 shadow">
          <label className="flex flex-col gap-2">
            <span className="text-sm text-slate-600">소방서 검색</span>
            <input
              type="text"
              placeholder="예) 강남소방서"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              className="rounded border border-slate-300 px-3 py-2 focus:border-primary focus:outline-none"
            />
          </label>
          <StationMap stations={filteredStations} />
        </div>
      </section>
    </main>
  );
}
