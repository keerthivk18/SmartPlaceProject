from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path(
        'place/<int:place_id>/',
        views.place_detail,
        name='place_detail'
    ),

    path(
        'search-suggestions/',
        views.search_suggestions,
        name='search_suggestions'
    ),

    path(
        'place/<int:place_id>/services/<str:service_type>/',
        views.nearby_services,
        name='nearby_services'
    ),

    path(
        'route/<int:place_id>/<int:service_id>/',
        views.route_to_service,
        name='route'
    ),

    path(
        'api/route/',
        views.route_api,
        name='route_api'
    ),

    path(
        'api/geocode/',
        views.geocode,
        name='geocode'
    ),
    path(
    "route-planner/",
    views.route_planner,
    name="route_planner"
    ),
    path("save-trip/", views.save_trip, name="save_trip"),
    path("my-trips/", views.my_trips, name="my_trips"),
    path("chat-assistant/", views.chat_assistant, name="chat_assistant"),
]