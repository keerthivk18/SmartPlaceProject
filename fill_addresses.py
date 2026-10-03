import time
import requests
from places.models import Place

headers = {
    "User-Agent": "SmartPlaceProject/1.0"
}

places = Place.objects.filter(
    address="Information not available"
).exclude(
    latitude__isnull=True
).exclude(
    longitude__isnull=True
).order_by("id")

updated = 0
failed = 0

for place in places:

    print(f"Searching: {place.name}")

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": place.latitude,
                "lon": place.longitude,
                "format": "jsonv2"
            },
            headers=headers,
            timeout=15
        )

        data = response.json()
        address = data.get("display_name")

        if address:
            place.address = address
            place.save(update_fields=["address"])
            updated += 1
            print(f"  ✓ {address}")
        else:
            failed += 1
            print("  ✗ Address not found")

    except Exception as error:
        failed += 1
        print(f"  ✗ Error: {error}")

    time.sleep(1)

print()
print("================================")
print("ADDRESS UPDATE COMPLETE")
print("Updated:", updated)
print("Failed:", failed)
print("================================")