// Statistics Page Script

let profilesData = [];

document.addEventListener('DOMContentLoaded', async () => {
  await loadProfiles();
  updateOverviewStats();
  renderTopProfiles();
  loadServerStats();
});

async function loadProfiles() {
  try {
    const response = await fetch('/data/profiles.json');
    if (!response.ok) throw new Error('Failed to load profiles');
    profilesData = await response.json();
  } catch (error) {
    console.error('Error loading profiles:', error);
  }
}

function updateOverviewStats() {
  const totalProfiles = profilesData.length;
  const totalPosts = profilesData.reduce((sum, p) => sum + (p.statuses_count || 0), 0);
  const totalFollowers = profilesData.reduce((sum, p) => sum + (p.followers_count || 0), 0);
  const activeProfiles = profilesData.filter(p => {
    const lastStatus = p.last_status_at ? new Date(p.last_status_at) : null;
    if (!lastStatus) return false;
    const daysSince = (Date.now() - lastStatus.getTime()) / (1000 * 60 * 60 * 24);
    return daysSince <= 30;
  }).length;
  
  animateValue('totalProfiles', 0, totalProfiles, 1000);
  animateValue('totalPosts', 0, totalPosts, 1000);
  animateValue('totalFollowers', 0, totalFollowers, 1000);
  animateValue('activeProfiles', 0, activeProfiles, 1000);
}

function animateValue(id, start, end, duration) {
  const element = document.getElementById(id);
  if (!element) return;
  
  const range = end - start;
  const increment = range / (duration / 16);
  let current = start;
  
  const timer = setInterval(() => {
    current += increment;
    if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
      current = end;
      clearInterval(timer);
    }
    element.textContent = formatNumber(Math.floor(current));
  }, 16);
}

function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function renderTopProfiles() {
  // Top by posts
  const topPosts = [...profilesData]
    .sort((a, b) => (b.statuses_count || 0) - (a.statuses_count || 0))
    .slice(0, 10);
  
  const topPostsEl = document.getElementById('topPosts');
  if (topPostsEl) {
    topPostsEl.innerHTML = topPosts.map((profile, index) => `
      <div class="top-profile-item" onclick="window.location.href='/profiles/${encodeURIComponent(profile.username)}/'">
        <div class="top-profile-info">
          <div class="top-profile-rank">#${index + 1}</div>
          <div>
            <div class="top-profile-name">${escapeHtml(profile.display_name || profile.username)}</div>
            <div style="font-size: 14px; color: var(--text-muted);">@${escapeHtml(profile.username)}</div>
          </div>
        </div>
        <div class="top-profile-stat">${formatNumber(profile.statuses_count || 0)}</div>
      </div>
    `).join('');
  }
  
  // Top by followers
  const topFollowers = [...profilesData]
    .sort((a, b) => (b.followers_count || 0) - (a.followers_count || 0))
    .slice(0, 10);
  
  const topFollowersEl = document.getElementById('topFollowers');
  if (topFollowersEl) {
    topFollowersEl.innerHTML = topFollowers.map((profile, index) => `
      <div class="top-profile-item" onclick="window.location.href='/profiles/${encodeURIComponent(profile.username)}/'">
        <div class="top-profile-info">
          <div class="top-profile-rank">#${index + 1}</div>
          <div>
            <div class="top-profile-name">${escapeHtml(profile.display_name || profile.username)}</div>
            <div style="font-size: 14px; color: var(--text-muted);">@${escapeHtml(profile.username)}</div>
          </div>
        </div>
        <div class="top-profile-stat">${formatNumber(profile.followers_count || 0)}</div>
      </div>
    `).join('');
  }
}

async function loadServerStats() {
  try {
    const response = await fetch('/data/server-stats.json');
    if (!response.ok) throw new Error('Failed to load server stats');
    const stats = await response.json();
    renderServerStats(stats);
  } catch (error) {
    console.error('Error loading server stats:', error);
    const serverStatsEl = document.getElementById('serverStats');
    if (serverStatsEl) {
      serverStatsEl.innerHTML = '<p style="color: var(--text-muted);">Statisticile serverului nu sunt disponibile momentan.</p>';
    }
  }
}

function renderServerStats(stats) {
  const serverStatsEl = document.getElementById('serverStats');
  if (!serverStatsEl) return;
  
  // Handle both possible structures from API
  const version = stats.version || 'N/A';
  const statsData = stats.stats || {};
  const userCount = statsData.user_count || 0;
  const statusCount = statsData.status_count || 0;
  const domainCount = statsData.domain_count || 0;
  
  // Show loading state if no data
  if (!stats || Object.keys(stats).length === 0) {
    serverStatsEl.innerHTML = '<p style="color: var(--text-muted);">Statisticile serverului nu sunt disponibile momentan.</p>';
    return;
  }
  
  serverStatsEl.innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 24px;">
      <div>
        <div style="font-size: 14px; color: var(--text-muted); margin-bottom: 8px;">Versiune Mastodon</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--text);">${escapeHtml(version)}</div>
      </div>
      <div>
        <div style="font-size: 14px; color: var(--text-muted); margin-bottom: 8px;">Utilizatori Totali</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--text);">${formatNumber(userCount)}</div>
      </div>
      <div>
        <div style="font-size: 14px; color: var(--text-muted); margin-bottom: 8px;">Statusuri Totale</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--text);">${formatNumber(statusCount)}</div>
      </div>
      <div>
        <div style="font-size: 14px; color: var(--text-muted); margin-bottom: 8px;">Domenii Conectate</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--text);">${formatNumber(domainCount)}</div>
      </div>
    </div>
    ${stats.title ? `
    <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid var(--border);">
      <div style="font-size: 14px; color: var(--text-muted); margin-bottom: 8px;">Titlu Server</div>
      <div style="font-size: 18px; font-weight: 600; color: var(--text);">${escapeHtml(stats.title)}</div>
      ${stats.short_description ? `<div style="font-size: 14px; color: var(--text-muted); margin-top: 8px;">${escapeHtml(stats.short_description)}</div>` : ''}
    </div>
    ` : ''}
  `;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}


