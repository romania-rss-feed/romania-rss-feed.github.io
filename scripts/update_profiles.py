#!/usr/bin/env python3
"""
Script pentru actualizarea profilurilor Mastodon de pe social.5th.ro
Detectează automat profilurile noi și actualizează datele existente.
"""

import json
import requests
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

API_BASE = "https://social.5th.ro/api/v1"
INSTANCE_API = f"{API_BASE}/instance"
ACCOUNTS_ENDPOINT = f"{API_BASE}/accounts"

# Lista de username-uri cunoscute
KNOWN_USERNAMES = [
    "pentruoameni", "recent_news", "topcomunicate_ro", "pr360", "ai_advertising",
    "cetatean_model", "Iasi", "femeie_antreprenor", "afaceri_top", "banat",
    "ziar360", "cutremur", "dobrogea", "constanta", "brasov", "femeiAZ", "top",
    "cluj", "noutati24", "constructii360", "AfaceriProfi", "oltenia", "clasici",
    "afaceri24", "bucovina", "efaq", "prbusiness", "stiri_sociale", "SolutiiConstructii",
    "topantreprenor", "Partizani", "clinic_sanatos", "inovare_afaceri", "doctor360",
    "DoctoriteBlog", "stiri_democratice", "eratehnologica", "ArtaConstructiilor",
    "ienergie", "iFemeie", "9z", "UniversulTech", "BIZWoman"
]

def fetch_account(username: str) -> Optional[Dict]:
    """Fetch account data from Mastodon API"""
    try:
        url = f"{ACCOUNTS_ENDPOINT}/lookup"
        params = {"acct": username}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"  ⚠️  Profil {username} nu a fost găsit")
            return None
        else:
            print(f"  ❌ Eroare pentru {username}: {response.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ Eroare la fetch pentru {username}: {e}")
        return None

def fetch_instance_stats() -> Dict:
    """Fetch instance statistics"""
    try:
        response = requests.get(INSTANCE_API, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        print(f"⚠️  Eroare la fetch statistici server: {e}")
        return {}

def discover_new_accounts(known_usernames: List[str]) -> List[Dict]:
    """Discover new accounts by searching directory - only local accounts from social.5th.ro
    Returns list of account data dictionaries, not just usernames"""
    new_accounts = []
    try:
        # Try to get directory (may not be available on all instances)
        url = f"{API_BASE}/directory"
        params = {"limit": 200, "order": "active", "local": "true"}  # Only local accounts
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            accounts = response.json()
            print(f"  📋 Directory API returned {len(accounts)} accounts")
            
            for account in accounts:
                username = account.get("username", "")
                acct = account.get("acct", "")
                url_field = account.get("url", "")
                
                # Strict filter: only local accounts
                # Must have URL with @social.5th.ro AND (acct without @ OR acct == username)
                is_local = False
                
                # First check: URL must contain @social.5th.ro
                if not url_field or "@social.5th.ro" not in url_field:
                    is_local = False
                elif not acct or acct == "":
                    # No acct field but URL is local - assume local
                    is_local = True
                elif "@" not in acct:
                    # Local account without domain (just username)
                    is_local = True
                elif acct == username:
                    # acct equals username (local)
                    is_local = True
                elif acct.endswith("@social.5th.ro"):
                    # Explicit local domain
                    is_local = True
                else:
                    # Has @ but not @social.5th.ro - federated, skip
                    is_local = False
                
                if is_local and username and username not in known_usernames:
                    # Use account data from directory directly
                    new_accounts.append(account)
                    print(f"  ✨ Profil nou descoperit (local): {username}")
            
            print(f"  ✅ Total profiluri noi locale: {len(new_accounts)}")
        else:
            print(f"⚠️  Directory API returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️  Nu s-au putut descoperi profiluri noi: {e}")
    
    return new_accounts

def normalize_profile(account_data: Dict) -> Dict:
    """Normalize profile data to our format"""
    return {
        "id": str(account_data.get("id", "")),
        "username": account_data.get("username", ""),
        "display_name": account_data.get("display_name", ""),
        "note": account_data.get("note", ""),
        "avatar": account_data.get("avatar", ""),
        "header": account_data.get("header", ""),
        "statuses_count": account_data.get("statuses_count", 0),
        "followers_count": account_data.get("followers_count", 0),
        "following_count": account_data.get("following_count", 0),
        "created_at": account_data.get("created_at", ""),
        "last_status_at": account_data.get("last_status_at"),
        "url": account_data.get("url", ""),
        "rss_url": f"https://social.5th.ro/@{account_data.get('username', '')}.rss"
    }

def main():
    print("🚀 Începe actualizarea profilurilor Mastodon...")
    
    # Load existing profiles
    profiles_file = Path(__file__).parent.parent / "data" / "profiles.json"
    profiles_file.parent.mkdir(parents=True, exist_ok=True)
    
    existing_profiles = []
    if profiles_file.exists():
        try:
            with open(profiles_file, "r", encoding="utf-8") as f:
                existing_profiles = json.load(f)
            print(f"📂 S-au încărcat {len(existing_profiles)} profiluri existente")
        except Exception as e:
            print(f"⚠️  Eroare la citirea profilurilor existente: {e}")
    
    # Create username map for quick lookup
    existing_usernames = {p.get("username", "") for p in existing_profiles}
    
    # Discover new accounts (returns account data directly from directory)
    print("\n🔍 Căutare profiluri noi...")
    new_accounts_data = discover_new_accounts(list(existing_usernames))
    
    # Process new accounts from directory (they already have data)
    new_profiles = []
    for account_data in new_accounts_data:
        profile = normalize_profile(account_data)
        new_profiles.append(profile)
    
    # Start with existing profiles
    profiles = existing_profiles.copy()
    
    # Update existing profiles that are in KNOWN_USERNAMES
    print(f"\n📥 Se actualizează profilurile existente...")
    known_usernames_to_update = [u for u in KNOWN_USERNAMES if u in existing_usernames]
    
    for i, username in enumerate(known_usernames_to_update, 1):
        print(f"[{i}/{len(known_usernames_to_update)}] {username}...", end=" ")
        account_data = fetch_account(username)
        if account_data:
            profile = normalize_profile(account_data)
            # Update existing profile
            existing_idx = next((i for i, p in enumerate(profiles) if p.get("username") == username), None)
            if existing_idx is not None:
                profiles[existing_idx] = profile
            print("✅")
        else:
            print("📋 (păstrat profil existent)")
    
    # Add new profiles from directory (they already have complete data)
    if new_profiles:
        print(f"\n➕ Se adaugă {len(new_profiles)} profiluri noi din directory...")
        for new_profile in new_profiles:
            username = new_profile.get("username")
            if username and not any(p.get("username") == username for p in profiles):
                profiles.append(new_profile)
                print(f"  ✅ {username}")
    
    # Sort by username
    profiles.sort(key=lambda x: x.get("username", "").lower())
    
    # Save profiles
    print(f"\n💾 Se salvează {len(profiles)} profiluri...")
    with open(profiles_file, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    print("✅ Profilurile au fost salvate!")
    
    # Fetch and save server stats
    print("\n📊 Se descarcă statisticile serverului...")
    server_stats = fetch_instance_stats()
    if server_stats:
        server_stats_file = Path(__file__).parent.parent / "data" / "server-stats.json"
        with open(server_stats_file, "w", encoding="utf-8") as f:
            json.dump(server_stats, f, indent=2, ensure_ascii=False)
        print(f"✅ Statisticile serverului au fost salvate!")
        print(f"   - Versiune: {server_stats.get('version', 'N/A')}")
        print(f"   - Utilizatori: {server_stats.get('stats', {}).get('user_count', 0)}")
        print(f"   - Statusuri: {server_stats.get('stats', {}).get('status_count', 0)}")
        print(f"   - Domenii: {server_stats.get('stats', {}).get('domain_count', 0)}")
    else:
        print("⚠️  Nu s-au putut obține statisticile serverului")
    
    print(f"\n🎉 Actualizare completă! {len(profiles)} profiluri disponibile.")
    if new_accounts_data:
        print(f"✨ {len(new_accounts_data)} profiluri noi descoperite!")

if __name__ == "__main__":
    main()

