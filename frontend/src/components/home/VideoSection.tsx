import { getFireIncidents } from '@/lib/data/incidents';

export default async function VideoSection() {
  const incidents = await getFireIncidents(20);

  // 영상이 있는 사건만 필터링
  const incidentsWithVideos = incidents.filter(
    (incident: any) => incident.video_count && incident.video_count > 0
  );

  if (incidentsWithVideos.length === 0) {
    return null; // 영상이 없으면 섹션 숨김
  }

  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            🎥 화재 현장 영상
          </h2>
          <p className="text-gray-600">
            실시간으로 수집된 화재 현장 영상을 확인하세요
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {incidentsWithVideos.slice(0, 6).map((incident: any) =>
            incident.videos?.slice(0, 1).map((video: any, idx: number) => (
              <div
                key={`${incident.id}-${idx}`}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow"
              >
                <a
                  href={video.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  {/* 썸네일 */}
                  {video.thumbnail && (
                    <div className="relative w-full h-48 bg-gray-200">
                      <img
                        src={video.thumbnail}
                        alt={video.title}
                        className="w-full h-full object-cover"
                      />
                      {/* 재생 아이콘 오버레이 */}
                      <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 hover:bg-opacity-40 transition-opacity">
                        <svg
                          className="w-16 h-16 text-white"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </div>
                    </div>
                  )}

                  {/* 정보 */}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                      {video.title}
                    </h3>
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="mr-2">📍</span>
                      <span className="line-clamp-1">{incident.location_address}</span>
                    </div>
                    {video.published_at && (
                      <div className="text-xs text-gray-500 mt-2">
                        {new Date(video.published_at).toLocaleDateString('ko-KR')}
                      </div>
                    )}
                  </div>
                </a>
              </div>
            ))
          )}
        </div>

        {incidentsWithVideos.length > 6 && (
          <div className="text-center mt-8">
            <p className="text-gray-600">
              외 {incidentsWithVideos.length - 6}개의 영상이 더 있습니다
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
