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

def discover_new_accounts(known_usernames: List[str]) -> List[str]:
    """Discover new accounts by searching directory"""
    new_accounts = []
    try:
        # Try to get directory (may not be available on all instances)
        url = f"{API_BASE}/directory"
        params = {"limit": 100, "order": "active"}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            accounts = response.json()
            for account in accounts:
                username = account.get("username", "")
                if username and username not in known_usernames:
                    new_accounts.append(username)
                    print(f"  ✨ Profil nou descoperit: {username}")
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
    
    # Discover new accounts
    print("\n🔍 Căutare profiluri noi...")
    new_usernames = discover_new_accounts(list(existing_usernames) + KNOWN_USERNAMES)
    all_usernames = list(set(KNOWN_USERNAMES + new_usernames))
    
    # Fetch all profiles
    print(f"\n📥 Se descarcă date pentru {len(all_usernames)} profiluri...")
    profiles = []
    
    for i, username in enumerate(all_usernames, 1):
        print(f"[{i}/{len(all_usernames)}] {username}...", end=" ")
        account_data = fetch_account(username)
        if account_data:
            profile = normalize_profile(account_data)
            profiles.append(profile)
            print("✅")
        else:
            # Keep existing profile if available
            existing = next((p for p in existing_profiles if p.get("username") == username), None)
            if existing:
                profiles.append(existing)
                print("📋 (folosit profil existent)")
            else:
                print("❌")
    
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
    server_stats_file = Path(__file__).parent.parent / "data" / "server-stats.json"
    with open(server_stats_file, "w", encoding="utf-8") as f:
        json.dump(server_stats, f, indent=2, ensure_ascii=False)
    print("✅ Statisticile serverului au fost salvate!")
    
    print(f"\n🎉 Actualizare completă! {len(profiles)} profiluri disponibile.")
    if new_usernames:
        print(f"✨ {len(new_usernames)} profiluri noi descoperite!")

if __name__ == "__main__":
    main()

