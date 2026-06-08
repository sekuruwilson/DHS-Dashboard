from pydantic import BaseModel
from typing import Optional


class DistrictResult(BaseModel):
    district_id: int
    district_name: str
    value: Optional[float]
    data_label: str


class ProvinceResult(BaseModel):
    province_id: int
    province_name: str
    value: Optional[float]


class NationalResult(BaseModel):
    value: Optional[float]


class IndicatorResponse(BaseModel):
    indicator: str
    unit: str
    category: str
    year: int
    data_source: str = "DHS Rwanda 2019-20"
    districts: list[DistrictResult]
    provinces: list[ProvinceResult]
    national: NationalResult


class IndicatorSummary(BaseModel):
    name: str
    unit: str
    years_available: list[int]


class ChapterSummary(BaseModel):
    chapter: str
    indicators: list[IndicatorSummary]


class ProvinceInfo(BaseModel):
    dhs_code: int
    name: str
    district_count: int
    districts: list[str]


class DatasetInfo(BaseModel):
    id: int
    recode_type: str
    year: int
    original_filename: str
    uploaded_at: str
    num_rows: Optional[int]
    num_vars: Optional[int]
