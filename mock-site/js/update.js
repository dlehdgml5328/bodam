let currentIndex = 0;
let incidents = [];
let displayedIncidents = [];

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

function createTableRow(incident) {
  const statusColors = {
    'A': '#ef4444',
    'B': '#f59e0b',
    'C': '#10b981',
    'D': '#6b7280'
  };

  const statusTexts = {
    'A': '출동중',
    'B': '도착',
    'C': '진압완료',
    'D': '귀소'
  };

  const casualties = incident.casualties + incident.injured;
  const damageText = incident.damageAmount > 0
    ? `${(incident.damageAmount / 10000).toLocaleString()}만원`
    : '-';

  return `
    <tr data-id="${incident.id}"
        data-lat="${incident.axisY}"
        data-lng="${incident.axisX}"
        data-date="${incident.occurrenceDate}">
      <td>${incident.fireName}</td>
      <td>${incident.occurrenceDate} ${incident.occurrenceTime}</td>
      <td>${incident.address}</td>
      <td><span class="status-badge" style="background-color: ${statusColors[incident.status] || '#6b7280'}">${statusTexts[incident.status]}</span></td>
      <td>${incident.progress}</td>
      <td>${casualties > 0 ? `${casualties}명` : '-'}</td>
      <td>${damageText}</td>
    </tr>
  `;
}

function renderTable() {
  const tbody = document.getElementById('incidents-tbody');
  if (!tbody) {
    console.error('Table tbody not found');
    return;
  }

  // 최신 데이터가 위로 오도록 역순 정렬 (날짜+시간 기준)
  const sorted = [...displayedIncidents].sort((a, b) => {
    const dateA = new Date(a.occurrenceDate + ' ' + a.occurrenceTime);
    const dateB = new Date(b.occurrenceDate + ' ' + b.occurrenceTime);
    return dateB - dateA; // 최신이 먼저 (내림차순)
  });

  tbody.innerHTML = sorted.map(inc => createTableRow(inc)).join('');

  // 최근 갱신 시간 업데이트
  document.getElementById('last-updated').textContent = new Date().toLocaleString('ko-KR');
}

async function rotateIncidents() {
  await loadIncidents();

  if (incidents.length === 0) {
    console.error('No incidents to display');
    return;
  }

  // 초기 5개 표시
  displayedIncidents = incidents.slice(0, 5);
  currentIndex = 4;
  renderTable();
  console.log(`[${new Date().toISOString()}] Initial 5 incidents displayed`);

  // 10초마다 1개씩 추가 (테스트용, 프로덕션에서는 300000ms = 5분)
  const rotationInterval = 10000; // 10초 (개발용)
  // const rotationInterval = 300000; // 5분 (프로덕션용)

  setInterval(() => {
    currentIndex = (currentIndex + 1) % incidents.length;

    // 새 데이터를 배열 뒤에 추가 (reverse하면 위로 표시됨)
    const newIncident = incidents[currentIndex];
    if (!displayedIncidents.find(inc => inc.id === newIncident.id)) {
      displayedIncidents.push(newIncident); // 배열 뒤에 추가 (reverse하면 상단에 표시)
      renderTable();
      console.log(`[${new Date().toISOString()}] New incident added at top: ${newIncident.fireName} (Total: ${displayedIncidents.length})`);
    }
  }, rotationInterval);

  console.log(`[${new Date().toISOString()}] Rotation started - adding 1 every ${rotationInterval/1000}s`);
}

// 페이지 로드 시 실행
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', rotateIncidents);
} else {
  rotateIncidents();
}
