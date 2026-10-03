import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from places.models import Place


coordinates = {
    "Gateway of India": (18.92196, 72.83456),
    "Marine Drive": (18.94149, 72.82385),
    "Siddhivinayak Temple": (19.01688, 72.83040),
    "Chhatrapati Shivaji Maharaj Terminus": (18.94012, 72.83620),
}


for name, (latitude, longitude) in coordinates.items():

    place = Place.objects.filter(name__iexact=name).first()

    if place:
        place.latitude = latitude
        place.longitude = longitude
        place.save()

        print(f"Updated: {place.name}")

    else:
        print(f"Not found: {name}")