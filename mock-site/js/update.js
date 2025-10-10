let currentIndex = 0;
let incidents = [];

async function loadIncidents() {
  try {
    const response = await fetch('data/incidents.json');
    incidents = await response.json();
    console.log(`[${new Date().toISOString()}] Loaded ${incidents.length} incidents`);
    return incidents;
  } catch (error) {
    console.error('Failed to load incidents:', error);
    return [];
  }
}

function displayIncident(incident) {
  const container = document.getElementById('current-incident');
  if (!container) {
    console.error('Container element not found');
    return;
  }

  // 상태별 색상
  const statusColors = {
    'A': '#ef4444', // 출동 중 - 빨강
    'B': '#f59e0b', // 도착 - 주황
    'C': '#10b981', // 진압 완료 - 초록
    'D': '#6b7280'  // 귀소 - 회색
  };

  const statusTexts = {
    'A': '출동 중',
    'B': '현장 도착',
    'C': '진압 완료',
    'D': '귀소'
  };

  container.innerHTML = `
    <div class="incident"
         data-id="${incident.id}"
         data-lat="${incident.axisY}"
         data-lng="${incident.axisX}"
         data-union="${incident.union}"
         data-status="${incident.status}">
      <div class="incident-header">
        <h2 class="fire-name">${incident.fireName}</h2>
        <span class="status-badge" style="background-color: ${statusColors[incident.status] || '#6b7280'}">
          ${statusTexts[incident.status] || incident.status}
        </span>
      </div>
      <div class="incident-body">
        <p class="address">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          ${incident.address}
        </p>
        <p class="time">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          발생시간: ${incident.occurrenceTime}
        </p>
        <p class="progress">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
          ${incident.progress}
        </p>
      </div>
      ${incident.casualties > 0 || incident.injured > 0 ? `
      <div class="incident-stats">
        ${incident.casualties > 0 ? `<span class="stat-item danger">사망: ${incident.casualties}명</span>` : ''}
        ${incident.injured > 0 ? `<span class="stat-item warning">부상: ${incident.injured}명</span>` : ''}
        ${incident.damageAmount > 0 ? `<span class="stat-item info">피해액: ${(incident.damageAmount / 10000).toLocaleString()}만원</span>` : ''}
      </div>
      ` : ''}
      <div class="incident-footer">
        <span class="coordinates">위도: ${incident.axisY.toFixed(4)}, 경도: ${incident.axisX.toFixed(4)}</span>
        <span class="incident-id">ID: ${incident.id}</span>
      </div>
    </div>
  `;

  console.log(`[${new Date().toISOString()}] Displaying incident #${currentIndex + 1}: ${incident.fireName} - ${incident.progress}`);
}

async function rotateIncidents() {
  await loadIncidents();

  if (incidents.length === 0) {
    console.error('No incidents to display');
    return;
  }

  function showNext() {
    displayIncident(incidents[currentIndex]);
    console.log(`[${new Date().toISOString()}] Current index: ${currentIndex + 1}/${incidents.length}`);
    currentIndex = (currentIndex + 1) % incidents.length;
  }

  // 초기 표시
  showNext();

  // 5분(300초 = 300000ms)마다 갱신
  // 테스트용으로 10초로 설정 (실제 배포 시 300000으로 변경)
  const rotationInterval = 10000; // 10초 (개발용)
  // const rotationInterval = 300000; // 5분 (프로덕션용)

  setInterval(showNext, rotationInterval);
  console.log(`[${new Date().toISOString()}] Rotation started with ${rotationInterval}ms interval`);
}

// 페이지 로드 시 실행
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', rotateIncidents);
} else {
  rotateIncidents();
}
