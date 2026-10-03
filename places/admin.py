from django.contrib import admin
from .models import (
    Place,
    Occupancy,
    Parking,
    Facility,
    Announcement,
    TripPlan,
    TripPlace,
    NearbyService
)


admin.site.register(Place)
admin.site.register(Occupancy)
admin.site.register(Parking)
admin.site.register(Facility)
admin.site.register(Announcement)
admin.site.register(TripPlan)
admin.site.register(TripPlace)
admin.site.register(NearbyService)