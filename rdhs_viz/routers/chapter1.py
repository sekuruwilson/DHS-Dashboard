from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter1",
    tags=["Chapter 1 - Household Characteristics"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/electricity",
    response_model=IndicatorResponse,
    summary="1.1 Electricity Coverage",
    description="Percentage of households with electricity access, by district and province.",
)
async def get_electricity(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown (e.g. Total, Urban, Rural)"),
):
    return await build_indicator_response("1.1 Electricity coverage", year, province_id, data_label)


@router.get(
    "/household-assets",
    response_model=IndicatorResponse,
    summary="1.2 Household Durable Goods",
    description="Ownership of durable goods (radio, TV, mobile, computer, etc.). Use `data_label` to select a specific good.",
)
async def get_household_assets(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Radio", description="Good to display: Radio, Television, Mobile Phone, Computer, Refrigerator, Bicycle, Motorcycle, Car/Truck"),
):
    return await build_indicator_response("1.2 Household durable goods", year, province_id, data_label)


@router.get(
    "/handwashing",
    response_model=IndicatorResponse,
    summary="1.3 Hand Washing Place",
    description="Distribution of hand washing place type (Fixed, Mobile, No specific place). Use `data_label` to select type.",
)
async def get_handwashing(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Fixed place", description="Place type: Fixed place, Mobile place, No specific place"),
):
    return await build_indicator_response("1.3 Hand washing place", year, province_id, data_label)
