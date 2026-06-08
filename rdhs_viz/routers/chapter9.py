from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter9",
    tags=["Chapter 9 - HIV Attitude & Knowledge"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/hiv-knowledge-prevention",
    response_model=IndicatorResponse,
    summary="9.1 HIV Prevention Knowledge",
    description="Percentage of women who know any HIV prevention method.",
)
async def get_hiv_knowledge_prevention(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("9.1 HIV Knowledge (Prevention)", year, province_id, data_label)


@router.get(
    "/hiv-knowledge-comprehensive",
    response_model=IndicatorResponse,
    summary="9.2 Comprehensive HIV Knowledge",
    description="Percentage of women with comprehensive knowledge of HIV prevention (knows all five key prevention methods).",
)
async def get_hiv_knowledge_comprehensive(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("9.2 HIV Knowledge (Comprehensive)", year, province_id, data_label)


@router.get(
    "/multiple-partners",
    response_model=IndicatorResponse,
    summary="9.3 Multiple Sexual Partners (Men)",
    description="Percentage of men aged 15–49 who had two or more sexual partners in the past 12 months.",
)
async def get_multiple_partners(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("9.3 Multiple Partners (Men)", year, province_id, data_label)


@router.get(
    "/paid-sex",
    response_model=IndicatorResponse,
    summary="9.4 Paid Sex (Men)",
    description="Percentage of men aged 15–49 who paid for sex in the last 12 months.",
)
async def get_paid_sex(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("9.4 Paid Sex (Men)", year, province_id, data_label)


@router.get(
    "/sti-prevalence",
    response_model=IndicatorResponse,
    summary="9.5 STI Prevalence / Symptoms (Women)",
    description="Percentage of women who reported STI symptoms in the last 12 months.",
)
async def get_sti_prevalence(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("9.5 STI Prevalence (Women)", year, province_id, data_label)


@router.get(
    "/circumcision",
    response_model=IndicatorResponse,
    summary="9.6 Male Circumcision",
    description="Percentage of men aged 15–49 who are circumcised.",
)
async def get_circumcision(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("9.6 Circumcision (Men)", year, province_id, data_label)
