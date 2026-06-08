from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter5",
    tags=["Chapter 5 - Maternal Health"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/antenatal-care",
    response_model=IndicatorResponse,
    summary="5.1 Antenatal Care (Skilled Provider)",
    description="Percentage of live births in the last 5 years with at least one antenatal care visit from a skilled provider.",
)
async def get_antenatal_care(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("5.1 Antenatal Care (Skilled)", year, province_id, data_label)


@router.get(
    "/tetanus-protection",
    response_model=IndicatorResponse,
    summary="5.2 Tetanus Protection at Birth",
    description="Percentage of last births protected against neonatal tetanus.",
)
async def get_tetanus_protection(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("5.2 Tetanus Protection", year, province_id, data_label)


@router.get(
    "/delivery-place",
    response_model=IndicatorResponse,
    summary="5.3 Place of Delivery",
    description="Distribution of place of delivery for live births in the last 5 years. Use `data_label` to select: Health facility, Home, Other.",
)
async def get_delivery_place(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Health facility", description="Place: Health facility, Home, Other"),
):
    return await build_indicator_response("5.3 Place of Delivery", year, province_id, data_label)


@router.get(
    "/delivery-assistance",
    response_model=IndicatorResponse,
    summary="5.4 Assistance at Delivery",
    description="Percentage of live births assisted by a skilled provider (doctor, nurse/midwife).",
)
async def get_delivery_assistance(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("5.4 Assistance at Delivery", year, province_id, data_label)


@router.get(
    "/postnatal-care",
    response_model=IndicatorResponse,
    summary="5.5 Postnatal Checkups",
    description="Percentage of mothers who received a postnatal check within 2 days of delivery.",
)
async def get_postnatal_care(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("5.5 Postnatal Checkups", year, province_id, data_label)
