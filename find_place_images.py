"""
Find likely Wikimedia Commons images for places in the Django database.

Run from the project folder in PowerShell:
  python manage.py shell -c "exec(open('find_place_images.py', encoding='utf-8').read())"

Safety:
- Searches Commons using each place name + city.
- Saves up to 5 candidates per place in place_image_candidates.csv for review.
- Automatically updates image_url ONLY when the result title strongly matches the place name.
- Does not overwrite an existing URL unless a strong exact match is found.
- Does not guarantee photos are crowd-free; inspect candidates before using them.
"""
import csv
import re
import time
import requests
from places.models import Place

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "SmartPlaceProject/1.0 (place image lookup)"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# For these known suspicious links, clear the old URL only if no strong replacement is found.
SUSPICIOUS_NAMES = {
    "amphitheatre", "kala qila", "landmark heights apartment park",
    "mount blanc view gallery", "shangri-la", "flamingo point",
    "mangaldas market",
}

def norm(value):
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())

def tokens(value):
    return set(norm(value).split())

def score_title(place_name, title):
    name = norm(place_name)
    title_norm = norm(re.sub(r"^file:", "", title, flags=re.I))
    name_tokens = tokens(name)
    title_tokens = tokens(title_norm)
    if not name_tokens:
        return 0.0
    overlap = len(name_tokens & title_tokens) / len(name_tokens)
    phrase = 1.0 if name and name in title_norm else 0.0
    # Prefer title containing the complete place name.
    return max(phrase, overlap * 0.85)

def search_commons(place):
    query = f'"{place.name}" {place.city} India'
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": 5,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": 900,
    }
    response = SESSION.get(API, params=params, timeout=25)
    response.raise_for_status()
    data = response.json()
    pages = list(data.get("query", {}).get("pages", {}).values())
    results = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url", "")
        if not url:
            continue
        title = page.get("title", "")
        results.append({
            "title": title,
            "url": url,
            "score": score_title(place.name, title),
            "page_url": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
        })
    return sorted(results, key=lambda x: x["score"], reverse=True)

places = list(Place.objects.all().order_by("id"))
report_rows = []
updated = 0
errors = 0

for i, place in enumerate(places, start=1):
    print(f"[{i}/{len(places)}] Searching: {place.name}")
    try:
        candidates = search_commons(place)
        top = candidates[0] if candidates else None

        # Conservative threshold: require strong title-name overlap.
        strong = top and top["score"] >= 0.85

        # Only update when a strong candidate exists.
        if strong and (not place.image_url or norm(place.name) in norm(top["title"])):
            place.image_url = top["url"]
            place.save(update_fields=["image_url"])
            updated += 1
            status = "AUTO-UPDATED — verify photo"
        elif norm(place.name) in SUSPICIOUS_NAMES:
            # Remove a known suspicious image rather than keep showing an unrelated picture.
            place.image_url = ""
            place.save(update_fields=["image_url"])
            status = "CLEARED SUSPICIOUS URL — review candidates"
        elif not place.image_url:
            status = "REVIEW — no strong match"
        else:
            status = "KEPT EXISTING — candidate needs review"

        for rank, item in enumerate(candidates, start=1):
            report_rows.append([
                place.id, place.name, place.city, place.category,
                rank, item["title"], f'{item["score"]:.2f}',
                item["url"], item["page_url"], status
            ])
        if not candidates:
            report_rows.append([
                place.id, place.name, place.city, place.category,
                "", "", "", "", "", status
            ])
    except Exception as exc:
        errors += 1
        report_rows.append([
            place.id, place.name, place.city, place.category,
            "", "", "", "", "", f"ERROR: {exc}"
        ])
        print("  Error:", exc)

    time.sleep(1.2)  # reduce the chance of API rate limiting

out_file = "place_image_candidates.csv"
with open(out_file, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Place ID", "Place Name", "City", "Category", "Candidate Rank",
        "Commons File Title", "Name Match Score", "Image URL",
        "Commons File Page", "Status"
    ])
    writer.writerows(report_rows)

print("\nFinished.")
print(f"Places checked: {len(places)}")
print(f"Image URLs updated automatically: {updated}")
print(f"Errors: {errors}")
print(f"Candidate report: {out_file}")
print("Please review the candidate report and verify photos before final use.")
