from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter6",
    tags=["Chapter 6 - Child Health"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/illness-prevalence",
    response_model=IndicatorResponse,
    summary="6.1–6.3 Child Illness Prevalence (ARI / Fever / Diarrhea)",
    description="Percentage of children under 5 with ARI, fever, or diarrhea in the two weeks before the survey. Use `data_label` to select: ARI, Fever, Diarrhea.",
)
async def get_illness_prevalence(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Fever", description="Illness type: ARI, Fever, Diarrhea"),
):
    return await build_indicator_response("6.1-6.3 Illness Prevalence (ARI/Fever/Diarrhea)", year, province_id, data_label)


@router.get(
    "/child-anemia",
    response_model=IndicatorResponse,
    summary="6.4 Anemia in Children",
    description="Percentage of children aged 6–59 months with any anemia.",
)
async def get_child_anemia(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("6.4 Anemia (Children)", year, province_id, data_label)
