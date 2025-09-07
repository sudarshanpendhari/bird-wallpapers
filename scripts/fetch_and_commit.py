import os
import json
import random
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image
from io import BytesIO

# Repo paths
IMAGES_DIR = Path("images")
INDEX_FILE = Path("index.json")

IMAGES_DIR.mkdir(exist_ok=True)

def load_index():
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_index(index):
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)

def fetch_from_pexels(api_key):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {"query": "birds", "per_page": 1, "page": random.randint(1, 50)}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    photos = data.get("photos", [])
    if photos:
        return photos[0]["src"]["original"]
    return None

def fetch_from_pixabay(api_key):
    url = "https://pixabay.com/api/"
    params = {"key": api_key, "q": "birds", "image_type": "photo", "per_page": 3}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    hits = data.get("hits", [])
    if hits:
        return random.choice(hits)["largeImageURL"]
    return None

def fetch_from_unsplash(api_key):
    url = "https://api.unsplash.com/photos/random"
    headers = {"Authorization": f"Client-ID {api_key}"}
    params = {"query": "birds"}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("urls", {}).get("full")

def download_and_save(image_url, index):
    if not image_url:
        return None

    try:
        r = requests.get(image_url, timeout=20)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))

        # Save with timestamp
        filename = f"bird_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = IMAGES_DIR / filename
        img.save(filepath, "JPEG")

        entry = {"file": str(filepath), "source_url": image_url, "timestamp": datetime.utcnow().isoformat()}
        index.append(entry)
        return entry
    except Exception as e:
        print(f"❌ Failed to download {image_url}: {e}")
        return None

def main():
    index = load_index()

    providers = []

    if os.getenv("PEXELS_KEY"):
        providers.append(("Pexels", lambda: fetch_from_pexels(os.getenv("PEXELS_KEY"))))
    if os.getenv("PIXABAY_KEY"):
        providers.append(("Pixabay", lambda: fetch_from_pixabay(os.getenv("PIXABAY_KEY"))))
    if os.getenv("UNSPLASH_KEY"):
        providers.append(("Unsplash", lambda: fetch_from_unsplash(os.getenv("UNSPLASH_KEY"))))

    if not providers:
        print("❌ No API keys found. Please set PEXELS_KEY, PIXABAY_KEY, or UNSPLASH_KEY.")
        return

    provider = random.choice(providers)  # pick one randomly
    name, fetcher = provider
    print(f"👉 Fetching image from {name}...")

    image_url = fetcher()
    if image_url:
        entry = download_and_save(image_url, index)
        if entry:
            save_index(index)
            print(f"✅ Saved image from {name}: {entry['file']}")
    else:
        print(f"⚠️ No image found from {name}")

if __name__ == "__main__":
    main()
