from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter4",
    tags=["Chapter 4 - Family Planning"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/contraception-use",
    response_model=IndicatorResponse,
    summary="4.1 Current Contraceptive Use",
    description="Percentage of currently married women using any contraceptive method (mCPR). Use `data_label` to select method type (Total, Modern, Traditional).",
)
async def get_contraception_use(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Modern", description="Method type: Total, Modern, Traditional"),
):
    return await build_indicator_response("4.1 Current Contraception", year, province_id, data_label)


@router.get(
    "/fp-demand",
    response_model=IndicatorResponse,
    summary="4.2 Demand for Family Planning Satisfied",
    description="Percentage of demand for family planning satisfied with modern methods.",
)
async def get_fp_demand(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("4.2 Demand for FP", year, province_id, data_label)


@router.get(
    "/fp-messages",
    response_model=IndicatorResponse,
    summary="4.3 Exposure to Family Planning Messages",
    description="Percentage of women exposed to family planning messages through any media channel.",
)
async def get_fp_messages(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("4.3 Exposure to Messages", year, province_id, data_label)
