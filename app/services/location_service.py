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
import unicodedata

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    """Strips combining diacritics/macrons (e.g. Kolhāpur -> Kolhapur) and strips whitespace."""
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip()


def _deduplicate_names(names: List[str]) -> List[str]:
    """
    Normalizes names by stripping diacritical marks and deduplicating case-insensitively.
    Prioritizes clean ASCII representation.
    """
    seen: Dict[str, str] = {}
    for n in names:
        if not n or not n.strip():
            continue
        cleaned = _normalize_name(n)
        key = cleaned.lower()
        if key not in seen:
            seen[key] = cleaned
        elif not any(ord(ch) > 127 for ch in cleaned):
            # Prefer plain ASCII
            seen[key] = cleaned
    return sorted(list(seen.values()), key=lambda x: x.lower())

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


def _get_db_distinct_locations(
    country: Optional[str] = None,
    state: Optional[str] = None,
) -> Dict[str, set]:
    """Dynamically gathers distinct location values recorded in Supplier & Customer tables, scoped by country and state."""
    distinct = {"countries": set(), "states": set(), "cities": set()}
    clean_country = (country or "").strip()
    clean_state = (state or "").strip()

    try:
        from app.models.supplier import Supplier
        from app.models.customer import Customer

        for model in (Supplier, Customer):
            # Only query distinct countries if no country filter is specified
            if not clean_country:
                records = model.query.with_entities(model.country).filter(model.country.isnot(None)).distinct().all()
                for (val,) in records:
                    if val and val.strip():
                        distinct["countries"].add(val.strip())

            # Only query states matching the specified country (or all if country not specified)
            state_query = model.query.with_entities(model.state).filter(model.state.isnot(None))
            if clean_country:
                state_query = state_query.filter(model.country.ilike(clean_country))
            for (val,) in state_query.distinct().all():
                if val and val.strip():
                    distinct["states"].add(val.strip())

            # Only query cities matching country and/or state
            city_query = model.query.with_entities(model.city).filter(model.city.isnot(None))
            if clean_country:
                city_query = city_query.filter(model.country.ilike(clean_country))
            if clean_state:
                city_query = city_query.filter(model.state.ilike(clean_state))
            for (val,) in city_query.distinct().all():
                if val and val.strip():
                    distinct["cities"].add(val.strip())
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
        unique = _deduplicate_names(countries)
        cached = ["India"] + [c for c in unique if c.lower() != "india"]

        with _LOCK:
            _CACHE["countries"] = cached

    result = cached
    if search and search.strip():
        q = _normalize_name(search).lower()
        result = [c for c in cached if q in _normalize_name(c).lower()]

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

        # Merge DB states for this specific country
        db_locs = _get_db_distinct_locations(country=clean_country)
        for s in db_locs["states"]:
            if s not in states:
                states.append(s)

        cached_states = _deduplicate_names(states)
        with _LOCK:
            _CACHE["states_by_country"][cache_key] = cached_states

    result = cached_states
    if search and search.strip():
        q = _normalize_name(search).lower()
        result = [s for s in cached_states if q in _normalize_name(s).lower()]

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

        # Augment with any cities already present in DB for this specific country & state
        db_locs = _get_db_distinct_locations(country=clean_country, state=clean_state)
        for db_city in db_locs["cities"]:
            if db_city not in cities:
                cities.append(db_city)

        cached_cities = _deduplicate_names(cities)
        with _LOCK:
            _CACHE["cities_by_state"][cache_key] = cached_cities

    result = cached_cities
    if search and search.strip():
        q = _normalize_name(search).lower()
        result = [c for c in cached_cities if q in _normalize_name(c).lower()]

    if limit and isinstance(limit, int) and limit > 0:
        result = result[:limit]

    return result


def lookup_location(
    city: str,
    country: Optional[str] = None,
    state: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """
    Dynamically resolves state and country for a given city name
    using OpenStreetMap Nominatim reverse lookup with English language response and caching.
    Supports contextual country and state filtering and exact name matching.
    """
    if not city or not city.strip():
        return None

    clean_city = city.strip()
    clean_country = (country or "").strip()
    clean_state = (state or "").strip()
    cache_key = f"{clean_city.lower()}|{clean_country.lower()}|{clean_state.lower()}"

    with _LOCK:
        if cache_key in _CACHE["lookups"]:
            return _CACHE["lookups"][cache_key]

    # Try OpenStreetMap Nominatim live search in English
    resolved: Optional[Dict[str, str]] = None
    try:
        params: Dict[str, Any] = {
            "city": clean_city,
            "format": "json",
            "addressdetails": 1,
            "limit": 10,
        }
        if clean_country:
            params["country"] = clean_country
        if clean_state:
            params["state"] = clean_state

        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers={"User-Agent": "MaterialManagementBackend/1.0", "Accept-Language": "en"},
            timeout=5,
        )
        if resp.status_code == 200:
            results = resp.json()
            if results and len(results) > 0:
                best_item = None
                clean_city_lower = clean_city.lower()
                clean_country_lower = clean_country.lower()

                for item in results:
                    addr = item.get("address", {})
                    item_name = (item.get("name") or "").strip().lower()
                    addr_city = (
                        addr.get("city")
                        or addr.get("town")
                        or addr.get("village")
                        or addr.get("municipality")
                        or ""
                    ).strip().lower()
                    addr_country = (addr.get("country") or "").strip().lower()

                    name_exact = (item_name == clean_city_lower or addr_city == clean_city_lower)
                    country_matches = (
                        not clean_country_lower
                        or clean_country_lower == addr_country
                        or clean_country_lower in addr_country
                        or addr_country in clean_country_lower
                    )

                    if name_exact and country_matches:
                        best_item = item
                        break
                    elif name_exact and not best_item:
                        best_item = item
                    elif country_matches and not best_item:
                        best_item = item

                if not best_item:
                    best_item = results[0]

                addr = best_item.get("address", {})
                res_city = (
                    addr.get("city")
                    or addr.get("town")
                    or addr.get("village")
                    or addr.get("municipality")
                    or best_item.get("name")
                    or clean_city
                )
                res_country = addr.get("country") or clean_country or "India"
                raw_state = (
                    addr.get("state")
                    or addr.get("state_district")
                    or addr.get("county")
                    or clean_state
                )
                res_state = raw_state
                if res_country and raw_state:
                    try:
                        avail_states = list_states(res_country)
                        for st in avail_states:
                            if st.lower() in raw_state.lower() or raw_state.lower() in st.lower():
                                res_state = st
                                break
                    except Exception:
                        pass

                resolved = {
                    "city": _normalize_name(res_city) or clean_city,
                    "state": _normalize_name(res_state) or clean_state,
                    "country": _normalize_name(res_country) or (clean_country or "India"),
                }
    except Exception as e:
        logger.warning(f"Dynamic lookup failed for {clean_city}: {e}")

    # Fallback to DB entities if Nominatim did not find it
    if not resolved:
        try:
            from app.models.supplier import Supplier
            from app.models.customer import Customer

            for model in (Supplier, Customer):
                query = model.query.filter(model.city.ilike(clean_city))
                if clean_country:
                    query = query.filter(model.country.ilike(clean_country))
                record = query.first()
                if record and record.state:
                    resolved = {
                        "city": record.city or clean_city,
                        "state": record.state or "",
                        "country": record.country or (clean_country or "India"),
                    }
                    break
        except Exception:
            pass

    if resolved:
        with _LOCK:
            _CACHE["lookups"][cache_key] = resolved

    return resolved
