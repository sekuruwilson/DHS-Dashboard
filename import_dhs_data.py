#!/usr/bin/env python3
"""
DHS Data Importer
-----------------
Reads all JSON files from DHS/Chap X/ folders and imports into SQLite.
Run:  python import_dhs_data.py
"""

import os, sys, json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rdhs_viz.settings')

import django
django.setup()

from indicators.models import Category, Indicator, IndicatorValue, District, Province

YEAR = 2020

CHAPTERS = {
    1:  {"name": "Chapter 1: Household Characteristics",    "description": "Housing, utilities, and household assets"},
    2:  {"name": "Chapter 2: Population and Household",     "description": "Demographics, education, media, and registration"},
    3:  {"name": "Chapter 3: Fertility",                    "description": "Fertility rates, birth intervals, and teenage pregnancy"},
    4:  {"name": "Chapter 4: Family Planning",              "description": "Contraception use and family planning knowledge"},
    5:  {"name": "Chapter 5: Maternal Health",              "description": "Antenatal, delivery assistance, and postnatal care"},
    6:  {"name": "Chapter 6: Child Health",                 "description": "Child morbidity and treatment of childhood illnesses"},
    7:  {"name": "Chapter 7: Nutrition",                    "description": "Nutritional status of children and women"},
    8:  {"name": "Chapter 8: Malaria",                      "description": "Malaria prevalence and ITN use"},
    9:  {"name": "Chapter 9: HIV/AIDS and STIs",            "description": "HIV/AIDS knowledge, behaviour, and STI prevalence"},
    10: {"name": "Chapter 10: Women's Empowerment",         "description": "Decision-making, employment, and gender-based violence"},
}

# Canonical district names -> normalised display name
DISTRICT_NAMES = {
    'rwamagana': 'Rwamagana', 'nyagatare': 'Nyagatare', 'gatsibo': 'Gatsibo',
    'kayonza': 'Kayonza', 'kirehe': 'Kirehe', 'ngoma': 'Ngoma', 'bugesera': 'Bugesera',
}
PROVINCE_KEYS = {'east province', 'eastern province', 'east', 'eastern'}
NATIONAL_KEYS  = {'rwanda', 'rwanda (national)', 'national'}

# Explicit mapping: json filename (stem, lowercase) → indicator display name
NAME_MAP = {
    # Chap 1
    'chapter1_electricity':           'Electricity Access',
    'chapter1_phone':                 'Mobile Phone Ownership',
    'chapter1_radio':                 'Radio Ownership',
    'chapter1_television':            'Television Ownership',
    'chapter1_computer':              'Computer Ownership',
    'chapter1_handwashing':           'Handwashing Facility Observed',
    # Chap 2
    'eastern_birth_registration':     'Birth Registration',
    'education_females_eastern':      'Education Attainment (Women)',
    'education_males_eastern':        'Education Attainment (Men)',
    'media_exposure_women_eastern':   'Media Exposure (Women)',
    'media_exposure_men_eastern':     'Media Exposure (Men)',
    'eastern_insurance_coverage':     'Health Insurance Coverage',
    'marital_status_women':           'Marital Status (Women)',
    'marital_status_men':             'Marital Status (Men)',
    'eastern_orphanhood_prevalence':  'Orphanhood Prevalence',
    # Chap 3
    'eastern_tfr_corrected_final':    'Total Fertility Rate',
    'eastern_median_birth_interval':  'Median Birth Interval',
    'eastern_median_age_first_birth': 'Median Age at First Birth',
    'eastern_median_age_marriage':    'Median Age at First Marriage',
    'eastern_teenage_pregnancy':      'Teenage Pregnancy and Motherhood',
    # Chap 4
    'eastern_contraception_married_final': 'Contraception Use (Married Women)',
    'eastern_total_demand_planning':       'Total Demand for Family Planning',
    'eastern_fp_media_exposure_women':     'Family Planning Exposure (Women)',
    'eastern_fp_media_exposure_men':       'Family Planning Exposure (Men)',
    # Chap 5
    'eastern_skilled_anc_coverage':        'Antenatal Care Coverage',
    'eastern_skilled_assistance_delivery': 'Skilled Assistance at Delivery',
    'eastern_province_pnc':                'Postnatal Care Coverage',
    'eastern_tetanus_bulletproof':         'Neonatal Tetanus Protection',
    # Chap 6
    'eastern_child_diarrhea_prevalence':   'Prevalence of Diarrhea (Children)',
    'eastern_fever_prevalence':            'Prevalence of Fever (Children)',
    'eastern_ari_prevalence_exact':        'Prevalence of ARI (Children)',
    'eastern_child_anemia_stats':          'Anemia Prevalence (Children)',
    # Chap 7
    'eastern_child_nutrition_final':       'Nutritional Status (Children Under 5)',
    'eastern_women_nutrition_final':       'Nutritional Status (Women 15-49)',
    'eastern_women_anemia_stats':          'Anemia Prevalence (Women)',
    # Chap 8
    'eastern_malaria_prevalence_stats':    'Malaria Prevalence (Children)',
    'eastern_malaria_women_stats':         'Malaria Prevalence (Women)',
    'eastern_child_itn_use_report':        'ITN Use (Children)',
    'eastern_malaria_itn_children_stats':  'ITN Use Among Household Members',
    # Chap 9
    'eastern_hiv_comprehensive_stats':     'Comprehensive HIV Knowledge',
    'eastern_hiv_knowledge_investigated':  'Complete HIV Transmission Knowledge',
    'eastern_multiple_partners_final':     'Multiple Sexual Partners',
    'eastern_men_paid_sex_stats':          'Payment for Sex (Men)',
    'eastern_circumcision_final_stats':    'Practice of Male Circumcision',
    'eastern_sti_prevalence':              'Prevalence of STIs and Symptoms',
    # Chap 10
    'eastern_women_participation_decisions':    'Women Participation in Decision Making',
    'eastern_women_participation_all_none':     'Women Decision Making (All/None)',
    'eastern_men_earnings_decisions_stats':     'Married Men Cash Earnings Decisions',
    'eastern_women_earnings_final_stats':       'Married Women Cash Earnings (Women Report)',
    'eastern_women_earnings_simplified':        'Relative Magnitude of Women Earnings',
    'figure_46_eastern_report':                 'Married Women Cash Earnings (Men Report)',
    'eastern_wife_beating_final':               'Attitude Toward Wife Beating',
}

UNIT_MAP = {
    # Chap 1
    'chapter1_electricity': '%', 'chapter1_phone': '%', 'chapter1_radio': '%',
    'chapter1_television': '%', 'chapter1_computer': '%', 'chapter1_handwashing': '%',
    # default
}

def normalise_location(raw):
    """Return ('district'|'province'|'national', canonical_name)"""
    key = str(raw).strip().lower()
    if key in DISTRICT_NAMES:
        return 'district', DISTRICT_NAMES[key]
    if key in PROVINCE_KEYS:
        return 'province', 'Eastern Province'
    if key in NATIONAL_KEYS:
        return 'national', 'Rwanda'
    return None, raw

def get_or_create_location(raw):
    key = str(raw).strip().lower()
    eastern_prov = Province.objects.get(name='Eastern Province')
    national_prov = Province.objects.get(name='National')

    if key in DISTRICT_NAMES:
        d, _ = District.objects.get_or_create(
            name=DISTRICT_NAMES[key], defaults={'province': eastern_prov})
        return d
    if key in PROVINCE_KEYS:
        d, _ = District.objects.get_or_create(
            name='Eastern Province', defaults={'province': eastern_prov})
        return d
    if key in NATIONAL_KEYS:
        d, _ = District.objects.get_or_create(
            name='Rwanda', defaults={'province': national_prov})
        return d
    return None

def infer_unit(json_data, stem):
    raw_unit = json_data.get('unit', json_data.get('Unit', ''))
    if raw_unit:
        u = str(raw_unit).strip()
        if 'year' in u.lower() or 'age' in u.lower() or u == 'years':
            return 'years'
        return '%'
    return UNIT_MAP.get(stem, '%')

def import_file(json_path, category):
    stem = json_path.stem.lower()
    
    try:
        with open(json_path) as f:
            raw = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"    ⚠️  Skipping {json_path.name}: {e}")
        return 0

    # Determine if data is wrapped with metadata or raw
    if 'data' in raw and isinstance(raw['data'], dict):
        data_dict = raw['data']
        indicator_name = NAME_MAP.get(stem) or raw.get('indicator', stem.replace('_', ' ').title())
        figure_text    = raw.get('figure', raw.get('Figure', ''))
    elif all(isinstance(v, (dict, int, float)) for v in raw.values()):
        # Raw structure: {district: {label: value} or value}
        data_dict = raw
        indicator_name = NAME_MAP.get(stem, stem.replace('_', ' ').title())
        figure_text    = ''
    else:
        print(f"    ⚠️  Unknown structure in {json_path.name}")
        return 0

    unit = infer_unit(raw, stem)

    indicator, _ = Indicator.objects.get_or_create(
        name=indicator_name, category=category, year=YEAR,
        defaults={'unit': unit}
    )

    count = 0
    for location_key, value_data in data_dict.items():
        district = get_or_create_location(location_key)
        if district is None:
            continue

        if isinstance(value_data, dict):
            for label, val in value_data.items():
                if isinstance(val, (int, float)):
                    IndicatorValue.objects.update_or_create(
                        indicator=indicator, district=district,
                        data_label=str(label), year=YEAR,
                        defaults={'value': float(val)}
                    )
                    count += 1
        elif isinstance(value_data, (int, float)):
            IndicatorValue.objects.update_or_create(
                indicator=indicator, district=district,
                data_label='Total', year=YEAR,
                defaults={'value': float(value_data)}
            )
            count += 1

    print(f"    ✅  {indicator_name!r:<55} → {count} values")
    return count

def setup_locations():
    print("📍 Setting up locations...")
    eastern, _ = Province.objects.get_or_create(name='Eastern Province')
    national, _ = Province.objects.get_or_create(name='National')

    for name in ['Rwamagana','Nyagatare','Gatsibo','Kayonza','Kirehe','Ngoma','Bugesera']:
        District.objects.get_or_create(name=name, defaults={'province': eastern})
    District.objects.get_or_create(name='Eastern Province', defaults={'province': eastern})
    District.objects.get_or_create(name='Rwanda', defaults={'province': national})
    print("   ✅ Locations ready\n")

def clear_existing(year=None):
    if year:
        print(f"🗑️  Clearing existing data for year {year}...")
        IndicatorValue.objects.filter(year=year).delete()
        Indicator.objects.filter(year=year).delete()
    else:
        print("🗑️  Clearing ALL existing indicators/values...")
        IndicatorValue.objects.all().delete()
        Indicator.objects.all().delete()
        Category.objects.all().delete()
    print("   ✅ Cleared\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import DHS data into the database.')
    parser.add_argument('--year', type=int, default=2020, help='Survey year to import (default: 2020)')
    parser.add_argument('--clear-all', action='store_true', help='Clear ALL data before import')
    args = parser.parse_args()

    global YEAR
    YEAR = args.year
    print("=" * 65)
    print(f" DHS DATA IMPORTER  –  Year {YEAR}")
    print("=" * 65)

    if args.clear_all:
        clear_existing()
    else:
        clear_existing(year=YEAR)

    setup_locations()

    dhs_dir = BASE_DIR / 'DHS'
    total_values = 0

    # Skip files that are duplicates / superseded by better ones
    SKIP_FILES = {
        'eastern_insurance_final_match',   # superseded by eastern_insurance_coverage
        'eastern_orphanhood_under18',      # superseded by eastern_orphanhood_prevalence
    }

    for chap_num in range(1, 11):
        chap_dir = dhs_dir / f'Chap {chap_num}'
        if not chap_dir.exists():
            continue

        meta = CHAPTERS[chap_num]
        category, _ = Category.objects.get_or_create(
            name=meta['name'], defaults={'description': meta['description']}
        )

        json_files = sorted(chap_dir.glob('*.json'))
        if not json_files:
            print(f"\n⚠️  Chapter {chap_num}: no JSON files found")
            continue

        print(f"{'─'*65}")
        print(f"  CHAPTER {chap_num}: {meta['name']}")
        print(f"{'─'*65}")

        for jf in json_files:
            if jf.stem.lower() in SKIP_FILES:
                print(f"    ↩️  Skipping duplicate: {jf.name}")
                continue
            n = import_file(jf, category)
            total_values += n

    print(f"\n{'='*65}")
    print("  IMPORT SUMMARY")
    print(f"{'='*65}")
    print(f"  Categories : {Category.objects.count()}")
    print(f"  Indicators : {Indicator.objects.count()}")
    print(f"  Districts  : {District.objects.count()}")
    print(f"  Data Points: {IndicatorValue.objects.count()}")
    print(f"\n✅ Done!")

if __name__ == '__main__':
    main()
