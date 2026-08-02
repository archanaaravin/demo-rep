
const MAX_PHOTOS = 5;
const MAX_SIZE_MB = 5;
let uploadedPhotos = [];

/* ---------- Navigation ---------- */
document.querySelectorAll('#navlinks button').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('#navlinks button').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    const target = btn.dataset.page;
    document.querySelectorAll('.page').forEach(p=>p.classList.add('hidden'));
    document.getElementById('page-'+target).classList.remove('hidden');
    if(target === 'dashboard' && window._map) setTimeout(()=>window._map.invalidateSize(), 50);
  });
});

/* ---------- Dark / glow toggle ---------- */
document.getElementById('darkToggle').addEventListener('click', ()=>{
  document.body.classList.toggle('glow-off');
});

/* ---------- Alert bar dismiss ---------- */
document.getElementById('alertDismiss').addEventListener('click', ()=>{
  document.getElementById('alertBar').style.display = 'none';
});

/* ---------- Stat counters ---------- */
function animateStats(){
  document.querySelectorAll('.stat-num[data-target]').forEach(el=>{
    const target = parseFloat(el.dataset.target);
    const suffix = el.dataset.suffix || '';
    const isFloat = target % 1 !== 0;
    let cur = 0;
    const step = target / 30;
    const iv = setInterval(()=>{
      cur += step;
      if(cur >= target){ cur = target; clearInterval(iv); }
      el.textContent = (isFloat ? cur.toFixed(1) : Math.round(cur)) + suffix;
    }, 25);
  });
}

/* ---------- Leaflet map ---------- */
function initMap(){
  const map = L.map('map', { zoomControl:true, attributionControl:false }).setView([13.0827, 80.2707], 12);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

  const hotspots = [
    { lat:13.0067, lng:80.1998, risk:'High',   label:'Kathipara Junction' },
    { lat:13.0850, lng:80.2101, risk:'Medium', label:'Anna Nagar Roundabout' },
    { lat:12.9986, lng:80.2593, risk:'High',   label:'ECR Thiruvanmiyur' },
    { lat:12.9789, lng:80.2201, risk:'Medium', label:'Velachery Main Road' },
    { lat:13.0300, lng:80.2200, risk:'Low',    label:'Guindy Bridge' },
    { lat:13.0475, lng:80.2400, risk:'Medium', label:'Kilpauk Junction' },
  ];
  const colors = { High:'#EF4444', Medium:'#F97316', Low:'#22C55E' };

  window._hotspotLayer = L.layerGroup(hotspots.map(h=>{
    return L.circleMarker([h.lat,h.lng], {
      radius:9, color:colors[h.risk], weight:2, fillColor:colors[h.risk], fillOpacity:0.55
    }).bindPopup(`<b>${h.label}</b><br>Risk: ${h.risk}`);
  })).addTo(map);

  window._map = map;
}

/* ---------- Map control toggles ---------- */
document.getElementById('toggleHotspotsBtn').addEventListener('click', function(){
  this.classList.toggle('active');
  if(!window._hotspotLayer || !window._map) return;
  if(this.classList.contains('active')) window._map.addLayer(window._hotspotLayer);
  else window._map.removeLayer(window._hotspotLayer);
});
document.getElementById('toggleHeatmapBtn').addEventListener('click', function(){
  this.classList.toggle('active');
});

/* ---------- Route planner ---------- */
document.getElementById('findRouteBtn').addEventListener('click', ()=>{
  const from = document.getElementById('routeFrom').value.trim();
  const to = document.getElementById('routeTo').value.trim();
  const results = document.getElementById('routeResults');
  if(!from || !to){
    alert('Enter both a starting point and a destination.');
    return;
  }
  results.classList.add('show');
});

/* ================= CITIZEN PHOTO UPLOADER ================= */
const uploadZone   = document.getElementById('uploadZone');
const fileInput    = document.getElementById('fileInput');
const previewGrid  = document.getElementById('previewGrid');
const uploadError  = document.getElementById('uploadError');

uploadZone.addEventListener('click', ()=> fileInput.click());

uploadZone.addEventListener('dragover', e=>{
  e.preventDefault();
  uploadZone.classList.add('drag');
});
uploadZone.addEventListener('dragleave', ()=> uploadZone.classList.remove('drag'));
uploadZone.addEventListener('drop', e=>{
  e.preventDefault();
  uploadZone.classList.remove('drag');
  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', e=>{
  handleFiles(e.target.files);
  fileInput.value = '';
});

function handleFiles(fileList){
  uploadError.textContent = '';
  const files = Array.from(fileList);

  for(const file of files){
    if(!file.type.startsWith('image/')){
      uploadError.textContent = 'Only image files are allowed.';
      continue;
    }
    if(uploadedPhotos.length >= MAX_PHOTOS){
      uploadError.textContent = `You can attach up to ${MAX_PHOTOS} photos.`;
      break;
    }
    if(file.size > MAX_SIZE_MB * 1024 * 1024){
      uploadError.textContent = `"${file.name}" exceeds ${MAX_SIZE_MB}MB and was skipped.`;
      continue;
    }
    const reader = new FileReader();
    reader.onload = ev=>{
      uploadedPhotos.push({ name:file.name, dataUrl:ev.target.result });
      renderPreviews();
    };
    reader.readAsDataURL(file);
  }
}

function renderPreviews(){
  previewGrid.innerHTML = '';
  uploadedPhotos.forEach((p, idx)=>{
    const thumb = document.createElement('div');
    thumb.className = 'preview-thumb';
    thumb.innerHTML = `<img src="${p.dataUrl}" alt="${p.name}"><button class="preview-remove" data-idx="${idx}" title="Remove">✕</button>`;
    previewGrid.appendChild(thumb);
  });
  document.querySelectorAll('.preview-remove').forEach(btn=>{
    btn.addEventListener('click', e=>{
      const i = parseInt(e.currentTarget.dataset.idx, 10);
      uploadedPhotos.splice(i, 1);
      renderPreviews();
    });
  });
}

function resetUploader(){
  uploadedPhotos = [];
  previewGrid.innerHTML = '';
  uploadError.textContent = '';
}

/* ================= REPORT MODAL ================= */
const reportModal = document.getElementById('reportModal');

function openModal(){ reportModal.classList.add('show'); }
function closeModal(){ reportModal.classList.remove('show'); }

document.getElementById('openReportModalBtn').addEventListener('click', openModal);
document.getElementById('cancelReportBtn').addEventListener('click', closeModal);
reportModal.addEventListener('click', e=>{ if(e.target === reportModal) closeModal(); });

document.getElementById('submitReportBtn').addEventListener('click', ()=>{
  const loc  = document.getElementById('repLoc').value.trim();
  const type = document.getElementById('repType').value;
  const sev  = document.getElementById('repSev').value;
  const desc = document.getElementById('repDesc').value.trim();

  if(!loc){
    alert('Please enter a location or junction name.');
    return;
  }

  const report = {
    id: Date.now(),
    loc, type, sev, desc,
    photos: uploadedPhotos.map(p=>p.dataUrl),
    time: new Date().toLocaleString('en-IN', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' })
  };

  const stored = JSON.parse(localStorage.getItem('aegisReports') || '[]');
  stored.unshift(report);
  localStorage.setItem('aegisReports', JSON.stringify(stored));

  document.getElementById('repLoc').value = '';
  document.getElementById('repDesc').value = '';
  resetUploader();
  closeModal();

  showAlert(`🚨 New citizen report received: ${type} at ${loc}${report.photos.length ? ` (${report.photos.length} photo${report.photos.length>1?'s':''})` : ''}.`);
  renderTimeline();
  updateReportCount();
});

function showAlert(msg){
  const bar = document.getElementById('alertBar');
  document.getElementById('alertText').textContent = msg;
  bar.style.display = 'flex';
}

/* ================= LIGHTBOX ================= */
const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightboxImg');
document.getElementById('lightboxClose').addEventListener('click', ()=> lightbox.classList.remove('show'));
lightbox.addEventListener('click', e=>{ if(e.target === lightbox) lightbox.classList.remove('show'); });

function openLightbox(src){
  lightboxImg.src = src;
  lightbox.classList.add('show');
}

/* ================= INCIDENT HISTORY / TIMELINE ================= */
let historyRecords = [];
let currentFilter = 'all';

function getAllIncidents(){
  const stored = JSON.parse(localStorage.getItem('aegisReports') || '[]');
  return [...stored, ...historyRecords];
}

const sevColor = { Fatal:'var(--red)', Major:'var(--orange)', Minor:'var(--green)' };
const sevPill  = { Fatal:'pill-red', Major:'pill-orange', Minor:'pill-green' };

function renderTimeline(){
  const timeline = document.getElementById('timeline');
  const all = getAllIncidents().filter(i=> currentFilter==='all' || i.severity===currentFilter);
  timeline.innerHTML = '';

  if(all.length === 0){
    timeline.innerHTML = '<div class="tl-empty">No incidents match this filter yet.</div>';
    return;
  }

  all.forEach(inc=>{
    const item = document.createElement('div');
    item.className = 'tl-item glass';
    item.innerHTML = `
      <div class="tl-dot" style="background:${sevColor[inc.severity]}"></div>
      <div class="tl-body">
        <div class="tl-top">
          <span class="tl-loc">${inc.loc}</span>
          <span class="pill ${sevPill[inc.severity]}">${inc.severity} Severity</span>
        </div>
        <div class="tl-time">${inc.type} · ${inc.time}</div>
        <div class="tl-desc">${inc.desc || 'No additional description provided.'}</div>
        ${inc.photos && inc.photos.length ? `<div class="tl-photos">${inc.photos.map(src=>`<img src="${src}">`).join('')}</div>` : ''}
      </div>`;
    timeline.appendChild(item);

    item.querySelectorAll('.tl-photos img').forEach(img=>{
      img.addEventListener('click', ()=> openLightbox(img.src));
    });
  });
}

document.getElementById('filterRow').addEventListener('click', e=>{
  const chip = e.target.closest('.filter-chip');
  if(!chip) return;
  document.querySelectorAll('.filter-chip').forEach(c=>c.classList.remove('on'));
  chip.classList.add('on');
  currentFilter = chip.dataset.f;
  renderTimeline();
});

function updateReportCount(){
  const stored = JSON.parse(localStorage.getItem('aegisReports') || '[]');
  const el = document.getElementById('citizenReportCount');
  el.dataset.target = stored.length;
  el.textContent = stored.length;
}

/* ================= SOS / EMERGENCY ================= */
document.getElementById('sosBtn').addEventListener('click', ()=>{
  document.getElementById('emergPanel').classList.toggle('show');
});

/* ================= CHARTS ================= */
function buildCharts(){
  const dark = { grid:{ color:'rgba(255,255,255,0.06)' }, ticks:{ color:'#8b93a7', font:{ size:10 } } };
  const legendOff = { legend:{ display:false } };

  window.govResourcesChart = new Chart(document.getElementById('chartGovResources'), {
    type:'doughnut',
    data:{ labels:['Patrol Units','Ambulances','Traffic Marshals','Tow Units'],
      datasets:[{ data:[12,6,20,4], backgroundColor:['#06b6d4','#ef4444','#f97316','#22c55e'], borderWidth:0 }] },
    options:{ plugins:{ legend:{ position:'bottom', labels:{ color:'#8b93a7', font:{ size:10 } } } } }
  });

  window.govResponseChart = new Chart(document.getElementById('chartGovResponse'), {
    type:'line',
    data:{ labels:['W1','W2','W3','W4'],
      datasets:[
        { label:'Actual', data:[7.2,6.8,6.1,5.8], borderColor:'#06b6d4', tension:0.4 },
        { label:'Target', data:[6,6,6,6], borderColor:'#8b93a7', borderDash:[4,4], tension:0 }
      ]},
    options:{ scales:{ x:dark, y:dark }, plugins:{ legend:{ labels:{ color:'#8b93a7', font:{ size:10 } } } } }
  });

  window.govSignalChart = new Chart(document.getElementById('chartGovSignal'), {
    type:'bar',
    data:{ labels:['Kathipara','Anna Nagar','ECR','Velachery'],
      datasets:[{ data:[22,15,30,18], backgroundColor:'#3b82f6', borderRadius:6 }] },
    options:{ scales:{ x:dark, y:dark }, plugins:legendOff }
  });

  window.monthlyChart = new Chart(document.getElementById('chartMonthly'), {
    type:'bar',
    data:{ labels:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
      datasets:[{ data:[0,0,0,0,0,0,0,0,0,0,0,0], backgroundColor:'#06b6d4', borderRadius:6 }] },
    options:{ scales:{ x:dark, y:dark }, plugins:legendOff }
  });

  window.severityChart = new Chart(document.getElementById('chartSeverity'), {
    type:'doughnut',
    data:{ labels:['Minor','Major','Fatal'],
      datasets:[{ data:[0,0,0], backgroundColor:['#22c55e','#f97316','#ef4444'], borderWidth:0 }] },
    options:{ plugins:{ legend:{ position:'bottom', labels:{ color:'#8b93a7', font:{ size:10 } } } } }
  });

  window.timeChart = new Chart(document.getElementById('chartTime'), {
    type:'line',
    data:{ labels:['Early Morning','Morning','Afternoon','Evening','Night','Late Night'],
      datasets:[{ data:[0,0,0,0,0,0], borderColor:'#f97316', backgroundColor:'rgba(249,115,22,0.15)', fill:true, tension:0.4 }] },
    options:{ scales:{ x:dark, y:dark }, plugins:legendOff }
  });

  window.accuracyChart = new Chart(document.getElementById('chartAccuracy'), {
    type:'line',
    data:{ labels:['W1','W2','W3','W4','W5','W6','W7','W8'],
      datasets:[{ data:[0,0,0,0,0,0,0,0], borderColor:'#22c55e', tension:0.4 }] },
    options:{ scales:{ x:dark, y:dark }, plugins:legendOff }
  });
}

const API_BASE = window.location.host.includes('8000') ? '' : 'http://127.0.0.1:8000';
console.debug('API_BASE set to', API_BASE || 'relative origin');

async function fetchDatasetSummary(){
  try {
    const response = await fetch(`${API_BASE}/accidents/summary`);
    if(!response.ok) throw new Error(`Status ${response.status}`);
    const summary = await response.json();
    updateDashboardFromSummary(summary);
    return summary;
  } catch(err) {
    console.warn('Unable to fetch dataset summary:', err);
    return null;
  }
}

async function fetchGovernmentData(){
  try {
    const [hotspotResponse, summary] = await Promise.all([
      fetch(`${API_BASE}/accidents/hotspots?limit=6`),
      fetchDatasetSummary(),
    ]);

    let hotspots = [];
    if(hotspotResponse.ok){
      hotspots = await hotspotResponse.json();
    }
    populateGovernmentTable(hotspots);
    updateGovernmentCharts(summary, hotspots);
  } catch(err) {
    console.warn('Unable to fetch government dashboard data:', err);
  }
}

async function fetchAnalyticsData(){
  try {
    const [monthlyResp, severityResp, timeResp, accuracyResp] = await Promise.all([
      fetch(`${API_BASE}/accidents/analytics/monthly`),
      fetch(`${API_BASE}/accidents/analytics/severity`),
      fetch(`${API_BASE}/accidents/analytics/timeofday`),
      fetch(`${API_BASE}/accidents/analytics/accuracy`),
    ]);

    if(monthlyResp.ok){
      const monthly = await monthlyResp.json();
      window.monthlyChart.data.datasets[0].data = monthly.map(item => item.count);
      window.monthlyChart.update();
    }

    if(severityResp.ok){
      const severity = await severityResp.json();
      const labels = Object.keys(severity);
      const values = Object.values(severity);
      window.severityChart.data.labels = labels;
      window.severityChart.data.datasets[0].data = values;
      window.severityChart.update();
    }

    if(timeResp.ok){
      const timeData = await timeResp.json();
      const labels = timeData.map(item => item.time);
      const values = timeData.map(item => item.count);
      window.timeChart.data.labels = labels;
      window.timeChart.data.datasets[0].data = values;
      window.timeChart.update();
    }

    if(accuracyResp.ok){
      const accuracy = await accuracyResp.json();
      window.accuracyChart.data.datasets[0].data = accuracy.trend || [];
      window.accuracyChart.update();
      const accEl = document.getElementById('accuracySummary');
      if(accEl){
        accEl.textContent = `${accuracy.accuracy ?? 0}% model accuracy based on dataset validation`;
      }
    }
  } catch(err) {
    console.warn('Unable to fetch analytics dashboard data:', err);
  }
}

async function fetchIncidentHistory(){
  const timeline = document.getElementById('timeline');
  if(timeline){
    timeline.innerHTML = '<div class="tl-empty">Loading incident history from backend...</div>';
  }

  try {
    const response = await fetch(`${API_BASE}/accidents/history?limit=30`);
    if(!response.ok) throw new Error(`Status ${response.status}`);
    historyRecords = await response.json();
    console.debug('Incident history loaded:', historyRecords.length, 'records');
    renderTimeline();
  } catch(err) {
    console.warn('Unable to fetch incident history:', err);
    if(timeline){
      timeline.innerHTML = `<div class="tl-empty">Unable to load incident history: ${err.message}</div>`;
    }
    renderTimeline();
  }
}

function populateGovernmentTable(hotspots){
  const tbody = document.getElementById('govHotspotTableBody');
  if(!tbody) return;
  tbody.innerHTML = '';

  if(!hotspots || hotspots.length === 0){
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-dim);padding:24px;">No hotspot data available from backend.</td></tr>';
    return;
  }

  hotspots.forEach((row)=>{
    const risk = row.total_accidents >= 22 ? 'Critical' : row.total_accidents >= 14 ? 'Elevated' : 'Moderate';
    const primary = row.total_accidents >= 20 ? 'Overspeeding / Merge' : row.total_accidents >= 12 ? 'Signal congestion' : 'Visibility / road quality';
    const action = row.total_accidents >= 18 ? 'Pending Review' : row.total_accidents >= 10 ? 'Actioned' : 'Monitoring';
    const statusClass = action === 'Actioned' ? 'pill-green' : action === 'Pending Review' ? 'pill-blue' : 'pill-orange';
    const riskClass = risk === 'Critical' ? 'pill-red' : risk === 'Elevated' ? 'pill-orange' : 'pill-green';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><b>${row.road_name}</b></td>
      <td><span class="pill ${riskClass}">${risk}</span></td>
      <td>${primary}</td>
      <td>${row.total_accidents} accidents</td>
      <td><span class="pill ${statusClass}">${action}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function updateGovernmentCharts(summary, hotspots){
  if(!summary) return;
  const minor = summary.severity_counts?.Minor || 0;
  const major = summary.severity_counts?.Major || 0;
  const fatal = summary.severity_counts?.Fatal || 0;

  if(window.govResourcesChart){
    window.govResourcesChart.data.datasets[0].data = [
      Math.max(2, Math.round(summary.total_records / 200)),
      Math.max(1, Math.round((major + fatal) / 5)),
      20,
      Math.max(2, Math.round(summary.hotspot_count / 8)),
    ];
    window.govResourcesChart.update();
  }

  if(window.govSignalChart){
    const labels = hotspots.slice(0, 4).map(item => item.road_name || 'Unknown');
    const data = hotspots.slice(0, 4).map(item => item.total_accidents);
    window.govSignalChart.data.labels = labels.length ? labels : ['No data'];
    window.govSignalChart.data.datasets[0].data = data.length ? data : [0];
    window.govSignalChart.update();
  }

  if(window.govResponseChart){
    const responseTimes = [
      Math.max(5, 12 - Math.round((major + fatal) / 2)),
      Math.max(5, 11 - Math.round((major + fatal) / 2)),
      Math.max(4, 10 - Math.round((major + fatal) / 2)),
      Math.max(4, 9 - Math.round((major + fatal) / 2)),
    ];
    window.govResponseChart.data.datasets[0].data = responseTimes;
    window.govResponseChart.update();
  }
}

async function runPrediction(){
  const weather = document.getElementById('predictWeather').value.trim();
  const traffic = document.getElementById('predictTraffic').value.trim();
  const road = document.getElementById('predictRoadType').value.trim();
  const speed = Number(document.getElementById('predictSpeed').value.trim());
  const time = document.getElementById('predictTimeOfDay').value.trim();
  const resultEl = document.getElementById('predictResult');

  if(!weather || !traffic || !road || !time || Number.isNaN(speed) || !speed){
    resultEl.textContent = 'Please fill in weather, traffic, road type, speed, and time.';
    return;
  }

  try {
    resultEl.textContent = 'Running prediction…';
    const payload = { weather, traffic, road, speed, time };
    const response = await fetch(`${API_BASE}/predict/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if(!response.ok){
      const errorText = await response.text();
      throw new Error(errorText || `Status ${response.status}`);
    }

    const data = await response.json();
    resultEl.textContent = `Predicted Risk Level: ${data.prediction}`;
    document.getElementById('riskSummary').innerHTML = `Current City Risk: <b>${data.prediction}</b><br>Model suggestion based on current input.`;
    document.getElementById('riskRingValue').textContent = data.prediction === 'High' ? '92%' : data.prediction === 'Medium' ? '68%' : '34%';
  } catch(err) {
    resultEl.textContent = `Prediction failed: ${err.message}`;
    console.warn('Prediction request failed', err);
  }
}

document.getElementById('predictBtn').addEventListener('click', runPrediction);

/* ================= INIT ================= */
document.addEventListener('DOMContentLoaded', ()=>{
  initMap();
  animateStats();
  updateReportCount();
  buildCharts();
  fetchGovernmentData();
  fetchAnalyticsData();
  fetchIncidentHistory();
});
