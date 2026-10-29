"""
Dynamic Location Service for Material Management System.
Fetches global geographic data dynamically via open geocoding and location APIs
(CountriesNow & OpenStreetMap Nominatim), combined dynamically with distinct
records from the PostgreSQL database (Supplier & Customer models).
Includes thread-safe in-memory caching for sub-millisecond repeated responses.
"""

import logging
import threading
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

# Dynamic In-Memory Cache
_LOCK = threading.Lock()
_CACHE: Dict[str, Any] = {
    "countries": None,
    "states_by_country": {},
    "cities_by_state": {},
    "lookups": {},
}

DEFAULT_COUNTRIES = [
    "India",
    "Australia",
    "Austria",
    "Bahrain",
    "Belgium",
    "Brazil",
    "Canada",
    "China",
    "Denmark",
    "France",
    "Germany",
    "Indonesia",
    "Italy",
    "Japan",
    "Kuwait",
    "Malaysia",
    "Mexico",
    "Netherlands",
    "New Zealand",
    "Oman",
    "Poland",
    "Qatar",
    "Saudi Arabia",
    "Singapore",
    "South Africa",
    "South Korea",
    "Spain",
    "Sweden",
    "Switzerland",
    "Taiwan",
    "Thailand",
    "Turkey",
    "United Arab Emirates",
    "United Kingdom",
    "United States",
    "Vietnam",
]

DEFAULT_INDIAN_STATES = [
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]


def _get_db_distinct_locations() -> Dict[str, set]:
    """Dynamically gathers distinct location values recorded in Supplier & Customer tables."""
    distinct = {"countries": set(), "states": set(), "cities": set()}
    try:
        from app.models.supplier import Supplier
        from app.models.customer import Customer

        for model in (Supplier, Customer):
            for field, key in [
                (model.country, "countries"),
                (model.state, "states"),
                (model.city, "cities"),
            ]:
                if hasattr(model, field.key):
                    records = model.query.with_entities(field).filter(field.isnot(None)).distinct().all()
                    for (val,) in records:
                        if val and val.strip():
                            distinct[key].add(val.strip())
    except Exception as e:
        logger.debug(f"DB distinct locations query skipped: {e}")

    return distinct


def list_countries(search: Optional[str] = None) -> List[str]:
    """Dynamically returns list of all countries, prioritizing India."""
    with _LOCK:
        cached = _CACHE.get("countries")

    if cached is None:
        countries: List[str] = []
        try:
            resp = requests.get("https://countriesnow.space/api/v0.1/countries/iso", timeout=4)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                for item in data:
                    name = item.get("name")
                    if name and name.strip():
                        countries.append(name.strip())
        except Exception as e:
            logger.warning(f"Failed to fetch dynamic countries from API: {e}")

        if not countries:
            countries = list(DEFAULT_COUNTRIES)

        # Merge distinct countries from PostgreSQL
        db_locs = _get_db_distinct_locations()
        for c in db_locs["countries"]:
            if c not in countries:
                countries.append(c)

        # Clean and sort with India on top
        unique = sorted(list(set(countries)), key=lambda x: x.lower())
        cached = ["India"] + [c for c in unique if c.lower() != "india"]

        with _LOCK:
            _CACHE["countries"] = cached

    result = cached
    if search and search.strip():
        q = search.strip().lower()
        result = [c for c in cached if q in c.lower()]

    return result


def list_states(country: Optional[str] = None, search: Optional[str] = None) -> List[str]:
    """Dynamically returns states for the given country."""
    clean_country = (country or "India").strip()
    cache_key = clean_country.lower()

    with _LOCK:
        cached_states = _CACHE["states_by_country"].get(cache_key)

    if cached_states is None:
        states: List[str] = []
        try:
            resp = requests.post(
                "https://countriesnow.space/api/v0.1/countries/states",
                json={"country": clean_country},
                timeout=4,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                raw_states = data.get("states", [])
                for st in raw_states:
                    name = st.get("name")
                    if name and name.strip():
                        states.append(name.strip())
        except Exception as e:
            logger.warning(f"Failed to fetch dynamic states for {clean_country}: {e}")

        if not states and clean_country.lower() in ("india", "bharat"):
            states = list(DEFAULT_INDIAN_STATES)

        # Merge DB states
        db_locs = _get_db_distinct_locations()
        for s in db_locs["states"]:
            if s not in states:
                states.append(s)

        cached_states = sorted(list(set(states)), key=lambda x: x.lower())
        with _LOCK:
            _CACHE["states_by_country"][cache_key] = cached_states

    result = cached_states
    if search and search.strip():
        q = search.strip().lower()
        result = [s for s in cached_states if q in s.lower()]

    return result


def list_cities(
    country: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[str]:
    """Dynamically returns cities for the given country and state, with optional search filtering and limit."""
    clean_country = (country or "India").strip()
    clean_state = (state or "").strip()
    cache_key = f"{clean_country.lower()}|{clean_state.lower()}"

    with _LOCK:
        cached_cities = _CACHE["cities_by_state"].get(cache_key)

    if cached_cities is None:
        cities: List[str] = []
        if clean_state:
            try:
                resp = requests.post(
                    "https://countriesnow.space/api/v0.1/countries/state/cities",
                    json={"country": clean_country, "state": clean_state},
                    timeout=4,
                )
                if resp.status_code == 200:
                    raw_cities = resp.json().get("data", [])
                    cities = [c.strip() for c in raw_cities if c and c.strip()]
            except Exception as e:
                logger.warning(f"Failed to fetch dynamic cities for {clean_state}, {clean_country}: {e}")

        # If clean_state returned empty or no state specified, try country cities
        if not cities and not clean_state:
            try:
                resp = requests.post(
                    "https://countriesnow.space/api/v0.1/countries/cities",
                    json={"country": clean_country},
                    timeout=4,
                )
                if resp.status_code == 200:
                    raw_cities = resp.json().get("data", [])
                    cities = [c.strip() for c in raw_cities if c and c.strip()]
            except Exception as e:
                logger.warning(f"Failed to fetch country cities for {clean_country}: {e}")

        # Augment with any cities already present in DB
        db_locs = _get_db_distinct_locations()
        for db_city in db_locs["cities"]:
            if db_city not in cities:
                cities.append(db_city)

        cached_cities = sorted(list(set(cities)), key=lambda x: x.lower())
        with _LOCK:
            _CACHE["cities_by_state"][cache_key] = cached_cities

    result = cached_cities
    if search and search.strip():
        q = search.strip().lower()
        result = [c for c in cached_cities if q in c.lower()]

    if limit and isinstance(limit, int) and limit > 0:
        result = result[:limit]

    return result


def lookup_location(city: str) -> Optional[Dict[str, str]]:
    """
    Dynamically resolves state and country for a given city name
    using OpenStreetMap Nominatim reverse lookup with English language response and caching.
    """
    if not city or not city.strip():
        return None

    clean_city = city.strip()
    cache_key = clean_city.lower()

    with _LOCK:
        if cache_key in _CACHE["lookups"]:
            return _CACHE["lookups"][cache_key]

    # Try OpenStreetMap Nominatim live search in English
    resolved: Optional[Dict[str, str]] = None
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"city": clean_city, "format": "json", "addressdetails": 1, "limit": 1},
            headers={"User-Agent": "MaterialManagementBackend/1.0", "Accept-Language": "en"},
            timeout=4,
        )
        if resp.status_code == 200:
            results = resp.json()
            if results and len(results) > 0:
                addr = results[0].get("address", {})
                res_city = addr.get("city") or addr.get("town") or addr.get("village") or clean_city
                res_state = addr.get("state") or addr.get("county") or ""
                res_country = addr.get("country") or "India"
                resolved = {
                    "city": res_city,
                    "state": res_state,
                    "country": res_country,
                }
    except Exception as e:
        logger.warning(f"Dynamic lookup failed for {clean_city}: {e}")

    # Fallback to DB entities if Nominatim did not find it
    if not resolved:
        try:
            from app.models.supplier import Supplier
            from app.models.customer import Customer

            for model in (Supplier, Customer):
                record = model.query.filter(model.city.ilike(clean_city)).first()
                if record and record.state:
                    resolved = {
                        "city": record.city or clean_city,
                        "state": record.state or "",
                        "country": record.country or "India",
                    }
                    break
        except Exception:
            pass

    if resolved:
        with _LOCK:
            _CACHE["lookups"][cache_key] = resolved

    return resolved
