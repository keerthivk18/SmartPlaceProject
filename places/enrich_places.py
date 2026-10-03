
import os
import re
import time
import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from places.models import Place


# Get places that have OpenStreetMap source IDs
places = Place.objects.exclude(
    source_ref__isnull=True
).exclude(source_ref="")

# Group OSM IDs by type
groups = {"node": [], "way": [], "relation": []}

for place in places:
    try:
        kind, osm_id = place.source_ref.split("/")[-2:]
        if kind in groups:
            groups[kind].append(osm_id)
    except (ValueError, AttributeError):
        continue

# Fetch OSM data in small batches
tag_map = {}

endpoints = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

for kind, ids in groups.items():
    for start in range(0, len(ids), 20):
        batch = ids[start:start + 20]

        query = (
            "[out:json];("
            + f"{kind}(id:{','.join(batch)});"
            + ");out tags center;"
        )

        success = False

        for endpoint in endpoints:
            for attempt in range(3):
                try:
                    response = requests.post(
                        endpoint,
                        data={"data": query},
                        headers={
                            "User-Agent": "SmartPlaceProject/1.0",
                            "Accept": "application/json",
                        },
                        timeout=180,
                    )
                    response.raise_for_status()

                    elements = response.json().get("elements", [])

                    for item in elements:
                        key = f"{item['type']}/{item['id']}"
                        tag_map[key] = item.get("tags", {})

                    success = True
                    break

                except requests.RequestException as error:
                    print(
                        f"Request failed ({attempt + 1}/3): {error}"
                    )
                    time.sleep(5 * (attempt + 1))

            if success:
                break

        if not success:
            print(f"Skipping batch: {kind}, starting at {start}")
        else:
            print(
                f"Processed {kind}: "
                f"{min(start + 20, len(ids))}/{len(ids)}"
            )

        time.sleep(3)


# Update missing information only
updated = 0

for place in places:
    tags = tag_map.get(place.source_ref, {})
    changed = []

    # Address
    address = tags.get("addr:full", "")

    if not address:
        parts = [
            tags.get("addr:housenumber", ""),
            tags.get("addr:street", ""),
            tags.get("addr:suburb", ""),
            tags.get("addr:city", ""),
            tags.get("addr:state", ""),
            tags.get("addr:postcode", ""),
        ]
        address = ", ".join(part for part in parts if part)

    if not place.address and address:
        place.address = address
        changed.append("address")

    # Contact
    phone = (
        tags.get("contact:phone")
        or tags.get("phone")
        or tags.get("contact:mobile")
        or ""
    )

    if not place.contact and phone:
        place.contact = phone
        changed.append("contact")

    # Website
    website = tags.get("contact:website") or tags.get("website", "")

    if website and not place.website:
        if not website.startswith(("http://", "https://")):
            website = "https://" + website

        place.website = website
        changed.append("website")

    # Opening time
    # Opening and Closing Time
opening_hours = tags.get("opening_hours", "")
times = re.findall(r"\b([0-2]?\d:[0-5]\d)\b", opening_hours)

if len(times) >= 2:
    if not place.opening_time:
        place.opening_time = times[0]
        changed.append("opening_time")

    if not place.closing_time:
        place.closing_time = times[1]
        changed.append("closing_time")
    # Description
    description = tags.get("description", "")

    if not place.description and description:
        place.description = description
        changed.append("description")

    if changed:
        place.save(update_fields=changed)
        updated += 1

print(f"Finished. Updated {updated} places.")
print(f"OSM records retrieved: {len(tag_map)}")