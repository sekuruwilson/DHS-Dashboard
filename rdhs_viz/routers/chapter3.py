from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter3",
    tags=["Chapter 3 - Fertility Determinants & Rates"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/median-age-first-marriage",
    response_model=IndicatorResponse,
    summary="3.1 Median Age at First Marriage",
    description="Median age at first marriage among women aged 25–49.",
)
async def get_median_age_marriage(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("3.1 Median Age at First Marriage", year, province_id, data_label)


@router.get(
    "/birth-intervals",
    response_model=IndicatorResponse,
    summary="3.2 Birth Intervals",
    description="Median months between births.",
)
async def get_birth_intervals(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("3.2 Birth Interval", year, province_id, data_label)


@router.get(
    "/median-age-first-birth",
    response_model=IndicatorResponse,
    summary="3.3 Median Age at First Birth",
    description="Median age at first birth among women aged 25–49.",
)
async def get_median_age_birth(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("3.3 Median Age at First Birth", year, province_id, data_label)


@router.get(
    "/teenage-pregnancy",
    response_model=IndicatorResponse,
    summary="3.4 Teenage Pregnancy",
    description="Percentage of women aged 15–19 who have begun childbearing.",
)
async def get_teenage_pregnancy(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("3.4 Teenage Pregnancy", year, province_id, data_label)


@router.get(
    "/mean-children-ever-born",
    response_model=IndicatorResponse,
    summary="3.5 Mean Children Ever Born (Fertility Proxy)",
    description="Mean number of children ever born per woman — used as a fertility rate proxy.",
)
async def get_mean_children_ever_born(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("3.5 Fertility (Mean Children Ever Born)", year, province_id, data_label)
