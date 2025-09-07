import os, sys, io, json, datetime, random, requests
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(REPO_ROOT, 'images')
INDEX_FILE = os.path.join(REPO_ROOT, 'index.json')

# CONFIG
PER_DAY_PER_CATEGORY = 15
CATEGORIES = {
    "mobile": {"query":"bird wallpaper phone", "min_width":1080, "min_height":1920},
    "tablet": {"query":"bird wallpaper tablet", "min_width":1200, "min_height":1920},
    "other_mobile": {"query":"bird abstract phone", "min_width":1080, "min_height":1920},
    "other_tablet": {"query":"bird abstract tablet", "min_width":1200, "min_height":1920}
}

UNSPLASH_KEY = os.environ.get('UNSPLASH_KEY')
PEXELS_KEY = os.environ.get('PEXELS_KEY')
PIXABAY_KEY = os.environ.get('PIXABAY_KEY')

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE,'r') as f:
            return json.load(f)
    return []

def save_index(idx):
    with open(INDEX_FILE,'w') as f:
        json.dump(idx, f, indent=2)

def download_image(url):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.content

def save_resized_image(content, out_path, max_width=1600):
    img = Image.open(io.BytesIO(content)).convert('RGB')
    w,h = img.size
    if w > max_width:
        new_h = int(max_width*h/w)
        img = img.resize((max_width,new_h), Image.LANCZOS)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, format='JPEG', quality=88)
    return img.size

# Simple rotation choice
def choose_source():
    day = datetime.datetime.utcnow().day % 3
    return ['unsplash','pexels','pixabay'][day]

def fetch_from_unsplash(query):
    url = f"https://api.unsplash.com/photos/random?count=3&query={requests.utils.quote(query)}&orientation=portrait&client_id={UNSPLASH_KEY}"
    r = requests.get(url, timeout=15).json()
    results = []
    for item in r:
        results.append(item['urls']['full'])
    return results

def fetch_from_pexels(query):
    url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=3&orientation=portrait"
    r = requests.get(url, headers={"Authorization":PEXELS_KEY}, timeout=15).json()
    return [p['src']['original'] for p in r.get('photos',[])]

def fetch_from_pixabay(query):
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={requests.utils.quote(query)}&per_page=3&image_type=photo&orientation=vertical"
    r = requests.get(url, timeout=15).json()
    return [h['largeImageURL'] for h in r.get('hits',[])]

def fetch_urls_for_query(query):
    source = choose_source()
    try:
        if source == 'unsplash' and UNSPLASH_KEY:
            return fetch_from_unsplash(query)
        if source == 'pexels' and PEXELS_KEY:
            return fetch_from_pexels(query)
        if source == 'pixabay' and PIXABAY_KEY:
            return fetch_from_pixabay(query)
    except Exception as e:
        print("fetch error", e)
    # fallback: try all available
    for fn in (fetch_from_unsplash, fetch_from_pexels, fetch_from_pixabay):
        try:
            return fn(query)
        except:
            continue
    return []

def main():
    index = load_index()
    existing_files = {item['filename'] for item in index}
    today = datetime.datetime.utcnow().strftime('%Y%m%d')

    for cat, cfg in CATEGORIES.items():
        urls = fetch_urls_for_query(cfg['query'])
        saved = 0
        for u in urls:
            if saved >= PER_DAY_PER_CATEGORY:
                break
            try:
                content = download_image(u)
                fname = f"{cat}/{cat}-{today}-{random.randint(1000,9999)}.jpg"
                out_path = os.path.join(REPO_ROOT, 'images', fname)
                w,h = save_resized_image(content, out_path, max_width=2000)
                rec = {
                    "id": fname.replace('/','-'),
                    "filename": f"images/{fname}",
                    "category": cat,
                    "width": w,
                    "height": h,
                    "tags": [ "bird" ],
                    "date_added": today
                }
                if rec['filename'] not in existing_files:
                    index.append(rec)
                    existing_files.add(rec['filename'])
                    saved += 1
                    print("Saved", rec['filename'])
            except Exception as e:
                print("error saving:", e)

    save_index(index)
    print("Done. Total images:", len(index))

if __name__ == '__main__':
    main()
