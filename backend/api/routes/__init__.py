from api.routes.health import router as health_router
from api.routes.search import router as search_router
from api.routes.trips import router as trips_router

__all__ = ["health_router", "search_router", "trips_router"]