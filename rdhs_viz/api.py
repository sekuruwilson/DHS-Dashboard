from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from asgiref.sync import sync_to_async
from indicators.models import Category, Indicator, IndicatorValue, District, Province

from rdhs_viz.routers import metadata, chapter1, chapter2, chapter3, chapter4, chapter5
from rdhs_viz.routers import chapter6, chapter7, chapter8, chapter9, chapter10

app = FastAPI(
    title="Rwanda DHS Dashboard API",
    description=(
        "Chapter-based REST API for DHS Rwanda 2019-20 health and demographic indicators. "
        "Endpoints are organized by survey chapter and return district, province, and national breakdowns."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Chapter routers ---
app.include_router(metadata.router)
app.include_router(chapter1.router)
app.include_router(chapter2.router)
app.include_router(chapter3.router)
app.include_router(chapter4.router)
app.include_router(chapter5.router)
app.include_router(chapter6.router)
app.include_router(chapter7.router)
app.include_router(chapter8.router)
app.include_router(chapter9.router)
app.include_router(chapter10.router)


# ---------------------------------------------------------------------------
# Legacy generic endpoints (kept for backward compatibility)
# ---------------------------------------------------------------------------

class CategorySchema(BaseModel):
    id: int
    name: str
    description: Optional[str]

class IndicatorSchema(BaseModel):
    id: int
    category_id: int
    name: str
    unit: str
    year: int

class LocationSchema(BaseModel):
    id: int
    name: str
    type: str

class ValueSchema(BaseModel):
    indicator_id: int
    location_id: int
    location_name: str
    data_label: str
    year: int
    value: float
    urban_value: Optional[float]
    rural_value: Optional[float]
    confidence_interval_lower: Optional[float]
    confidence_interval_upper: Optional[float]


@app.get(
    "/categories",
    response_model=List[CategorySchema],
    tags=["Legacy — Generic"],
    summary="List all data categories (chapters)",
)
async def get_categories():
    categories = await sync_to_async(list)(Category.objects.all().order_by('name'))
    return [CategorySchema(id=c.id, name=c.name, description=c.description) for c in categories]


@app.get(
    "/indicators",
    response_model=List[IndicatorSchema],
    tags=["Legacy — Generic"],
    summary="List indicators, optionally filtered by category",
)
async def get_indicators(category_id: Optional[int] = Query(None, description="Filter by category ID")):
    qs = Indicator.objects.all()
    if category_id:
        qs = qs.filter(category_id=category_id)
    indicators = await sync_to_async(list)(qs.order_by('name'))
    return [
        IndicatorSchema(id=i.id, category_id=i.category_id, name=i.name, unit=i.unit, year=i.year)
        for i in indicators
    ]


@app.get(
    "/values",
    response_model=List[ValueSchema],
    tags=["Legacy — Generic"],
    summary="Get raw data values for an indicator",
    description="Returns district-level values. Provide `indicator_id` (required). Optional filters: year, district_id, province_id, data_label.",
)
async def get_values(
    indicator_id: int = Query(..., description="Indicator ID (required)"),
    year: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    province_id: Optional[int] = Query(None),
    data_label: Optional[str] = Query(None),
):
    qs = IndicatorValue.objects.filter(indicator_id=indicator_id)
    if year:
        qs = qs.filter(year=year)
    if district_id:
        qs = qs.filter(district_id=district_id)
    if province_id:
        qs = qs.filter(district__province_id=province_id)
    if data_label:
        qs = qs.filter(data_label=data_label)
    qs = qs.select_related('district', 'district__province')
    values = await sync_to_async(list)(qs)
    return [
        ValueSchema(
            indicator_id=v.indicator_id,
            location_id=v.district_id or 0,
            location_name=v.district.name if v.district else "Unknown",
            data_label=v.data_label,
            year=v.year,
            value=v.value,
            urban_value=None,
            rural_value=None,
            confidence_interval_lower=None,
            confidence_interval_upper=None,
        )
        for v in values
    ]
