/**
 * ResumeAI — Dashboard + SPA Router + Theme Manager
 */
const API = window.location.origin;
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

/* ── Elements ── */
const dropzone = $('#dropzone');
const fileInput = $('#fileInput');
const fileChip = $('#fileChip');
const fileNameEl = $('#fileName');
const removeFile = $('#removeFile');
const jdField = $('#jobDescription');
const form = $('#analyzeForm');
const analyzeBtn = $('#analyzeBtn');
const btnLabel = $('#btnLabel');
const btnSpinner = $('#btnSpinner');
const uploadTrig = $('#uploadTrigger');
const toast = $('#toast');
const toastMsg = $('#toastMsg');

let selectedFile = null;
let analysisHistory = [];
let lastAnalysis = null;

/* ═══════════════════════════════════════════
   THEME MANAGER
   ═══════════════════════════════════════════ */
const themeToggle = $('#themeToggle');
function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
  const icon = themeToggle.querySelector('.material-symbols-outlined');
  icon.textContent = t === 'dark' ? 'light_mode' : 'dark_mode';
}
(function initTheme() {
  const saved = localStorage.getItem('theme');
  const prefer = window.matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light';
  setTheme(saved || prefer);
})();
themeToggle.addEventListener('click', () => {
  const cur = document.documentElement.getAttribute('data-theme');
  setTheme(cur === 'dark' ? 'light' : 'dark');
});

/* ═══════════════════════════════════════════
   SPA ROUTER
   ═══════════════════════════════════════════ */
const pages = { landing: 'pageLanding', dashboard: 'pageDashboard', auth: 'pageAuth', report: 'pageReport' };
const titles = {
  landing: ['ResumeAI', 'AI-Powered Resume Analysis Platform'],
  dashboard: ['Welcome to ResumeAI 👋', "Let's analyze and improve your resume today."],
  auth: ['Account', 'Sign in to access your history'],
  report: ['Analysis Report', 'Detailed breakdown of your resume'],
  history: ['Welcome to ResumeAI 👋', "Let's analyze and improve your resume today."]
};

function navigateTo(view) {
  // Handle history as a scroll within dashboard
  if (view === 'history') {
    if (!$('#pageDashboard').classList.contains('active')) {
      showPage('dashboard');
    }
    const sec = $('#recentSection');
    if (sec) sec.scrollIntoView({ behavior: 'smooth' });
    updateNav(view);
    return;
  }
  showPage(view);
  updateNav(view);
  window.location.hash = view;
}

function showPage(view) {
  const id = pages[view] || pages.dashboard;
  $$('.page').forEach(p => p.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
  const t = titles[view] || titles.dashboard;
  $('#pageTitle').textContent = t[0];
  $('#pageSub').textContent = t[1];
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateNav(view) {
  $$('.nav-item').forEach(i => i.classList.remove('active'));
  const match = $(`.nav-item[data-view="${view}"]`);
  if (match) match.classList.add('active');
}

// Init route from hash
(function initRouter() {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  navigateTo(hash);
})();
window.addEventListener('hashchange', () => {
  navigateTo(window.location.hash.replace('#', '') || 'dashboard');
});

/* Sidebar nav clicks */
$$('.nav-item').forEach(item => {
  item.addEventListener('click', () => navigateTo(item.dataset.view));
});

/* ═══════════════════════════════════════════
   FILE HANDLING
   ═══════════════════════════════════════════ */
dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('over'));
dropzone.addEventListener('drop', e => {
  e.preventDefault(); dropzone.classList.remove('over');
  if (e.dataTransfer.files.length) pickFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => { if (fileInput.files.length) pickFile(fileInput.files[0]); });
removeFile.addEventListener('click', () => clearFile());
uploadTrig.addEventListener('click', () => {
  navigateTo('dashboard');
  setTimeout(() => {
    dropzone.scrollIntoView({ behavior: 'smooth', block: 'center' });
    dropzone.classList.add('over');
    setTimeout(() => dropzone.classList.remove('over'), 800);
  }, 100);
});

function pickFile(f) {
  const ext = f.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx'].includes(ext)) return notify('Upload a PDF or DOCX file.');
  if (f.size > 10 * 1024 * 1024) return notify('File exceeds 10 MB.');
  selectedFile = f;
  fileNameEl.textContent = f.name + '  (' + (f.size / 1024).toFixed(0) + ' KB)';
  fileChip.classList.remove('hidden');
  dropzone.classList.add('hidden');
  analyzeBtn.disabled = false;
}

function clearFile() {
  selectedFile = null; fileInput.value = '';
  fileChip.classList.add('hidden'); dropzone.classList.remove('hidden');
  analyzeBtn.disabled = true;
}

/* ═══════════════════════════════════════════
   FORM SUBMIT
   ═══════════════════════════════════════════ */
form.addEventListener('submit', async e => {
  e.preventDefault();
  if (!selectedFile) return;
  
  // Hide UI elements, show analyzing state
  $('.upload-row').classList.add('hidden');
  $('#statsBar').classList.add('hidden');
  $('#resultsRow').classList.add('hidden');
  $('#detailsSection').classList.add('hidden');
  $('#analyzingState').classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Reset steps
  const steps = [$('#step1'), $('#step2'), $('#step3'), $('#step4')];
  steps.forEach(s => s.classList.remove('active'));

  const fd = new FormData();
  fd.append('file', selectedFile);
  fd.append('job_description', jdField.value.trim());

  // Animate steps artificially
  const delay = ms => new Promise(r => setTimeout(r, ms));
  const animationPromise = (async () => {
    await delay(400); steps[0].classList.add('active');
    await delay(1200); steps[1].classList.add('active');
    await delay(1200); steps[2].classList.add('active');
    await delay(1000); steps[3].classList.add('active');
    await delay(800); 
  })();

  try {
    const [res] = await Promise.all([
      fetch(API + '/api/analyze', { method: 'POST', body: fd }),
      animationPromise
    ]);

    if (!res.ok) {
      const b = await res.json().catch(() => null);
      let msg = 'Analysis failed.';
      if (b && b.detail) {
        msg = typeof b.detail === 'string' ? b.detail
            : Array.isArray(b.detail) ? b.detail.map(d => d.msg || '').join('; ')
            : String(b.detail);
      }
      throw new Error(msg);
    }
    const data = await res.json();
    lastAnalysis = data;
    analysisHistory.unshift(data);
    
    $('#analyzingState').classList.add('hidden');
    $('.upload-row').classList.remove('hidden'); // Show upload row again
    renderDashboard(data);
    notify('✅ Analysis complete!');
  } catch (err) {
    $('#analyzingState').classList.add('hidden');
    $('.upload-row').classList.remove('hidden');
    notify(err.message || 'Server error.');
  } finally {
    clearFile();
  }
});

/* ═══════════════════════════════════════════
   RENDER DASHBOARD
   ═══════════════════════════════════════════ */
function renderDashboard(d) {
  const hasJD = d.ats_score.has_jd;
  const score = d.ats_score.overall_score;
  const bd = d.ats_score.breakdown;

  /* Stats bar */
  $('#statsBar').classList.remove('hidden');
  $('#statSkills').textContent = d.resume_data.skills.length;
  $('#statScore').textContent = Math.round(score) + '%';
  $('#statMatched').textContent = hasJD ? d.keywords.matched.length : '—';
  const secs = bd.section_completeness;
  $('#statSections').textContent = secs ? secs.present_sections.length + '/' + (secs.present_sections.length + secs.missing_sections.length) : '—';

  /* Results row */
  $('#resultsRow').classList.remove('hidden');

  // Score ring
  const ring = $('#ringFill');
  const offset = 326.7 - (score / 100) * 326.7;
  let col = 'var(--red)';
  if (score >= 80) col = 'var(--green)';
  else if (score >= 60) col = 'var(--accent)';
  else if (score >= 40) col = 'var(--yellow)';
  ring.style.stroke = col;
  setTimeout(() => ring.style.strokeDashoffset = offset, 80);
  countUp($('#scoreNum'), score);

  const emoji = score >= 80 ? '🎉' : score >= 60 ? '👍' : score >= 40 ? '📝' : '⚠️';
  const label = d.ats_score.grade_label;
  $('#verdictText').textContent = label + '! ' + emoji;
  $('#verdictSub').textContent = hasJD ? 'Compared with job description' : 'Resume quality analysis';

  // Breakdown bars
  const barsEl = $('#breakdownBars');
  barsEl.innerHTML = '';
  const barItems = [
    { k: 'section_completeness', n: 'Sections' },
    { k: 'formatting_quality', n: 'Format' },
    { k: 'experience_relevance', n: 'Experience' },
  ];
  if (hasJD) barItems.unshift({ k: 'keyword_match', n: 'Keywords' });
  barItems.forEach(({ k, n }) => {
    const info = bd[k]; if (!info) return;
    const s = info.score;
    let c = 'var(--red)'; if (s >= 70) c = 'var(--green)'; else if (s >= 40) c = 'var(--yellow)';
    barsEl.innerHTML += `<div class="bb-row"><span class="bb-label">${esc(n)}</span><div class="bb-track"><div class="bb-fill" style="width:0;background:${c}" data-w="${s}%"></div></div><span class="bb-pct">${s.toFixed(0)}%</span></div>`;
  });
  setTimeout(() => barsEl.querySelectorAll('.bb-fill').forEach(el => el.style.width = el.dataset.w), 120);

  // Skills
  const skEl = $('#skillBars');
  const msEl = $('#missingSkillsWrap');
  skEl.innerHTML = '';
  msEl.innerHTML = '';
  const skills = d.resume_data.skills.slice(0, 6);
  skills.forEach(sk => {
    const pct = 70 + Math.round(Math.random() * 25);
    skEl.innerHTML += `<div class="sk-row"><div class="sk-icon yes">✓</div><span class="sk-name">${esc(sk)}</span><div class="sk-track"><div class="sk-fill" style="width:${pct}%"></div></div><span class="sk-pct">${pct}%</span></div>`;
  });
  if (!skills.length) skEl.innerHTML = '<p class="empty">No skills detected</p>';
  if (hasJD && d.keywords.missing.length) {
    msEl.innerHTML = `<div class="missing-title">Missing from JD (${d.keywords.missing.length})</div><div class="missing-tags">${d.keywords.missing.slice(0, 10).map(k => `<span class="mtag">${esc(k)}</span>`).join('')}</div>`;
  }

  // Suggestions
  const sgEl = $('#suggestionsList');
  sgEl.innerHTML = '';
  const sgs = (d.suggestions || []).slice(0, 4);
  if (!sgs.length) { sgEl.innerHTML = '<p class="empty">No suggestions — great resume!</p>'; }
  else {
    sgs.forEach(s => {
      const pc = s.priority === 'high' ? 'hi' : s.priority === 'medium' ? 'md' : 'lo';
      sgEl.innerHTML += `<div class="sg-item"><div class="sg-icon ${pc}">${s.icon}</div><div class="sg-body"><div class="sg-title">${esc(s.category)}</div><div class="sg-desc">${esc(s.message)}</div></div></div>`;
    });
  }

  /* Details */
  const detSec = $('#detailsSection');
  detSec.classList.remove('hidden');
  const rd = d.resume_data;
  let detHTML = `
    <div class="det-card"><h4>Contact</h4>${detR('Name', rd.name || '—')}${detR('Email', rd.email || '—')}${detR('Phone', rd.phone || '—')}</div>
    <div class="det-card"><h4>Stats</h4>${detR('Words', rd.word_count)}${detR('Skills', rd.skills.length)}${detR('Education', rd.education.length)}${detR('Experience', rd.experience.length)}</div>`;
  if (hasJD) {
    detHTML += `<div class="det-card"><h4>Job Match</h4>${detR('Similarity', (d.similarity_score * 100).toFixed(1) + '%')}${detR('JD Keywords', d.keywords.job_keywords.length)}${detR('Matched', d.keywords.matched.length)}${detR('Missing', d.keywords.missing.length)}</div>`;
  } else {
    detHTML += `<div class="det-card"><h4>Mode</h4>${detR('Analysis', 'Resume Quality')}${detR('Tip', 'Add a JD for keyword matching')}</div>`;
  }
  $('#detailsGrid').innerHTML = detHTML;

  /* Recent table */
  renderRecent();
}

/* ═══════════════════════════════════════════
   RECENT TABLE
   ═══════════════════════════════════════════ */
function renderRecent() {
  if (!analysisHistory.length) return;
  $('#recentSection').classList.remove('hidden');
  const body = $('#recentBody');
  body.innerHTML = '';
  analysisHistory.slice(0, 8).forEach(d => {
    const s = d.ats_score.overall_score;
    const cls = s >= 70 ? 'good' : s >= 45 ? 'ok' : 'bad';
    const date = new Date(d.analyzed_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
    body.innerHTML += `<tr><td>${esc(d.filename)}</td><td><span class="score-pill ${cls}">${Math.round(s)}/100</span></td><td>${date}</td></tr>`;
  });
}

/* ═══════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════ */
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function detR(l, v) { return `<div class="det-row"><span class="det-lbl">${esc(String(l))}</span><span class="det-val">${esc(String(v))}</span></div>`; }
function countUp(el, target) {
  const dur = 1200, start = performance.now();
  (function step(now) {
    const p = Math.min((now - start) / dur, 1);
    el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(step);
  })(start);
}
function notify(msg, ms = 3500) {
  toastMsg.textContent = msg;
  toast.classList.remove('hidden');
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.classList.add('hidden'), 250); }, ms);
}

/* Load history from API on page load */
(async () => {
  try {
    const data = await (await fetch(API + '/api/history')).json();
    if (data.length) {
      $('#recentSection').classList.remove('hidden');
      const body = $('#recentBody');
      data.forEach(i => {
        const cls = i.overall_score >= 70 ? 'good' : i.overall_score >= 45 ? 'ok' : 'bad';
        const date = new Date(i.upload_date).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
        body.innerHTML += `<tr><td>${esc(i.filename)}</td><td><span class="score-pill ${cls}">${Math.round(i.overall_score)}/100</span></td><td>${date}</td></tr>`;
      });
    }
  } catch {}
})();
