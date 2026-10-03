
import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from places.models import Place


def search_image(place):
    queries = [
        f'"{place.name}" {place.city}',
        place.name,
    ]

    for query in queries:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": 6,
            "gsrlimit": 5,
            "gsrsearch": query,
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": 800,
        }

        url = "https://commons.wikimedia.org/w/api.php?" + urlencode(params)

        try:
            request = Request(
                url,
                headers={"User-Agent": "SmartPlaceProject/1.0"}
            )

            with urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))

            pages = data.get("query", {}).get("pages", {})

            for page in pages.values():
                for info in page.get("imageinfo", []):
                    if info.get("mime", "").startswith("image/"):
                        image_url = info.get("thumburl") or info.get("url")
                        if image_url:
                            return image_url

        except Exception as error:
            print("Search error:", place.name, error)

        time.sleep(0.5)

    return ""


places = Place.objects.filter(image_url="")

total = places.count()
updated = 0
not_found = 0

print(f"Searching images for {total} places...")

for place in places.iterator():
    image_url = search_image(place)

    if image_url:
        place.image_url = image_url
        place.save(update_fields=["image_url"])
        updated += 1
        print(f"FOUND: {place.name}")
    else:
        not_found += 1
        print(f"NOT FOUND: {place.name}")

    time.sleep(0.5)

print("\nImage search completed!")
print("Updated:", updated)
print("Not found:", not_found)