from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter10",
    tags=["Chapter 10 - Women's Empowerment"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/earnings-control-women",
    response_model=IndicatorResponse,
    summary="10.1 Control over Women's Cash Earnings",
    description="Percentage of employed women who have sole or joint control over their own cash earnings.",
)
async def get_earnings_control_women(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("10.1 Control Women's Earnings", year, province_id, data_label)


@router.get(
    "/earnings-control-men",
    response_model=IndicatorResponse,
    summary="10.2 Control over Men's Cash Earnings",
    description="Percentage of currently married women who have sole or joint say over how their husband's earnings are used.",
)
async def get_earnings_control_men(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("10.2 Control Men's Earnings", year, province_id, data_label)


@router.get(
    "/decision-making",
    response_model=IndicatorResponse,
    summary="10.3 Women's Participation in Decision-Making",
    description="Percentage of currently married women who participate in all three key household decisions (own health, major purchases, visits to family).",
)
async def get_decision_making(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("10.3 Decision Making", year, province_id, data_label)


@router.get(
    "/attitude-violence",
    response_model=IndicatorResponse,
    summary="10.4 Attitude toward Wife Beating",
    description="Percentage of women who justify wife beating for at least one reason.",
)
async def get_attitude_violence(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("10.4 Wife Beating Justified", year, province_id, data_label)
