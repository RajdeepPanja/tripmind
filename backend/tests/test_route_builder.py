from models.common import GeoPoint, SourceRef
from models.constraints import TripConstraints
from models.enums import DataSource, PlaceCategory
from models.hotel import HotelOption
from models.place import Place
from services.route_builder import build_route_plan


def make_place(id_, lat, lon):
    return Place(
        id=id_,
        name=f"Place {id_}",
        category=PlaceCategory.ATTRACTION,
        location=GeoPoint(latitude=lat, longitude=lon),
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_MAPS),
    )


def make_hotel(lat, lon):
    return HotelOption(
        id="hotel1",
        name="Test Hotel",
        price_per_night={"amount": 3000, "currency": "INR"},
        total_price={"amount": 3000, "currency": "INR"},
        nights=1,
        location=GeoPoint(latitude=lat, longitude=lon),
        source_ref=SourceRef(source=DataSource.SERPAPI_GOOGLE_HOTELS),
    )


def make_constraints(**overrides):
    defaults = dict(
        max_budget_amount=50000,
        max_daily_activities=3,
        max_daily_travel_minutes=180,
    )
    defaults.update(overrides)
    return TripConstraints(**defaults)


def test_build_route_plan_distributes_places_across_days():
    places = [
        make_place(str(i), 26.9 + i * 0.001, 75.8 + i * 0.001)
        for i in range(6)
    ]

    hotel = make_hotel(26.9, 75.8)

    plan = build_route_plan(
        places,
        hotel,
        duration_days=2,
        constraints=make_constraints(
            max_daily_travel_minutes=180,
        ),
    )

    assert len(plan.days) == 2

    total_stops = sum(len(day.stops) for day in plan.days)

    assert total_stops == 6


def test_build_route_plan_empty_places_returns_empty_plan():
    plan = build_route_plan(
        [],
        None,
        duration_days=3,
        constraints=make_constraints(),
    )

    assert plan.days == []
    assert plan.total_distance_km == 0.0


def test_build_route_plan_orders_feasible_stops_nearest_first():
    near = make_place("near", 26.901, 75.801)
    middle = make_place("middle", 26.905, 75.805)

    hotel = make_hotel(26.9, 75.8)

    plan = build_route_plan(
        [middle, near],
        hotel,
        duration_days=1,
        constraints=make_constraints(
            max_daily_travel_minutes=180,
        ),
    )

    assert plan.days[0].stops[0].place_id == "near"
    assert plan.days[0].stops[1].place_id == "middle"


def test_build_route_plan_skips_place_that_exceeds_daily_travel_limit():
    near = make_place("near", 26.901, 75.801)

    # Deliberately far enough away that adding it would exceed
    # the configured daily travel limit.
    far = make_place("far", 27.5, 76.5)

    hotel = make_hotel(26.9, 75.8)

    plan = build_route_plan(
        [far, near],
        hotel,
        duration_days=1,
        constraints=make_constraints(
            max_daily_travel_minutes=180,
        ),
    )

    assert plan.days[0].stops[0].place_id == "near"
    assert all(
        day.total_travel_minutes <= 180
        for day in plan.days
    )


def test_build_route_plan_without_hotel_uses_first_place_as_start():
    places = [
        make_place(str(i), 26.9 + i * 0.001, 75.8 + i * 0.001)
        for i in range(3)
    ]

    plan = build_route_plan(
        places,
        None,
        duration_days=1,
        constraints=make_constraints(
            max_daily_travel_minutes=180,
        ),
    )

    assert len(plan.days[0].stops) == 3


def test_build_route_plan_respects_max_daily_activities():
    places = [
        make_place(str(i), 26.9 + i * 0.001, 75.8 + i * 0.001)
        for i in range(10)
    ]

    hotel = make_hotel(26.9, 75.8)

    plan = build_route_plan(
        places,
        hotel,
        duration_days=2,
        constraints=make_constraints(
            max_daily_activities=2,
            max_daily_travel_minutes=180,
        ),
    )

    total_stops = sum(
        len(day.stops)
        for day in plan.days
    )

    assert total_stops == 4


def test_build_route_plan_never_exceeds_daily_travel_limit():
    places = [
        make_place(str(i), 26.9 + i * 0.002, 75.8 + i * 0.002)
        for i in range(10)
    ]

    hotel = make_hotel(26.9, 75.8)

    plan = build_route_plan(
        places,
        hotel,
        duration_days=3,
        constraints=make_constraints(
            max_daily_activities=3,
            max_daily_travel_minutes=180,
        ),
    )

    for day in plan.days:
        assert day.total_travel_minutes <= 180