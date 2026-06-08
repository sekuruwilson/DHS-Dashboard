from fastapi import APIRouter
from asgiref.sync import sync_to_async
from indicators.models import Province, DHSUploadedDataset, Indicator, Category
from rdhs_viz.schemas import ProvinceInfo, DatasetInfo, ChapterSummary, IndicatorSummary
from rdhs_viz.db_queries import DHS_PROVINCE_NAMES

router = APIRouter(tags=["Metadata"])

CHAPTERS = [
    "Chapter 1: Household characteristics",
    "Chapter 2: Respondent characteristics",
    "Chapter 3: Fertility determinants and fertility rates",
    "Chapter 4: Family planning",
    "Chapter 5: Maternal health",
    "Chapter 6: Child health",
    "Chapter 7: Nutrition among children and women",
    "Chapter 8: Malaria",
    "Chapter 9: HIV Attitude and Knowledge",
    "Chapter 10: Women empowerment",
]


@router.get("/", tags=["Metadata"], summary="API overview")
async def root():
    return {
        "title": "Rwanda DHS Dashboard API",
        "description": "Chapter-based endpoints for DHS Rwanda 2019-20 indicators.",
        "chapters": CHAPTERS,
        "docs": "/docs",
    }


@router.get("/health", tags=["Metadata"], summary="Health check")
async def health():
    return {"status": "ok"}


@router.get("/meta/provinces", response_model=list[ProvinceInfo], tags=["Metadata"], summary="List provinces with DHS codes")
async def get_provinces():
    """
    Returns all provinces with their **DHS survey code** (1–5).
    Use the `dhs_code` value as `province_id` when filtering chapter endpoints.

    | dhs_code | Province |
    |----------|----------|
    | 1 | Kigali City |
    | 2 | Southern Province |
    | 3 | Western Province |
    | 4 | Northern Province |
    | 5 | Eastern Province |
    """
    name_to_code = {v: k for k, v in DHS_PROVINCE_NAMES.items()}

    @sync_to_async
    def fetch():
        provs = Province.objects.prefetch_related('districts').filter(
            name__in=DHS_PROVINCE_NAMES.values()
        ).order_by('name')
        return [
            ProvinceInfo(
                dhs_code=name_to_code[p.name],
                name=p.name,
                district_count=p.districts.count(),
                districts=[d.name for d in p.districts.all().order_by('name')],
            )
            for p in provs
        ]
    return await fetch()


@router.get("/meta/datasets", response_model=list[DatasetInfo], tags=["Metadata"], summary="List uploaded DHS datasets")
async def get_datasets():
    @sync_to_async
    def fetch():
        datasets = DHSUploadedDataset.objects.all().order_by('-uploaded_at')
        return [
            DatasetInfo(
                id=d.id,
                recode_type=d.recode_type,
                year=d.year,
                original_filename=d.original_filename,
                uploaded_at=d.uploaded_at.isoformat(),
                num_rows=d.num_rows,
                num_vars=d.num_vars,
            )
            for d in datasets
        ]
    return await fetch()


@router.get("/meta/indicators", response_model=list[ChapterSummary], tags=["Metadata"], summary="All indicators grouped by chapter")
async def get_meta_indicators():
    @sync_to_async
    def fetch():
        results = []
        cats = Category.objects.prefetch_related('indicators').all().order_by('name')
        for cat in cats:
            indicators = cat.indicators.all()
            years_map: dict[str, set] = {}
            for ind in indicators:
                if ind.name not in years_map:
                    years_map[ind.name] = set()
                years_map[ind.name].add(ind.year)

            seen = set()
            items = []
            for ind in indicators:
                if ind.name not in seen:
                    seen.add(ind.name)
                    items.append(IndicatorSummary(
                        name=ind.name,
                        unit=ind.unit,
                        years_available=sorted(years_map[ind.name]),
                    ))
            results.append(ChapterSummary(chapter=cat.name, indicators=items))
        return results
    return await fetch()
