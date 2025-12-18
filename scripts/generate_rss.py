#!/usr/bin/env python3
"""
Generator RSS feed pentru toate profilurile
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from html import escape

def generate_rss_feed(profiles: list) -> str:
    """Generate main RSS feed"""
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    
    channel = ET.SubElement(rss, "channel")
    
    ET.SubElement(channel, "title").text = "Romania RSS Feed - Profiluri Mastodon"
    ET.SubElement(channel, "link").text = "https://romania-rss-feed.github.io/"
    ET.SubElement(channel, "description").text = "Feed RSS pentru profilurile Mastodon de pe social.5th.ro"
    ET.SubElement(channel, "language").text = "ro"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    
    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", "https://romania-rss-feed.github.io/feed.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")
    
    # Add each profile as an item
    for profile in sorted(profiles, key=lambda x: x.get("username", "").lower()):
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = escape(f"{profile.get('display_name', profile.get('username', ''))} (@{profile.get('username', '')})")
        ET.SubElement(item, "link").text = f"https://romania-rss-feed.github.io/profiles/{profile.get('username', '')}/"
        ET.SubElement(item, "description").text = escape(profile.get("note", "")[:500])
        ET.SubElement(item, "guid", isPermaLink="false").text = f"profile-{profile.get('username', '')}"
        ET.SubElement(item, "pubDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    return ET.tostring(rss, encoding="unicode", xml_declaration=True)

def main():
    print("📡 Generare feed RSS...")
    
    profiles_file = Path(__file__).parent.parent / "data" / "profiles.json"
    if not profiles_file.exists():
        print("❌ Fișierul profiles.json nu există!")
        return
    
    with open(profiles_file, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    
    rss_content = generate_rss_feed(profiles)
    
    feed_file = Path(__file__).parent.parent / "feed.xml"
    with open(feed_file, "w", encoding="utf-8") as f:
        f.write(rss_content)
    
    print(f"✅ Feed RSS generat cu {len(profiles)} profiluri!")

if __name__ == "__main__":
    main()

