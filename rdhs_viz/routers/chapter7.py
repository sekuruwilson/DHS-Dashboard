from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter7",
    tags=["Chapter 7 - Nutrition (Children & Women)"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/child-nutrition",
    response_model=IndicatorResponse,
    summary="7.1 Child Nutrition Status",
    description="Percentage of children under 5 who are stunted, wasted, or underweight. Use `data_label` to select: Stunted, Wasted, Underweight.",
)
async def get_child_nutrition(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Stunted", description="Status: Stunted, Wasted, Underweight"),
):
    return await build_indicator_response("7.1 Child Nutrition Status", year, province_id, data_label)


@router.get(
    "/women-bmi",
    response_model=IndicatorResponse,
    summary="7.2 Women's Body Mass Index (BMI)",
    description="Distribution of BMI categories among women aged 15–49. Use `data_label` to select: Thin, Normal, Overweight/Obese.",
)
async def get_women_bmi(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Overweight/Obese", description="BMI category: Thin, Normal, Overweight/Obese"),
):
    return await build_indicator_response("7.2 Women's BMI", year, province_id, data_label)


@router.get(
    "/women-anemia",
    response_model=IndicatorResponse,
    summary="7.3 Anemia in Women",
    description="Percentage of non-pregnant women aged 15–49 with any anemia.",
)
async def get_women_anemia(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("7.3 Women's Anemia", year, province_id, data_label)
