#!/usr/bin/env python3
"""
Generator sitemap.xml pentru SEO
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

def generate_sitemap(profiles: list) -> str:
    """Generate sitemap.xml"""
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Homepage
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = "https://romania-rss-feed.github.io/"
    ET.SubElement(url, "changefreq").text = "daily"
    ET.SubElement(url, "priority").text = "1.0"
    
    # Profiles explorer
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = "https://romania-rss-feed.github.io/profiles/"
    ET.SubElement(url, "changefreq").text = "daily"
    ET.SubElement(url, "priority").text = "0.9"
    
    # Stats page
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = "https://romania-rss-feed.github.io/stats/"
    ET.SubElement(url, "changefreq").text = "daily"
    ET.SubElement(url, "priority").text = "0.8"
    
    # RSS feed
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = "https://romania-rss-feed.github.io/feed.xml"
    ET.SubElement(url, "changefreq").text = "hourly"
    ET.SubElement(url, "priority").text = "0.7"
    
    # Individual profile pages
    for profile in profiles:
        username = profile.get("username", "")
        if username:
            url = ET.SubElement(urlset, "url")
            ET.SubElement(url, "loc").text = f"https://romania-rss-feed.github.io/profiles/{username}/"
            ET.SubElement(url, "changefreq").text = "daily"
            ET.SubElement(url, "priority").text = "0.6"
            if profile.get("last_status_at"):
                try:
                    lastmod = datetime.fromisoformat(profile["last_status_at"].replace('Z', '+00:00'))
                    ET.SubElement(url, "lastmod").text = lastmod.strftime("%Y-%m-%d")
                except:
                    pass
    
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    return ET.tostring(urlset, encoding="unicode", xml_declaration=True)

def main():
    print("🗺️  Generare sitemap...")
    
    profiles_file = Path(__file__).parent.parent / "data" / "profiles.json"
    if not profiles_file.exists():
        print("❌ Fișierul profiles.json nu există!")
        return
    
    with open(profiles_file, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    
    sitemap_content = generate_sitemap(profiles)
    
    sitemap_file = Path(__file__).parent.parent / "sitemap.xml"
    with open(sitemap_file, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    
    print(f"✅ Sitemap generat cu {len(profiles) + 4} URL-uri!")

if __name__ == "__main__":
    main()

