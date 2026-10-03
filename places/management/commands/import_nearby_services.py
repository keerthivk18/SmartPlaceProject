import json
import ssl
import certifi

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.core.management.base import BaseCommand, CommandError

from places.models import Place, NearbyService


# Public Overpass servers.
# The command tries them one by one if a server fails.
OVERPASS_URLS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


CATEGORY_QUERIES = {
    "hotel": """
        nwr["tourism"="hotel"]
    """,

    "restaurant": """
        nwr["amenity"="restaurant"]
    """,

    "parking": """
        nwr["amenity"="parking"]
    """,

    "fuel": """
        nwr["amenity"="fuel"]
    """,

    "hospital": """
        nwr["amenity"="hospital"]
    """,

    "bank": """
        nwr["amenity"="bank"]
    """,

    "cafe": """
        nwr["amenity"="cafe"]
    """,

    

    "pharmacy": """
        nwr["amenity"="pharmacy"]
    """,

        "grocery": """
        nwr["shop"~"supermarket|convenience|grocery"]
    """,

    "transport": """
        nwr["amenity"~"bus_station|ferry_terminal"]
    """,

}


class Command(BaseCommand):
    help = "Import one nearby service category around a tourist place"

    def add_arguments(self, parser):

        parser.add_argument(
            "--place-id",
            type=int,
            required=True,
            help="ID of the tourist place"
        )

        parser.add_argument(
            "--category",
            type=str,
            required=True,
            choices=list(CATEGORY_QUERIES.keys()),
            help="Service category to import"
        )

        parser.add_argument(
            "--radius",
            type=int,
            default=2000,
            help="Search radius in metres"
        )

    def handle(self, *args, **options):

        place_id = options["place_id"]
        category = options["category"]
        radius = options["radius"]

        # ---------------------------------------------------------
        # Get place
        # ---------------------------------------------------------

        try:
            place = Place.objects.get(id=place_id)
        except Place.DoesNotExist:
            raise CommandError(
                f"Place with ID {place_id} does not exist."
            )

        if place.latitude is None or place.longitude is None:
            raise CommandError(
                f"{place.name} does not have latitude/longitude."
            )

        latitude = place.latitude
        longitude = place.longitude

        # ---------------------------------------------------------
        # Build a SMALL query for ONE category
        # ---------------------------------------------------------

        category_query = CATEGORY_QUERIES[category]

        query = f"""
        [out:json][timeout:60];

        (
            {category_query}
                (around:{radius},{latitude},{longitude});
        );

        out center tags;
        """

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                f"Searching {category} around {place.name}"
            )
        )
        self.stdout.write(
            f"Radius: {radius} metres"
        )

        # ---------------------------------------------------------
        # Create SSL context
        # ---------------------------------------------------------

        ssl_context = ssl.create_default_context(
            cafile=certifi.where()
        )

        data = None
        last_error = None

        # ---------------------------------------------------------
        # Try public Overpass servers one by one
        # ---------------------------------------------------------

        for overpass_url in OVERPASS_URLS:

            self.stdout.write(
                f"Trying: {overpass_url}"
            )

            try:

                encoded_data = urlencode({
                    "data": query
                }).encode("utf-8")

                request = Request(
                    overpass_url,
                    data=encoded_data,
                    headers={
                        "User-Agent": (
                            "SmartPlaceStudentProject/1.0 "
                            "(Django)"
                        ),
                        "Accept": "application/json",
                    }
                )

                with urlopen(
                    request,
                    timeout=90,
                    context=ssl_context
                ) as response:

                    data = json.loads(
                        response.read().decode("utf-8")
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        "Overpass server responded successfully."
                    )
                )

                break

            except (
                HTTPError,
                URLError,
                TimeoutError,
                OSError,
                json.JSONDecodeError
            ) as error:

                last_error = error

                self.stdout.write(
                    self.style.ERROR(
                        f"Server failed: {error}"
                    )
                )

        # ---------------------------------------------------------
        # All servers failed
        # ---------------------------------------------------------

        if data is None:
            raise CommandError(
                "All Overpass servers failed. "
                f"Last error: {last_error}"
            )

        # ---------------------------------------------------------
        # Import results
        # ---------------------------------------------------------

        created_count = 0
        updated_count = 0
        skipped_count = 0

        found_count = 0

        for element in data.get("elements", []):

            tags = element.get("tags", {})

            name = (
                tags.get("name")
                or tags.get("name:en")
            )

            if not name:
                skipped_count += 1
                continue

            # -----------------------------------------------------
            # Coordinates
            # -----------------------------------------------------

            latitude_value = element.get("lat")
            longitude_value = element.get("lon")

            if (
                latitude_value is None
                or longitude_value is None
            ):
                center = element.get("center", {})

                latitude_value = center.get("lat")
                longitude_value = center.get("lon")

            if (
                latitude_value is None
                or longitude_value is None
            ):
                skipped_count += 1
                continue

            # -----------------------------------------------------
            # OSM unique reference
            # -----------------------------------------------------

            source_ref = (
                f"{element.get('type')}/{element.get('id')}"
            )

            # -----------------------------------------------------
            # Address
            # -----------------------------------------------------

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

            # -----------------------------------------------------
            # Update or create
            # -----------------------------------------------------

            existing_service = (
                NearbyService.objects.filter(
                    source_ref=source_ref
                ).first()
            )

            if existing_service:

                existing_service.name = name
                existing_service.service_type = category
                existing_service.latitude = latitude_value
                existing_service.longitude = longitude_value
                existing_service.address = address

                existing_service.save()

                updated_count += 1

            else:

                NearbyService.objects.create(
                    name=name,
                    service_type=category,
                    latitude=latitude_value,
                    longitude=longitude_value,
                    address=address,
                    source_ref=source_ref,
                )

                created_count += 1

            found_count += 1

        # ---------------------------------------------------------
        # Result
        # ---------------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"{category.title()} import completed."
            )
        )

        self.stdout.write(
            f"Found: {found_count}"
        )

        self.stdout.write(
            f"Created: {created_count}"
        )

        self.stdout.write(
            f"Updated: {updated_count}"
        )

        self.stdout.write(
            f"Skipped: {skipped_count}"
        )