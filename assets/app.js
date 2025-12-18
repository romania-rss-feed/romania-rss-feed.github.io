// Romania RSS Feed - Main Application Script

const API_BASE = 'https://social.5th.ro/api/v1';
let profilesData = [];
let filteredProfiles = [];

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
  await loadProfiles();
  setupSearch();
  updateStats();
  renderProfiles();
});

// Load profiles data
async function loadProfiles() {
  try {
    const response = await fetch('/data/profiles.json');
    if (!response.ok) throw new Error('Failed to load profiles');
    profilesData = await response.json();
    filteredProfiles = [...profilesData];
  } catch (error) {
    console.error('Error loading profiles:', error);
    showError('Nu s-au putut încărca profilurile. Te rugăm să reîmprospătezi pagina.');
  }
}

// Setup search functionality
function setupSearch() {
  const searchInput = document.getElementById('searchInput');
  const sortSelect = document.getElementById('sortSelect');
  
  if (searchInput) {
    searchInput.addEventListener('input', handleSearch);
  }
  
  if (sortSelect) {
    sortSelect.addEventListener('change', handleSort);
  }
}

// Handle search
function handleSearch(e) {
  const query = e.target.value.toLowerCase().trim();
  
  if (!query) {
    filteredProfiles = [...profilesData];
  } else {
    filteredProfiles = profilesData.filter(profile => {
      const name = (profile.display_name || profile.username || '').toLowerCase();
      const username = (profile.username || '').toLowerCase();
      const description = (profile.note || '').toLowerCase();
      const searchTerm = query.toLowerCase();
      
      return name.includes(searchTerm) || 
             username.includes(searchTerm) || 
             description.includes(searchTerm);
    });
  }
  
  updateResultsCount();
  renderProfiles();
}

// Handle sort
function handleSort(e) {
  const sortBy = e.target.value;
  
  filteredProfiles.sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return (a.display_name || a.username || '').localeCompare(b.display_name || b.username || '');
      case 'posts':
        return (b.statuses_count || 0) - (a.statuses_count || 0);
      case 'followers':
        return (b.followers_count || 0) - (a.followers_count || 0);
      case 'recent':
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      default:
        return 0;
    }
  });
  
  renderProfiles();
}

// Update results count
function updateResultsCount() {
  const countEl = document.getElementById('resultsCount');
  if (countEl) {
    countEl.textContent = filteredProfiles.length;
  }
}

// Update statistics
function updateStats() {
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

// Animate value counter
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

// Format number with commas
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Render profiles grid
function renderProfiles() {
  const grid = document.getElementById('profilesGrid');
  if (!grid) return;
  
  if (filteredProfiles.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <p>Nu s-au găsit profiluri care să corespundă criteriilor de căutare.</p>
      </div>
    `;
    return;
  }
  
  grid.innerHTML = filteredProfiles.map(profile => createProfileCard(profile)).join('');
  
  // Add click handlers
  grid.querySelectorAll('.profile-card').forEach((card, index) => {
    card.addEventListener('click', () => {
      const profile = filteredProfiles[index];
      window.location.href = `/profiles/${encodeURIComponent(profile.username)}/`;
    });
  });
}

  // Get rel attribute based on instance
  function getRelAttribute(username, instance) {
    if (!instance || instance === 'mstdn.ro') {
      return 'noopener nofollow';
    }
    
    // For social.5th.ro: always dofollow (noopener only)
    return 'noopener';
  }

// Create profile card HTML
function createProfileCard(profile) {
  const displayName = profile.display_name || profile.username || 'Fără nume';
  const username = profile.username || '';
  const description = profile.note || 'Fără descriere';
  const avatar = profile.avatar || '';
  const avatarInitial = displayName.charAt(0).toUpperCase();
  const posts = profile.statuses_count || 0;
  const followers = profile.followers_count || 0;
  const following = profile.following_count || 0;
  const instance = profile.instance || 'social.5th.ro';
  const relAttr = getRelAttribute(username, instance);
  
  return `
    <div class="profile-card">
      <div class="profile-header">
        <div class="profile-avatar">
          ${avatar ? `<img src="${avatar}" alt="${displayName}" width="64" height="64" loading="lazy" decoding="async" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" style="width:100%;height:100%;object-fit:cover;border-radius:var(--radius);">
          <span style="display:none;">${avatarInitial}</span>` : `<span>${avatarInitial}</span>`}
        </div>
        <div class="profile-info">
          <h3 class="profile-name">${escapeHtml(displayName)}</h3>
          <p class="profile-username">@${escapeHtml(profile.acct || `${username}@${instance}`)}</p>
        </div>
      </div>
      <p class="profile-description">${escapeHtml(stripHtml(description))}</p>
      <div class="profile-stats">
        <div class="profile-stat">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
          </svg>
          <strong>${formatNumber(posts)}</strong> postări
        </div>
        <div class="profile-stat">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          <strong>${formatNumber(followers)}</strong> urmăritori
        </div>
      </div>
    </div>
  `;
}

// Utility functions
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function stripHtml(html) {
  const div = document.createElement('div');
  div.innerHTML = html;
  return div.textContent || div.innerText || '';
}

function showError(message) {
  const grid = document.getElementById('profilesGrid');
  if (grid) {
    grid.innerHTML = `
      <div class="empty-state">
        <p style="color: var(--accent-2);">${escapeHtml(message)}</p>
      </div>
    `;
  }
}

// Export for use in other pages
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { loadProfiles, formatNumber, escapeHtml, stripHtml };
}

