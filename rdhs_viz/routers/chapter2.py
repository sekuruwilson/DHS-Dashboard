from fastapi import APIRouter, Query
from typing import Optional
from rdhs_viz.schemas import IndicatorResponse
from rdhs_viz.db_queries import build_indicator_response

router = APIRouter(
    prefix="/chapter2",
    tags=["Chapter 2 - Demographics & Respondent Characteristics"],
    responses={404: {"description": "Indicator not found or not yet computed"}},
)


@router.get(
    "/education-women",
    response_model=IndicatorResponse,
    summary="2.1 Education Attainment (Women)",
    description="Distribution of education level among women aged 6+. Use `data_label` for level: No education, Primary, Secondary, Higher.",
)
async def get_education_women(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Secondary", description="Education level: No education, Primary, Secondary, Higher"),
):
    return await build_indicator_response("2.1 Education (Women)", year, province_id, data_label)


@router.get(
    "/education-men",
    response_model=IndicatorResponse,
    summary="2.1 Education Attainment (Men)",
    description="Distribution of education level among men aged 6+. Use `data_label` for level: No education, Primary, Secondary, Higher.",
)
async def get_education_men(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Secondary", description="Education level: No education, Primary, Secondary, Higher"),
):
    return await build_indicator_response("2.1 Education (Men)", year, province_id, data_label)


@router.get(
    "/birth-registration",
    response_model=IndicatorResponse,
    summary="2.2 Birth Registration",
    description="Percentage of children under 5 whose births are registered.",
)
async def get_birth_registration(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("2.2 Birth Registration", year, province_id, data_label)


@router.get(
    "/orphanhood",
    response_model=IndicatorResponse,
    summary="2.3 Orphanhood",
    description="Percentage of children under 18 who have lost one or both parents.",
)
async def get_orphanhood(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Total", description="Demographic breakdown"),
):
    return await build_indicator_response("2.3 Orphanhood", year, province_id, data_label)


@router.get(
    "/health-insurance",
    response_model=IndicatorResponse,
    summary="2.4 Health Insurance Coverage",
    description="Percentage of women and men with health insurance. Use `data_label` to select Women or Men.",
)
async def get_health_insurance(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Women", description="Population: Women, Men"),
):
    return await build_indicator_response("2.4 Health Insurance", year, province_id, data_label)


@router.get(
    "/media-exposure",
    response_model=IndicatorResponse,
    summary="2.5 Media Exposure",
    description="Percentage of women and men exposed to media (newspaper, radio, TV). Use `data_label` to select Women or Men.",
)
async def get_media_exposure(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Women", description="Population: Women, Men"),
):
    return await build_indicator_response("2.5 Media Exposure", year, province_id, data_label)


@router.get(
    "/marital-status",
    response_model=IndicatorResponse,
    summary="2.6 Marital Status (Women)",
    description="Distribution of marital status among women. Use `data_label` for status: Never married, Married, Living together, Widowed, Divorced, Separated.",
)
async def get_marital_status(
    year: Optional[int] = Query(None, description="Survey year (default: latest available)"),
    province_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by province ID (1–5)"),
    data_label: str = Query("Married", description="Status: Never married, Married, Living together, Widowed, Divorced, Separated"),
):
    return await build_indicator_response("2.6 Marital Status (Women)", year, province_id, data_label)
