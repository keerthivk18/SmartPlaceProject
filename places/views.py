from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
import os
from django.db.models import Q
from django.http import JsonResponse
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json
import ssl
import certifi
from urllib.parse import urlencode
from math import radians, sin, cos, sqrt, atan2
from .knowledge_base import find_answer

from .models import Place, NearbyService
from django.http import JsonResponse

@login_required
def home(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    places = Place.objects.all()

    if query:
        places = places.filter(
            Q(name__icontains=query) |
            Q(alternate_name__icontains=query) |
            Q(city__icontains=query) |
            Q(district__icontains=query) |
            Q(category__icontains=query)
        ).distinct()

    if category:
        places = places.filter(category__iexact=category)

    return render(request, 'home.html', {
        'places': places,
        'query': query,
        'selected_category': category
    })

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using the Haversine formula.
    Returns distance in kilometres.
    """

    earth_radius = 6371

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def place_detail(request, place_id):
    place = get_object_or_404(Place, id=place_id)

    weather = None

    if place.latitude is not None and place.longitude is not None:
        weather = get_weather(
            place.latitude,
            place.longitude
        )

    nearby_services = []

    if place.latitude is not None and place.longitude is not None:

        services = NearbyService.objects.all()

        for service in services:

            distance = calculate_distance(
                place.latitude,
                place.longitude,
                service.latitude,
                service.longitude
            )

            if distance <= 2:
                service.distance = round(distance, 2)
                nearby_services.append(service)

        nearby_services.sort(
            key=lambda service: service.distance
        )

    return render(request, 'place_detail.html', {
        'place': place,
        'weather': weather,
        'nearby_services': nearby_services
    })
def search_suggestions(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse([], safe=False)

    places = Place.objects.filter(
        Q(name__istartswith=query) |
        Q(alternate_name__istartswith=query)
    ).order_by('name')[:10]

    suggestions = []

    for place in places:
        suggestions.append({
            'id': place.id,
            'name': place.name,
            'alternate_name': place.alternate_name,
            'city': place.city,
        })

    return JsonResponse(suggestions, safe=False)
def get_weather(latitude, longitude):
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m',
        'timezone': 'auto'
    }

    url = 'https://api.open-meteo.com/v1/forecast?' + urlencode(params)

    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        weather_code = data.get('current', {}).get('weather_code')

        weather_conditions = {
            0: ('Clear Sky', '☀️'),
            1: ('Mainly Clear', '🌤️'),
            2: ('Partly Cloudy', '⛅'),
            3: ('Overcast', '☁️'),
            45: ('Foggy', '🌫️'),
            48: ('Foggy', '🌫️'),
            51: ('Light Drizzle', '🌦️'),
            53: ('Moderate Drizzle', '🌦️'),
            55: ('Heavy Drizzle', '🌧️'),
            61: ('Light Rain', '🌦️'),
            63: ('Moderate Rain', '🌧️'),
            65: ('Heavy Rain', '🌧️'),
            71: ('Light Snow', '🌨️'),
            73: ('Moderate Snow', '🌨️'),
            75: ('Heavy Snow', '❄️'),
            80: ('Light Rain Showers', '🌦️'),
            81: ('Moderate Rain Showers', '🌧️'),
            82: ('Heavy Rain Showers', '⛈️'),
            95: ('Thunderstorm', '⛈️'),
            96: ('Thunderstorm with Hail', '⛈️'),
            99: ('Heavy Thunderstorm with Hail', '⛈️'),
        }

        condition, icon = weather_conditions.get(
            weather_code,
            ('Weather information available', '🌤️')
        )

        data['condition'] = condition
        data['icon'] = icon

        return data

    except Exception:
        return None
def geocode(request):
    """
    Convert a user-entered place name into latitude and longitude.
    """

    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse(
            {"error": "Please enter a location."},
            status=400
        )

    search_queries = [query]

    # Add Maharashtra and India for short searches
    if "maharashtra" not in query.lower():
        search_queries.append(
            f"{query}, Maharashtra, India"
        )

    # Add Mumbai for common Mumbai-area searches
    if (
        "mumbai" not in query.lower()
        and "maharashtra" not in query.lower()
        and "india" not in query.lower()
    ):
        search_queries.append(
            f"{query}, Mumbai, Maharashtra, India"
        )

    # Common local names / abbreviations
    aliases = {
        "chembur camp":
            "Chembur, Mumbai, Maharashtra, India",

        "chembur colony":
            "Chembur, Mumbai, Maharashtra, India",

        "gateway":
            "Gateway of India, Mumbai, Maharashtra, India",

        "gateway of india":
            "Gateway of India, Mumbai, Maharashtra, India",

        "cst":
            "Chhatrapati Shivaji Maharaj Terminus, Mumbai, Maharashtra, India",

        "csmt":
            "Chhatrapati Shivaji Maharaj Terminus, Mumbai, Maharashtra, India",

        "bombay":
            "Mumbai, Maharashtra, India",

        "bombay airport":
            "Mumbai Airport, Maharashtra, India",

        "mumbai airport":
            "Mumbai Airport, Maharashtra, India",
    }

    lower_query = query.lower()

    if lower_query in aliases:
        search_queries.insert(
            0,
            aliases[lower_query]
        )

    # Remove duplicate searches
    search_queries = list(
        dict.fromkeys(search_queries)
    )

    # Try each search
    for search_query in search_queries:

        params = urlencode({
            "q": search_query,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "in",
        })

        url = (
            "https://nominatim.openstreetmap.org/search?"
            + params
        )

        request_obj = Request(
            url,
            headers={
                "User-Agent": "SmartPlaceProject/1.0",
                "Accept": "application/json",
            }
        )

        try:

            ssl_context = ssl.create_default_context(
                cafile=certifi.where()
            )

            with urlopen(
                request_obj,
                timeout=15,
                context=ssl_context
            ) as response:

                data = json.loads(
                    response.read().decode("utf-8")
                )

            if data:

                result = data[0]

                return JsonResponse({
                    "lat": float(result["lat"]),
                    "lon": float(result["lon"]),
                    "display_name": result.get(
                        "display_name",
                        search_query
                    )
                })

        except Exception as error:

            print(
                "Geocoding attempt failed:",
                search_query,
                error
            )

            continue

    return JsonResponse(
        {
            "error":
                f"Location not found: {query}. "
                "Try adding the city name."
        },
        status=404
    )
     
def nearby_services(request, place_id, service_type):
    place = get_object_or_404(Place, id=place_id)

    services = []

    if place.latitude is not None and place.longitude is not None:

        nearby = NearbyService.objects.filter(
            service_type=service_type
        )

        for service in nearby:

            distance = calculate_distance(
                place.latitude,
                place.longitude,
                service.latitude,
                service.longitude
            )

            if distance <= 25:
                service.distance = round(distance, 2)
                services.append(service)

        services.sort(
            key=lambda service: service.distance
        )

    service_names = {
        "hotel": ("🏨", "Hotels"),
        "restaurant": ("🍴", "Restaurants"),
       
        "fuel": ("⛽", "Fuel Stations"),
        "hospital": ("🏥", "Hospitals"),
        "bank": ("🏦", "Banks"),
        "cafe": ("☕", "Cafes"),
        "grocery": ("🛒", "Groceries"),
        "pharmacy": ("💊", "Pharmacies"),
        "transport": ("🚉", "Transport"),
    }

    icon, service_title = service_names.get(
        service_type,
        ("📍", "Nearby Services")
    )

    return render(request, "nearby_services.html", {
        "place": place,
        "services": services,
        "service_type": service_type,
        "service_title": service_title,
        "service_icon": icon,
    })

def get_route(start_lat, start_lon, end_lat, end_lon, profile="driving-car"):
    """
    Get a road route using OSRM.
    Returns the route in a format similar to the existing route page.
    """

    url = "https://router.project-osrm.org/route/v1/driving/"

    params = urlencode({
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
    })

    route_url = (
        f"{url}"
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
        f"?{params}"
    )

    request = Request(
        route_url,
        headers={
            "User-Agent": "SmartPlaceProject/1.0"
        }
    )

    try:
        ssl_context = ssl.create_default_context(
            cafile=certifi.where()
        )

        with urlopen(
            request,
            timeout=15,
            context=ssl_context
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        if data.get("code") != "Ok":
            print("Routing error:", data)
            return None

        osrm_route = data["routes"][0]

        # Convert OSRM response into the format
        # expected by our existing route page.
        return {
    "routes": [
        {
            "summary": {
                "distance": osrm_route["distance"],
                "duration": osrm_route["duration"],
            },
            "geometry": osrm_route["geometry"],
            "waypoints": data.get("waypoints", []),
        }
    ]
}

    except Exception as error:
        print("Routing error:", error)
        return None
def route_api(request):
    start_lat = request.GET.get("start_lat")
    start_lon = request.GET.get("start_lon")
    end_lat = request.GET.get("end_lat")
    end_lon = request.GET.get("end_lon")
    profile = request.GET.get("profile", "driving-car")

    if not all([start_lat, start_lon, end_lat, end_lon]):
        return JsonResponse(
            {"error": "Missing route coordinates"},
            status=400
        )

    try:
        route = get_route(
            float(start_lat),
            float(start_lon),
            float(end_lat),
            float(end_lon),
            profile
        )

        if not route:
            return JsonResponse(
                {"error": "Route could not be calculated"},
                status=500
            )

        return JsonResponse(route)

    except ValueError:
        return JsonResponse(
            {"error": "Invalid coordinates"},
            status=400
        )
def route_to_service(request, place_id, service_id):
    place = Place.objects.get(id=place_id)
    service = NearbyService.objects.get(id=service_id)

    return render(
        request,
        "route.html",
        {
            "place": place,
            "service": service,
        }
    )
@login_required
def route_planner(request):
    return render(request, "route_planner.html")
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import TripPlan


@login_required
@require_POST
def save_trip(request):
    try:
        data = json.loads(request.body)

        trip = TripPlan.objects.create(
            user=request.user,
            title=data.get("title", "My Trip"),
            start_location=data.get("start_location", ""),
            destination=data.get("destination", ""),
            stops=data.get("stops", []),
            route_details=data.get("route_details", []),
            total_distance=data.get("total_distance", 0),
            total_duration=data.get("total_duration", 0),
        )

        return JsonResponse({
            "success": True,
            "message": "Trip saved successfully!",
            "trip_id": trip.id,
        })

    except (ValueError, TypeError, KeyError):
        return JsonResponse({
            "success": False,
            "message": "Invalid trip data."
        }, status=400)
@login_required
def my_trips(request):
    trips = TripPlan.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "my_trips.html", {
        "trips": trips
    })
import os
import json
from openai import OpenAI
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect




@require_POST
@csrf_protect
def chat_assistant(request):
    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()

        if not message:
            return JsonResponse(
                {"reply": "Please enter a message."},
                status=400
            )

        if len(message) > 2000:
            return JsonResponse(
                {"reply": "Please keep your message under 2000 characters."},
                status=400
            )

        reply = find_answer(message)

        return JsonResponse({"reply": reply})

    except Exception as e:
        print("CHAT ASSISTANT ERROR:", repr(e))
        return JsonResponse(
            {"reply": "Sorry, something went wrong. Please try again."},
            status=500
        )