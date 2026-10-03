import json
from pathlib import Path

from django.core.management.base import BaseCommand

from places.models import Place


class Command(BaseCommand):
    help = "Import tourist places from OpenStreetMap JSON data"

    def handle(self, *args, **options):
        file_path = Path("data/export.json")

        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR("data/export.json was not found.")
            )
            return

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for element in data.get("elements", []):
            tags = element.get("tags", {})

            name = tags.get("name") or tags.get("name:en")
            alternate_name = tags.get("name:en", "")

            if not name:
                skipped_count += 1
                continue

            latitude = element.get("lat")
            longitude = element.get("lon")

            if latitude is None or longitude is None:
                center = element.get("center", {})
                latitude = center.get("lat")
                longitude = center.get("lon")

            if latitude is None or longitude is None:
                skipped_count += 1
                continue

            source_ref = f"{element.get('type')}/{element.get('id')}"

            tourism_type = tags.get("tourism", "Other")

            category_map = {
                "attraction": "Tourist Attraction",
                "museum": "Museum",
                "gallery": "Gallery",
                "viewpoint": "Viewpoint",
                "zoo": "Zoo",
                "theme_park": "Theme Park",
                "aquarium": "Aquarium",
                "artwork": "Artwork",
            }

            category = category_map.get(
                tourism_type,
                tourism_type.replace("_", " ").title()
            )

            city = tags.get("addr:city") or "Mumbai"
            district = tags.get("addr:district", "")

            address_parts = []

            for key in [
                "addr:housenumber",
                "addr:street",
                "addr:suburb",
                "addr:city",
            ]:
                value = tags.get(key)

                if value:
                    address_parts.append(value)

            address = ", ".join(address_parts)

            description = tags.get("description", "")
            contact = tags.get("phone", "")
            website = tags.get("website", "")

            place = Place.objects.filter(
                source_ref=source_ref
            ).first()

            if place is None:
                place = Place.objects.filter(
                    name__iexact=name,
                    city__iexact=city
                ).first()

            if place is None:
                Place.objects.create(
                    name=name,
                    alternate_name=alternate_name,
                    source_ref=source_ref,
                    category=category,
                    city=city,
                    district=district,
                    address=address,
                    description=description,
                    latitude=latitude,
                    longitude=longitude,
                    contact=contact,
                    website=website,
                )

                created_count += 1

            else:
                place.source_ref = source_ref
                place.name = name
                place.alternate_name = alternate_name
                place.category = category
                place.city = city
                place.district = district
                place.address = address
                place.description = description
                place.latitude = latitude
                place.longitude = longitude
                place.contact = contact
                place.website = website

                place.save()

                updated_count += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed: {created_count} created, "
                f"{updated_count} updated, "
                f"{skipped_count} skipped."
            )
        )