import logging
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import TripPlanRequest, TripPlan, TripEditRequest
from app.agents.trip_planner import TripPlannerAgent
from app.services.unsplash import UnsplashService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trip", tags=["trip"])


def get_planner() -> TripPlannerAgent:
    return TripPlannerAgent()


def get_unsplash() -> UnsplashService:
    return UnsplashService()


def _enrich_images(trip_plan: TripPlan, city: str, unsplash: UnsplashService) -> None:
    for day in trip_plan.days:
        for attraction in day.attractions:
            if not attraction.image_url:
                image_url = unsplash.get_photo_url(f"{attraction.name} {city}")
                attraction.image_url = image_url or f"https://picsum.photos/seed/{attraction.name}/400/300"


@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(
    request: TripPlanRequest,
    planner: TripPlannerAgent = Depends(get_planner),
    unsplash: UnsplashService = Depends(get_unsplash),
) -> TripPlan:
    logger.info(f"收到旅行规划请求: {request.city} {request.days}天")

    try:
        trip_plan = planner.plan_trip(request)
        _enrich_images(trip_plan, request.city, unsplash)
        logger.info(f"旅行规划完成: {request.city}")
        return trip_plan
    except Exception as e:
        logger.error(f"生成计划失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="生成旅行计划失败，请稍后重试")


@router.post("/edit", response_model=TripPlan)
async def edit_trip_plan(
    request: TripEditRequest,
    planner: TripPlannerAgent = Depends(get_planner),
    unsplash: UnsplashService = Depends(get_unsplash),
) -> TripPlan:
    logger.info(f"收到行程编辑请求: {request.trip_plan.city}")

    try:
        updated_plan = planner.update_budget(request.trip_plan)
        _enrich_images(updated_plan, updated_plan.city, unsplash)
        logger.info(f"行程编辑完成: {updated_plan.city}")
        return updated_plan
    except Exception as e:
        logger.error(f"编辑计划失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="编辑旅行计划失败，请稍后重试")
