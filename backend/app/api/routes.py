from fastapi import APIRouter, HTTPException
from app.models.schemas import TripPlanRequest, TripPlan, TripEditRequest
from app.agents.trip_planner import TripPlannerAgent
from app.services.unsplash import UnsplashService

router = APIRouter(prefix="/api/trip", tags=["trip"])

trip_planner = TripPlannerAgent()
unsplash_service = UnsplashService()

@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    print(f"\n{'='*60}")
    print(f"📨 收到旅行规划请求: {request.city}")
    print(f"{'='*60}")

    try:
        print("🔄 开始调用Agent系统...")
        trip_plan = trip_planner.plan_trip(request)
        print("✅ Agent系统调用完成")

        print("📸 开始加载景点图片...")
        for day in trip_plan.days:
            for attraction in day.attractions:
                if not attraction.image_url:
                    print(f"  🔍 搜索图片: {attraction.name}")
                    image_url = unsplash_service.get_photo_url(
                        f"{attraction.name} {request.city}"
                    )
                    if image_url:
                        attraction.image_url = image_url
                        print(f"  ✅ 找到图片: {image_url[:50]}...")
                    else:
                        print(f"  ⚠️ 未找到图片，使用默认图片")
                        # 使用默认的占位图
                        attraction.image_url = f"https://picsum.photos/seed/{attraction.name}/400/300"

        print(f"\n✅ 旅行规划完成!")
        return trip_plan
    except Exception as e:
        print(f"\n❌ 生成计划失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成旅行计划失败: {str(e)}"
        )

@router.post("/edit", response_model=TripPlan)
async def edit_trip_plan(request: TripEditRequest) -> TripPlan:
    print(f"\n{'='*60}")
    print(f"✏️ 收到行程编辑请求: {request.trip_plan.city}")
    print(f"{'='*60}")

    try:
        print("🔄 开始重新计算预算...")
        updated_plan = trip_planner.update_budget(request.trip_plan)
        print("✅ 预算计算完成")

        print("📸 开始加载景点图片...")
        for day in updated_plan.days:
            for attraction in day.attractions:
                if not attraction.image_url:
                    print(f"  🔍 搜索图片: {attraction.name}")
                    image_url = unsplash_service.get_photo_url(
                        f"{attraction.name} {updated_plan.city}"
                    )
                    if image_url:
                        attraction.image_url = image_url
                        print(f"  ✅ 找到图片: {image_url[:50]}...")
                    else:
                        print(f"  ⚠️ 未找到图片，使用默认图片")
                        attraction.image_url = f"https://picsum.photos/seed/{attraction.name}/400/300"

        print(f"\n✅ 行程编辑完成!")
        return updated_plan
    except Exception as e:
        print(f"\n❌ 编辑计划失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"编辑旅行计划失败: {str(e)}"
        )
