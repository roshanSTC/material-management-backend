"""
Location master endpoints for dynamic Country, State, and City fetching.
"""

from flask import request
from flask_smorest import Blueprint
from app.services import location_service

location_bp = Blueprint(
    "locations",
    __name__,
    url_prefix="/api/v1/locations",
    description="Geographic master data (Countries, States, Cities, and Reverse Lookup)",
)


@location_bp.get("/countries")
@location_bp.doc(description="Get list of supported and registered countries")
def get_countries():
    search = request.args.get("search", "").strip() or None
    countries = location_service.list_countries(search=search)
    return {
        "success": True,
        "count": len(countries),
        "data": countries
    }, 200


@location_bp.get("/states")
@location_bp.doc(description="Get list of states/territories for a country (defaults to India)")
def get_states():
    country = request.args.get("country", "India").strip() or "India"
    search = request.args.get("search", "").strip() or None
    states = location_service.list_states(country=country, search=search)
    return {
        "success": True,
        "country": country,
        "count": len(states),
        "data": states
    }, 200


@location_bp.get("/cities")
@location_bp.doc(description="Get list of cities for a state/country or search query")
def get_cities():
    country = request.args.get("country", "").strip() or None
    state = request.args.get("state", "").strip() or None
    search = request.args.get("search", "").strip() or request.args.get("q", "").strip() or None
    limit = int(request.args.get("limit", 200))

    cities = location_service.list_cities(
        country=country,
        state=state,
        search=search,
        limit=limit
    )
    return {
        "success": True,
        "country": country,
        "state": state,
        "count": len(cities),
        "data": cities
    }, 200


@location_bp.get("/lookup")
@location_bp.doc(description="Auto-resolve State and Country from City name")
def lookup():
    city = request.args.get("city", "").strip()
    if not city:
        return {
            "success": False,
            "error": "City parameter is required"
        }, 400

    match = location_service.lookup_location(city)
    if not match:
        return {
            "success": False,
            "message": "City not found in database or master catalog",
            "data": None
        }, 404

    return {
        "success": True,
        "data": match
    }, 200
