#!/usr/bin/env python3
"""
Generator pagini HTML pentru fiecare profil
"""

import json
import html
from pathlib import Path
from datetime import datetime

PROFILE_TEMPLATE = """<!doctype html>
<html lang="ro" dir="ltr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{display_name} (@{acct}) — Romania RSS Feed</title>
  <meta name="description" content="{description_meta}">
  <link rel="canonical" href="https://romania-rss-feed.github.io/profiles/{username}/">
  <link rel="alternate" type="application/rss+xml" title="{display_name} RSS" href="{rss_url}">
  <link rel="stylesheet" href="/assets/styles.css">
</head>
<body>
  <nav class="nav">
    <div class="nav-inner">
      <a class="brand" href="/" aria-label="Romania RSS Feed homepage">
        <svg class="brand-logo" width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="16" cy="16" r="14" fill="var(--accent)"/>
          <path d="M16 8 L20 16 L16 20 L12 16 Z" fill="var(--bg)"/>
        </svg>
        <span>Romania RSS Feed</span>
      </a>
      <div class="nav-links">
        <a href="/profiles/">Explorator</a>
        <a href="/stats/">Statistici</a>
        <a href="/feed.xml">RSS Feed</a>
        <a href="https://social.5th.ro/" target="_blank" rel="noopener">Mastodon</a>
      </div>
    </div>
  </nav>

  <main class="container">
    <div class="profile-page">
      <div class="profile-banner"></div>
      <div class="profile-header-large">
        <div class="profile-avatar-large">
          {avatar_html}
        </div>
        <div class="profile-details">
          <h1 class="profile-name-large">{display_name}</h1>
          <p class="profile-username-large">@{acct}</p>
          <div class="profile-description-large">{description}</div>
        </div>
      </div>

      <div class="profile-stats-large">
        <div class="profile-stat-large">
          <div class="stat-value">{statuses_count}</div>
          <div class="stat-label">Postări</div>
        </div>
        <div class="profile-stat-large">
          <div class="stat-value">{followers_count}</div>
          <div class="stat-label">Urmăritori</div>
        </div>
        <div class="profile-stat-large">
          <div class="stat-value">{following_count}</div>
          <div class="stat-label">Urmărește</div>
        </div>
        <div class="profile-stat-large">
          <div class="stat-value">{created_date}</div>
          <div class="stat-label">Membru din</div>
        </div>
      </div>

      <div style="margin: 40px 0; padding: 32px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg);">
        <h2 style="font-size: 24px; font-weight: 700; margin: 0 0 24px; color: var(--text);">Link-uri</h2>
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <a href="{url}" target="_blank" rel="{rel_attr}" class="btn btn-primary" style="display: inline-flex; align-items: center; gap: 8px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
            Vezi pe Mastodon
          </a>
          <a href="{rss_url}" target="_blank" rel="{rel_attr}" class="rss-link" style="font-size: 16px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 11a9 9 0 0 1 9 9"></path>
              <path d="M4 4a16 16 0 0 1 16 16"></path>
              <circle cx="5" cy="19" r="1"></circle>
            </svg>
            Abonează-te la RSS Feed
          </a>
        </div>
      </div>
    </div>
  </main>

  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-content">
        <div class="footer-section">
          <h3>Link-uri Rapide</h3>
          <nav>
            <a href="/">Acasă</a>
            <a href="/profiles/">Explorator</a>
            <a href="/stats/">Statistici</a>
            <a href="/feed.xml">RSS Feed</a>
          </nav>
        </div>
        <div class="footer-section">
          <h3>Despre</h3>
          <p>Romania RSS Feed este un explorator modern pentru profilurile Mastodon de pe social.5th.ro.</p>
        </div>
        <div class="footer-section">
          <h3>Server Mastodon</h3>
          <a href="https://social.5th.ro/" target="_blank" rel="noopener">social.5th.ro</a>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; 2025 Romania RSS Feed. Hub pentru profiluri Mastodon din România.</p>
      </div>
    </div>
  </footer>
</body>
</html>
"""

def format_number(num):
    """Format number with commas"""
    return f"{num:,}"

def format_date(date_str):
    """Format date string"""
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d %b %Y")
    except:
        return date_str[:10] if date_str else "N/A"

def strip_html(text):
    """Remove HTML tags"""
    if not text:
        return ""
    import re
    return re.sub(r'<[^>]+>', '', text)

def get_rel_attribute(username: str, instance: str) -> str:
    """Determine rel attribute based on instance
    - mstdn.ro: always nofollow
    - social.5th.ro: 20% nofollow, 80% dofollow (based on username hash)"""
    if instance == "mstdn.ro":
        return "noopener nofollow"
    
    # For social.5th.ro: 20% nofollow, 80% dofollow
    # Use hash of username for consistent assignment
    import hashlib
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    # 20% chance of nofollow (hash % 100 < 20)
    if hash_value % 100 < 20:
        return "noopener nofollow"
    else:
        return "noopener"

def main():
    print("📄 Generare pagini profil...")
    
    profiles_file = Path(__file__).parent.parent / "data" / "profiles.json"
    if not profiles_file.exists():
        print("❌ Fișierul profiles.json nu există!")
        return
    
    with open(profiles_file, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    
    profiles_dir = Path(__file__).parent.parent / "profiles"
    profiles_dir.mkdir(exist_ok=True)
    
    for profile in profiles:
        username = profile.get("username", "")
        if not username:
            continue
        
        profile_dir = profiles_dir / username
        profile_dir.mkdir(exist_ok=True)
        
        display_name = html.escape(profile.get("display_name", username))
        description = profile.get("note", "")
        description_meta = html.escape(strip_html(description)[:200])
        instance = profile.get("instance", "social.5th.ro")
        
        # Get acct (username@instance) or build it
        acct = profile.get("acct", "")
        if not acct:
            acct = f"{username}@{instance}"
        
        avatar = profile.get("avatar", "")
        if avatar:
            avatar_html = f'<img src="{html.escape(avatar)}" alt="{display_name}" style="width:100%;height:100%;object-fit:cover;border-radius:var(--radius-lg);" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';">\n          <span style="display:none;">{display_name[0].upper() if display_name else "?"}</span>'
        else:
            avatar_html = f'<span>{display_name[0].upper() if display_name else "?"}</span>'
        
        # Determine rel attribute
        rel_attr = get_rel_attribute(username, instance)
        
        html_content = PROFILE_TEMPLATE.format(
            display_name=display_name,
            username=html.escape(username),
            acct=html.escape(acct),
            description_meta=description_meta,
            description=description,  # Keep HTML in description
            avatar_html=avatar_html,
            statuses_count=format_number(profile.get("statuses_count", 0)),
            followers_count=format_number(profile.get("followers_count", 0)),
            following_count=format_number(profile.get("following_count", 0)),
            created_date=format_date(profile.get("created_at", "")),
            url=html.escape(profile.get("url", f"https://social.5th.ro/@{username}")),
            rss_url=html.escape(profile.get("rss_url", f"https://social.5th.ro/@{username}.rss")),
            rel_attr=rel_attr
        )
        
        index_file = profile_dir / "index.html"
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"  ✅ {username}")
    
    print(f"\n🎉 {len(profiles)} pagini generate!")

if __name__ == "__main__":
    main()

