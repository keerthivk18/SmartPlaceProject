from html import parser
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from places.models import NearbyService


class Command(BaseCommand):
    help = "Import nearby services from an OpenStreetMap JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
        "--file",
        default="data/mumbai_services.json",
        help="Path to the nearby services JSON file"
    )

    def handle(self, *args, **options):

        file_path = Path(options["file"])

        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(
                    f"File not found: {file_path}"
                )
            )
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

        except json.JSONDecodeError as error:
            self.stdout.write(
                self.style.ERROR(
                    f"Invalid JSON file: {error}"
                )
            )
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for element in data.get("elements", []):

            tags = element.get("tags", {})

            name = tags.get("name") or tags.get("name:en")

            if not name:
                skipped_count += 1
                continue

            latitude = element.get("lat")
            longitude = element.get("lon")

            # Ways and relations usually use center coordinates.
            if latitude is None or longitude is None:

                center = element.get("center", {})

                latitude = center.get("lat")
                longitude = center.get("lon")

            if latitude is None or longitude is None:
                skipped_count += 1
                continue

            # Identify the service type.
            if tags.get("tourism") == "hotel":

                service_type = "hotel"

            elif tags.get("amenity") == "restaurant":

                service_type = "restaurant"

            elif tags.get("amenity") == "parking":

                service_type = "parking"

            else:
                skipped_count += 1
                continue

            source_ref = f"{element.get('type')}/{element.get('id')}"

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

            existing_service = NearbyService.objects.filter(
                source_ref=source_ref
            ).first()

            if existing_service:

                existing_service.name = name
                existing_service.service_type = service_type
                existing_service.latitude = latitude
                existing_service.longitude = longitude
                existing_service.address = address

                existing_service.save()

                updated_count += 1

            else:

                NearbyService.objects.create(
                    name=name,
                    service_type=service_type,
                    latitude=latitude,
                    longitude=longitude,
                    address=address,
                    source_ref=source_ref,
                )

                created_count += 1

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed: "
                f"{created_count} created, "
                f"{updated_count} updated, "
                f"{skipped_count} skipped."
            )
        )