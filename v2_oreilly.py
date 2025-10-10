import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from html import unescape

# === CONFIG ===
OREILLY_TOKEN = "YOUR_OREILLY_API_TOKEN"
SEARCH_QUERY = "software development"
RESULT_LIMIT = 10
RSS_FILE = "v2_oreilly_feed.xml"  # path to your web-accessible file

# === FETCH DATA FROM O’REILLY ===
url = f"https://learning.oreilly.com/api/v2/search/?query={SEARCH_QUERY}&limit={RESULT_LIMIT}&type=video"
headers = {"Authorization": f"Bearer {OREILLY_TOKEN}"}
response = requests.get(url, headers=headers)
response.raise_for_status()

data = response.json()
results = data.get("results", [])

# === HELPER: Strip HTML tags ===
def clean_html(raw_html):
    text = unescape(re.sub(r"<.*?>", "", raw_html))
    return re.sub(r"\s+", " ", text).strip()

# === BUILD RSS FEED ===
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "O'Reilly - Recent Software Development Courses"
ET.SubElement(channel, "link").text = "https://learning.oreilly.com/"
ET.SubElement(channel, "description").text = "Latest software development courses from O'Reilly Online Learning."
ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

for item in results:
    course = ET.SubElement(channel, "item")

    title = item.get("title", "Untitled")

    # Some URLs are already full, some start with /api/v1/book/
    url_path = item.get("url", "")
    if url_path.startswith("http"):
        link = url_path
    else:
        link = f"https://learning.oreilly.com{url_path}"

    description_raw = item.get("description", "")
    description = clean_html(description_raw) or "No description available."

    pub_date = item.get("issued", datetime.utcnow().isoformat())

    # Find image field if available
    image_url = None
    for possible_field in ["cover", "thumbnail", "image"]:
        if possible_field in item and item[possible_field]:
            image_url = item[possible_field]
            break

    # Add RSS tags
    ET.SubElement(course, "title").text = title
    ET.SubElement(course, "link").text = link
    ET.SubElement(course, "description").text = description
    ET.SubElement(course, "pubDate").text = pub_date

    # Add enclosure if available
    if image_url:
        enclosure = ET.SubElement(course, "enclosure")
        enclosure.set("url", image_url)
        enclosure.set("type", "image/jpeg")

# === SAVE AS XML FILE ===
tree = ET.ElementTree(rss)
tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)

print(f"✅ RSS feed generated: {RSS_FILE}")
