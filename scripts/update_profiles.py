#!/usr/bin/env python3
"""
Script pentru actualizarea profilurilor Mastodon de pe social.5th.ro
Detectează automat profilurile noi și actualizează datele existente.
"""

import json
import requests
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Primary instance (priority)
PRIMARY_INSTANCE = "social.5th.ro"
SECONDARY_INSTANCE = "mstdn.ro"

API_BASE_PRIMARY = f"https://{PRIMARY_INSTANCE}/api/v1"
API_BASE_SECONDARY = f"https://{SECONDARY_INSTANCE}/api/v1"

INSTANCE_API = f"{API_BASE_PRIMARY}/instance"
ACCOUNTS_ENDPOINT = f"{API_BASE_PRIMARY}/accounts"

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

def fetch_account(username: str, instance: str = PRIMARY_INSTANCE) -> Optional[Dict]:
    """Fetch account data from Mastodon API"""
    try:
        api_base = API_BASE_PRIMARY if instance == PRIMARY_INSTANCE else API_BASE_SECONDARY
        url = f"{api_base}/accounts/lookup"
        params = {"acct": username}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            account_data = response.json()
            account_data["_instance"] = instance  # Mark instance
            return account_data
        elif response.status_code == 404:
            return None  # Don't print here, caller will handle
        else:
            print(f"  ❌ Eroare pentru {username} pe {instance}: {response.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ Eroare la fetch pentru {username} pe {instance}: {e}")
        return None

def fetch_instance_stats() -> Dict:
    """Fetch instance statistics from both instances"""
    stats = {
        "instances": {},
        "total_users": 0,
        "total_statuses": 0,
        "total_domains": 0
    }
    
    # Fetch from primary instance (social.5th.ro)
    try:
        response = requests.get(INSTANCE_API, timeout=10)
        if response.status_code == 200:
            primary_stats = response.json()
            stats["instances"][PRIMARY_INSTANCE] = primary_stats
            stats["total_users"] += primary_stats.get("stats", {}).get("user_count", 0)
            stats["total_statuses"] += primary_stats.get("stats", {}).get("status_count", 0)
            stats["total_domains"] += primary_stats.get("stats", {}).get("domain_count", 0)
            stats["version"] = primary_stats.get("version", "N/A")
    except Exception as e:
        print(f"⚠️  Eroare la fetch statistici {PRIMARY_INSTANCE}: {e}")
    
    # Fetch from secondary instance (mstdn.ro)
    try:
        secondary_api = f"{API_BASE_SECONDARY}/instance"
        response = requests.get(secondary_api, timeout=10)
        if response.status_code == 200:
            secondary_stats = response.json()
            stats["instances"][SECONDARY_INSTANCE] = secondary_stats
            stats["total_users"] += secondary_stats.get("stats", {}).get("user_count", 0)
            stats["total_statuses"] += secondary_stats.get("stats", {}).get("status_count", 0)
            stats["total_domains"] += secondary_stats.get("stats", {}).get("domain_count", 0)
    except Exception as e:
        print(f"⚠️  Eroare la fetch statistici {SECONDARY_INSTANCE}: {e}")
    
    return stats

def discover_new_accounts(known_usernames: List[str]) -> List[Dict]:
    """Discover new accounts by searching directory - only local accounts from social.5th.ro and mstdn.ro
    Returns list of account data dictionaries with instance info. Priority: social.5th.ro first"""
    new_accounts = []
    found_usernames = set()  # Track usernames to avoid duplicates (priority to primary)
    
    # Try primary instance first (social.5th.ro)
    instances = [
        (PRIMARY_INSTANCE, API_BASE_PRIMARY),
        (SECONDARY_INSTANCE, API_BASE_SECONDARY)
    ]
    
    for instance_name, api_base in instances:
        try:
            # Try directory API (returns active/popular accounts in directory)
            # Note: Directory API only returns accounts that are "active" or manually added to directory
            # It does NOT return all local accounts - this is a Mastodon API limitation
            url = f"{api_base}/directory"
            params = {"limit": 200, "order": "active", "local": "true"}
            
            # Add delay to avoid rate limiting
            time.sleep(0.5)
            
            response = requests.get(url, params=params, timeout=10)
            
            directory_accounts = []
            if response.status_code == 200:
                directory_accounts = response.json()
                print(f"  📋 {instance_name} Directory API returned {len(directory_accounts)} accounts")
            elif response.status_code == 429:
                print(f"  ⚠️  {instance_name} Rate limited, waiting...")
                time.sleep(2)
                # Retry once
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    directory_accounts = response.json()
                    print(f"  📋 {instance_name} Directory API (retry) returned {len(directory_accounts)} accounts")
            else:
                print(f"  ⚠️  {instance_name} Directory API returned status {response.status_code}")
            
            # Note: We can't get ALL local accounts via public API
            # Directory API only shows accounts that are "active" or in directory
            # To get all accounts, we would need admin API access or authenticated requests
            all_accounts = directory_accounts
            print(f"  📊 {instance_name} Total accounts from directory: {len(all_accounts)}")
            print(f"  ℹ️  Note: Directory API only shows active/popular accounts, not all {instance_name} users")
            
            for account in all_accounts:
                    username = account.get("username", "")
                    acct = account.get("acct", "")
                    url_field = account.get("url", "")
                    
                    # Skip if already found on primary instance
                    if username in found_usernames:
                        continue
                    
                    # Check if account is local to this instance
                    is_local = False
                    instance_domain = f"@{instance_name}"
                    instance_url = f"https://{instance_name}/"
                    
                    # STRICT check: URL must contain instance URL
                    # This ensures we only get truly local accounts
                    if url_field and instance_url in url_field:
                        # Additional strict checks for local accounts
                        if not acct or acct == "":
                            # No acct field - check URL only (must contain instance URL)
                            is_local = instance_url in url_field
                        elif "@" not in acct:
                            # Local account without domain (just username) - must be local
                            is_local = True
                        elif acct == username:
                            # acct equals username (local)
                            is_local = True
                        elif acct.endswith(instance_domain):
                            # Explicit local domain
                            is_local = True
                        elif "@" in acct and not acct.endswith(instance_domain):
                            # Has @ but NOT matching instance - federated, skip
                            is_local = False
                        else:
                            # Default: not local if we can't confirm
                            is_local = False
                    else:
                        # URL doesn't contain instance URL - not local
                        is_local = False
                    
                    if is_local and username and username not in known_usernames:
                        # Add instance info to account data
                        account["_instance"] = instance_name
                        new_accounts.append(account)
                        found_usernames.add(username)
                        print(f"  ✨ Profil nou descoperit ({instance_name}): {username}")
            else:
                print(f"⚠️  {instance_name} Directory API returned status {response.status_code}")
        except Exception as e:
            print(f"⚠️  Eroare la {instance_name}: {e}")
    
    print(f"  ✅ Total profiluri noi locale: {len(new_accounts)}")
    return new_accounts

def normalize_profile(account_data: Dict) -> Dict:
    """Normalize profile data to our format"""
    username = account_data.get("username", "")
    instance = account_data.get("_instance", PRIMARY_INSTANCE)  # Default to primary
    
    # Determine instance from URL if not set
    url_field = account_data.get("url", "")
    if not instance:
        if f"@{SECONDARY_INSTANCE}" in url_field:
            instance = SECONDARY_INSTANCE
        else:
            instance = PRIMARY_INSTANCE
    
    # Build URLs based on instance
    if instance == SECONDARY_INSTANCE:
        profile_url = f"https://{SECONDARY_INSTANCE}/@{username}"
        rss_url = f"https://{SECONDARY_INSTANCE}/@{username}.rss"
    else:
        profile_url = f"https://{PRIMARY_INSTANCE}/@{username}"
        rss_url = f"https://{PRIMARY_INSTANCE}/@{username}.rss"
    
    return {
        "id": str(account_data.get("id", "")),
        "username": username,
        "display_name": account_data.get("display_name", ""),
        "note": account_data.get("note", ""),
        "avatar": account_data.get("avatar", ""),
        "header": account_data.get("header", ""),
        "statuses_count": account_data.get("statuses_count", 0),
        "followers_count": account_data.get("followers_count", 0),
        "following_count": account_data.get("following_count", 0),
        "created_at": account_data.get("created_at", ""),
        "last_status_at": account_data.get("last_status_at"),
        "url": url_field or profile_url,
        "rss_url": rss_url,
        "instance": instance  # Store instance for rel attribute logic
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
    
    # For discovery, we want to find profiles NOT in KNOWN_USERNAMES
    # This allows discovering new profiles on social.5th.ro beyond the initial list
    # and all local profiles on mstdn.ro
    print("\n🔍 Căutare profiluri noi...")
    new_accounts_data = discover_new_accounts(KNOWN_USERNAMES)
    
    # Process new accounts from directory (they already have complete data)
    new_profiles = []
    for account_data in new_accounts_data:
        profile = normalize_profile(account_data)
        new_profiles.append(profile)
    
    # Start with existing profiles
    profiles = existing_profiles.copy()
    existing_usernames = {p.get("username", "") for p in existing_profiles}
    
    print(f"\n📊 Statistici inițiale:")
    print(f"  - Profiluri existente: {len(existing_profiles)}")
    print(f"  - Profiluri noi descoperite: {len(new_profiles)}")
    
    # First, add new profiles from directory BEFORE updating existing ones
    # Use the data directly from directory - don't try to fetch again
    if new_profiles:
        print(f"\n➕ Se adaugă profiluri noi din directory...")
        added_count = 0
        skipped_count = 0
        for new_profile in new_profiles:
            username = new_profile.get("username", "")
            instance = new_profile.get("instance", PRIMARY_INSTANCE)
            if not username:
                skipped_count += 1
                continue
            if username not in existing_usernames:
                # Add profile directly from directory data (already complete)
                profiles.append(new_profile)
                existing_usernames.add(username)
                added_count += 1
                if added_count <= 10:  # Show first 10
                    print(f"  ✅ {username} ({instance})")
            else:
                skipped_count += 1
        print(f"  📊 Adăugate {added_count} profiluri noi din {len(new_profiles)} descoperite")
        if skipped_count > 0:
            print(f"  ⚠️  Omise {skipped_count} profiluri (deja existente)")
    else:
        print("\n➕ Nu s-au găsit profiluri noi de adăugat")
    
    # Update ONLY existing profiles (not the newly discovered ones)
    # New profiles already have complete data from directory
    print(f"\n📥 Se actualizează profilurile existente ({len(existing_profiles)} profiluri)...")
    
    updated_count = 0
    kept_count = 0
    
    for i, existing_profile in enumerate(existing_profiles, 1):
        username = existing_profile.get("username", "")
        if not username:
            continue
            
        print(f"[{i}/{len(existing_profiles)}] {username}...", end=" ", flush=True)
        instance_used = existing_profile.get("instance", PRIMARY_INSTANCE)
        
        # Try to fetch updated data
        account_data = fetch_account(username, instance_used)
        
        # If not found on current instance, try primary (priority)
        if not account_data and instance_used != PRIMARY_INSTANCE:
            account_data = fetch_account(username, PRIMARY_INSTANCE)
            if account_data:
                instance_used = PRIMARY_INSTANCE
        
        if account_data:
            profile = normalize_profile(account_data)
            # Update existing profile
            existing_idx = next((i for i, p in enumerate(profiles) if p.get("username") == username), None)
            if existing_idx is not None:
                profiles[existing_idx] = profile
            else:
                # Profile not in list yet, add it
                profiles.append(profile)
            updated_count += 1
            print(f"✅ ({instance_used})")
        else:
            # Keep existing profile even if we can't fetch new data
            # This ensures profiles don't disappear if they become inactive
            existing_idx = next((i for i, p in enumerate(profiles) if p.get("username") == username), None)
            if existing_idx is None:
                profiles.append(existing_profile)
            kept_count += 1
            print("📋 (păstrat profil existent)")
        
        # Small delay to avoid rate limiting
        time.sleep(0.2)
    
    print(f"\n📊 Rezumat actualizare: {updated_count} actualizate, {kept_count} păstrate")
    
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
        if PRIMARY_INSTANCE in server_stats.get("instances", {}):
            primary = server_stats["instances"][PRIMARY_INSTANCE]
            print(f"   {PRIMARY_INSTANCE}:")
            print(f"     - Versiune: {primary.get('version', 'N/A')}")
            print(f"     - Utilizatori: {primary.get('stats', {}).get('user_count', 0)}")
            print(f"     - Statusuri: {primary.get('stats', {}).get('status_count', 0)}")
            print(f"     - Domenii: {primary.get('stats', {}).get('domain_count', 0)}")
        if SECONDARY_INSTANCE in server_stats.get("instances", {}):
            secondary = server_stats["instances"][SECONDARY_INSTANCE]
            print(f"   {SECONDARY_INSTANCE}:")
            print(f"     - Versiune: {secondary.get('version', 'N/A')}")
            print(f"     - Utilizatori: {secondary.get('stats', {}).get('user_count', 0)}")
            print(f"     - Statusuri: {secondary.get('stats', {}).get('status_count', 0)}")
            print(f"     - Domenii: {secondary.get('stats', {}).get('domain_count', 0)}")
        print(f"   Total: {server_stats.get('total_users', 0)} utilizatori, {server_stats.get('total_statuses', 0)} statusuri")
    else:
        print("⚠️  Nu s-au putut obține statisticile serverului")
    
    print(f"\n🎉 Actualizare completă! {len(profiles)} profiluri disponibile.")
    if new_accounts_data:
        print(f"✨ {len(new_accounts_data)} profiluri noi descoperite!")

if __name__ == "__main__":
    main()

