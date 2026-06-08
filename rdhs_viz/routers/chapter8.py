from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter8",
    tags=["Chapter 8 - Malaria"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/itn-use-total",
    response_model=IndicatorResponse,
    summary="8.1 ITN Use — Total Household Population",
    description="Percentage of the total household population who slept under an insecticide-treated net (ITN) the night before the survey.",
)
async def get_itn_use_total(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("8.1 ITN Use (Total HH Pop)", year, province_id, data_label)


@router.get(
    "/itn-use-children",
    response_model=IndicatorResponse,
    summary="8.2 ITN Use — Children Under 5",
    description="Percentage of children under 5 who slept under an ITN the night before the survey.",
)
async def get_itn_use_children(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("8.2 ITN Use (Children)", year, province_id, data_label)


@router.get(
    "/malaria-prevalence",
    response_model=IndicatorResponse,
    summary="8.3/8.4 Malaria Prevalence in Children",
    description="Percentage of children aged 6–59 months testing positive for malaria (RDT or microscopy).",
)
async def get_malaria_prevalence(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("8.3/8.4 Malaria Prevalence", year, province_id, data_label)
