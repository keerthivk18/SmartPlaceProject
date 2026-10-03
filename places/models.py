from django.db import models
from django.conf import settings


class Place(models.Model):
    name = models.CharField(max_length=150)
    alternate_name = models.CharField(max_length=200, blank=True)
    source_ref = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    category = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)

    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, default="")

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    opening_time = models.CharField(max_length=100, blank=True, default="")
    closing_time = models.CharField(max_length=100, blank=True, default="")

    contact = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    rating = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class Occupancy(models.Model):
    place = models.OneToOneField(
        Place,
        on_delete=models.CASCADE,
        related_name='occupancy'
    )

    crowd_status = models.CharField(max_length=50)
    waiting_time = models.CharField(max_length=50)
    best_time_to_visit = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Occupancies"

    def __str__(self):
        return f"{self.place.name} - {self.crowd_status}"


class Parking(models.Model):
    place = models.OneToOneField(
        Place,
        on_delete=models.CASCADE,
        related_name="parking"
    )

    total_slots = models.IntegerField(null=True, blank=True)
    available_slots = models.IntegerField(null=True, blank=True)

    parking_status = models.CharField(
        max_length=50,
        blank=True,
        default="Not updated"
    )

    class Meta:
        verbose_name_plural = "Parking"

    def __str__(self):
        return f"{self.place.name} - {self.parking_status}"
class Meta:
        verbose_name_plural = "Parking"

def __str__(self):
        return f"{self.place.name} - {self.parking_status}"


class Facility(models.Model):
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='facilities'
    )

    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.place.name} - {self.name}"


class Announcement(models.Model):
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='announcements'
    )

    message = models.TextField()

    def __str__(self):
        return f"{self.place.name} - {self.message[:30]}"


class TripPlan(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trip_plans'
    )

    trip_name = models.CharField(max_length=150)
    start_date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.trip_name


class TripPlace(models.Model):
    trip = models.ForeignKey(
        TripPlan,
        on_delete=models.CASCADE,
        related_name='trip_places'
    )

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='trip_entries'
    )

    visit_order = models.PositiveIntegerField(default=1)
    planned_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.trip.trip_name} - {self.place.name}"
class NearbyService(models.Model):
    SERVICE_TYPES = [
        ("hotel", "Hotel"),
        ("restaurant", "Restaurant"),
        ("parking", "Parking"),
        ("fuel", "Fuel Station"),
        ("hospital", "Hospital"),
        ("bank", "Bank"),
        ("cafe", "Cafe"),
        ("grocery", "Grocery"),
        ("pharmacy", "Pharmacy"),
        ("transport", "Transport"),
    ]

    name = models.CharField(max_length=150)
    service_type = models.CharField(
        max_length=30,
        choices=SERVICE_TYPES
    )

    latitude = models.FloatField()
    longitude = models.FloatField()

    address = models.TextField(blank=True)
    source_ref = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.service_type}"
    
    
class TripPlan(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trip_plans"
    )
    title = models.CharField(max_length=200)
    start_location = models.CharField(max_length=255, blank=True, default="")
    destination = models.CharField(max_length=255, blank=True, default="")
    stops = models.JSONField(default=list)
    route_details = models.JSONField(default=list)
    total_distance = models.FloatField(default=0)
    total_duration = models.IntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class TripPlace(models.Model):
    trip = models.ForeignKey(
        TripPlan,
        on_delete=models.CASCADE,
        related_name="trip_places"
    )
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="trip_entries"
    )
    visit_order = models.PositiveIntegerField(default=1)
    planned_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.trip.title} - {self.place.name}"


class NearbyService(models.Model):
    SERVICE_TYPES = [
        ("hotel", "Hotel"),
        ("restaurant", "Restaurant"),
        ("parking", "Parking"),
        ("fuel", "Fuel Station"),
        ("hospital", "Hospital"),
        ("bank", "Bank"),
        ("cafe", "Cafe"),
        ("grocery", "Grocery"),
        ("pharmacy", "Pharmacy"),
        ("transport", "Transport"),
    ]

    name = models.CharField(max_length=150)
    service_type = models.CharField(
        max_length=30,
        choices=SERVICE_TYPES
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField(blank=True)
    source_ref = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.service_type}"