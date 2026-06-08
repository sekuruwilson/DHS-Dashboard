import pandas as pd
import numpy as np
from .dhs_core import (
    prep_common_vars, 
    aggregate_by_location, 
    aggregate_distribution_by_location, 
    get_dhs_col, 
    get_weighted_mean, 
    aggregate_by_location_for_means
)

# ==============================================================================
# CHAPTER 1: HOUSEHOLD CHARACTERISTICS
# ==============================================================================
def calc_electricity(datasets, group_by=None):
    """1.1 Electricity coverage"""
    df = datasets['HR'].copy(); df, d = prep_common_vars(df, 'hv005')
    df['val'] = (df['hv206'] == 1).astype(int)
    return aggregate_by_location(df, 'val', d, group_by)

def calc_durable_goods(datasets, group_by=None):
    """1.2 Household durable goods (Consolidated Chart)"""
    df = datasets['HR'].copy(); df, d = prep_common_vars(df, 'hv005')
    
    goods = {
        'Radio': 'hv207',
        'Television': 'hv208',
        'Mobile Phone': 'hv243a',
        'Computer': 'hv243e',
        'Refrigerator': 'hv209',
        'Bicycle': 'hv210',
        'Motorcycle': 'hv211',
        'Car/Truck': 'hv212'
    }
    
    results = []
    for label, col in goods.items():
        if col in df.columns:
            df['val'] = (df[col] == 1).astype(int)
            res = aggregate_by_location(df, 'val', d, group_by)
            res['Category'] = label
            results.append(res)
            
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

def calc_handwashing_place(datasets, group_by=None):
    """1.3 Hand washing place observed"""
    df = datasets['HR'].copy(); df, d = prep_common_vars(df, 'hv005')
    if 'hv230a' not in df.columns: return pd.DataFrame()
    
    df = df[df['hv230a'].isin([1, 2, 3])]
    mapping = {1: "Fixed place", 2: "Mobile place", 3: "No specific place"}
    return aggregate_distribution_by_location(df, 'hv230a', d, mapping, group_by)

# ==============================================================================
# CHAPTER 2: RESPONDENT CHARACTERISTICS
# ==============================================================================
def calc_education_women(datasets, group_by=None):
    """2.1 Education attainment (Women 6+)"""
    df = datasets['PR'].copy(); df, d = prep_common_vars(df, 'hv005')
    df = df[(df['hv104'] == 2) & (df['hv105'] >= 6)] 
    mapping = {0: "No education", 1: "Primary", 2: "Secondary", 3: "Higher"}
    return aggregate_distribution_by_location(df, 'hv106', d, mapping, group_by)

def calc_education_men(datasets, group_by=None):
    """2.1 Education attainment (Men 6+)"""
    df = datasets['PR'].copy(); df, d = prep_common_vars(df, 'hv005')
    df = df[(df['hv104'] == 1) & (df['hv105'] >= 6)]
    mapping = {0: "No education", 1: "Primary", 2: "Secondary", 3: "Higher"}
    return aggregate_distribution_by_location(df, 'hv106', d, mapping, group_by)

def calc_birth_registration(datasets, group_by=None):
    """2.2 Birth registration of children under age 5"""
    df = datasets['PR'].copy(); df, d = prep_common_vars(df, 'hv005')
    df = df[df['hv105'] < 5]
    df['val'] = df['hv140'].isin([1, 2]).astype(int)
    return aggregate_by_location(df, 'val', d, group_by)

def calc_orphanhood(datasets, group_by=None):
    """2.3 Children's orphanhood (One or both parents dead, <18)"""
    df = datasets['PR'].copy(); df, d = prep_common_vars(df, 'hv005')
    df = df[df['hv105'] < 18]
    df['val'] = ((df['hv111'] == 0) | (df['hv113'] == 0)).astype(int)
    return aggregate_by_location(df, 'val', d, group_by)

def calc_health_insurance(datasets, group_by=None):
    """2.4 Health insurance coverage (Women & Men combined)"""
    results = []
    
    # Women (IR)
    df_ir = datasets['IR'].copy(); df_ir, d_ir = prep_common_vars(df_ir, 'v005')
    df_ir['val'] = (df_ir['v481'] == 1).astype(int)
    res_w = aggregate_by_location(df_ir, 'val', d_ir, group_by)
    res_w['Category'] = "Women"
    results.append(res_w)
    
    # Men (MR)
    if 'MR' in datasets:
        df_mr = datasets['MR'].copy(); df_mr, d_mr = prep_common_vars(df_mr, 'mv005')
        if 'mv481' in df_mr.columns:
            df_mr['val'] = (df_mr['mv481'] == 1).astype(int)
            res_m = aggregate_by_location(df_mr, 'val', d_mr, group_by)
            res_m['Category'] = "Men"
            results.append(res_m)
            
    return pd.concat(results, ignore_index=True)

def calc_media_exposure(datasets, group_by=None):
    """2.5 Exposure to mass media (Radio/TV/Paper at least once a week)"""
    results = []
    
    # Women
    df_w = datasets['IR'].copy(); df_w, d_w = prep_common_vars(df_w, 'v005')
    for lbl, col in {'Radio':'v159', 'TV':'v158', 'Newspaper':'v157'}.items():
        if col in df_w.columns:
            df_w['val'] = (df_w[col] >= 2).astype(int)
            res = aggregate_by_location(df_w, 'val', d_w, group_by)
            res['Category'] = f"{lbl} (Women)"
            results.append(res)

    # Men
    if 'MR' in datasets:
        df_m = datasets['MR'].copy(); df_m, d_m = prep_common_vars(df_m, 'mv005')
        for lbl, col in {'Radio':'mv159', 'TV':'mv158', 'Newspaper':'mv157'}.items():
            if col in df_m.columns:
                df_m['val'] = (df_m[col] >= 2).astype(int)
                res = aggregate_by_location(df_m, 'val', d_m, group_by)
                res['Category'] = f"{lbl} (Men)"
                results.append(res)
                
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

def calc_marital_status(datasets, group_by=None):
    """2.6 Current marital status (Women)"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    mapping = {0: "Never in union", 1: "Married", 2: "Living with partner", 3: "Widowed", 4: "Divorced", 5: "Separated"}
    return aggregate_distribution_by_location(df, 'v501', d, mapping, group_by)

# ==============================================================================
# CHAPTER 3: FERTILITY
# ==============================================================================
def _get_interpolated_median_age(sub, age_col, weight_col='w'):
    if sub.empty or sub[weight_col].sum() == 0:
        return np.nan
    
    freq = sub.groupby(age_col)[weight_col].sum().sort_index()
    total_wt = freq.sum()
    if total_wt == 0:
        return np.nan
        
    props = freq / total_wt
    cum_props = props.cumsum()
    
    try:
        median_bin = cum_props[cum_props >= 0.5].index[0]
        if median_bin >= 90:
            return np.nan
        idx_loc = cum_props.index.get_loc(median_bin)
        prop_prev = cum_props.iloc[idx_loc - 1] if idx_loc > 0 else 0.0
        prop_curr = props.loc[median_bin]
        if prop_curr == 0:
            return np.nan
        median_val = median_bin + ((0.5 - prop_prev) / prop_curr)
        return round(median_val, 2)
    except (IndexError, KeyError):
        return np.nan

def calc_median_age_marriage(datasets, group_by=None):
    """3.1 Median age at first marriage (Women 25-49)"""
    from .dhs_core import DISTRICT_MAP, PROVINCE_MAP
    
    df = datasets['IR'].copy(); df, dist_col = prep_common_vars(df, 'v005')
    
    if 'w' not in df.columns:
        df['w'] = df['v005'].astype(float) / 1000000.0
    
    df = df[df['v012'].between(25, 49)]
    if 'v511' not in df.columns or not dist_col: return pd.DataFrame()
    
    df['final_age'] = df['v511'].copy()
    df.loc[df['v501'] == 0, 'final_age'] = 99
    
    results = []
    reg_col = next((c for c in ['hv024', 'v024'] if c in df.columns), None)
    
    for code, name in DISTRICT_MAP.items():
        sub = df[df[dist_col] == code].copy()
        median_val = _get_interpolated_median_age(sub, 'final_age')
        prov_code = int(str(code)[0])
        parent = PROVINCE_MAP.get(prov_code, "Unknown")
        results.append({"Location": name, "Value": median_val, "Type": "District", "Parent": parent})
    
    if reg_col:
        for code, name in PROVINCE_MAP.items():
            sub = df[df[reg_col] == code].copy()
            median_val = _get_interpolated_median_age(sub, 'final_age')
            results.append({"Location": name, "Value": median_val, "Type": "Province", "Parent": "Rwanda"})
            
    nat_median = _get_interpolated_median_age(df, 'final_age')
    results.append({"Location": "Rwanda", "Value": nat_median, "Type": "National", "Parent": ""})
    
    return pd.DataFrame(results)

def calc_median_age_birth(datasets, group_by=None):
    """3.3 Median age at first birth (Women 25-49)"""
    from .dhs_core import DISTRICT_MAP, PROVINCE_MAP
    
    df = datasets['IR'].copy(); df, dist_col = prep_common_vars(df, 'v005')
    
    if 'w' not in df.columns:
        df['w'] = df['v005'].astype(float) / 1000000.0
    
    df = df[df['v012'].between(25, 49)]
    if 'v212' not in df.columns or not dist_col: return pd.DataFrame()
    
    df['final_age'] = df['v212'].copy()
    df.loc[(df['v201'] == 0) | (df['v212'].isna()) | (df['v212'] >= 90), 'final_age'] = 99
    
    results = []
    reg_col = next((c for c in ['hv024', 'v024'] if c in df.columns), None)
    
    for code, name in DISTRICT_MAP.items():
        sub = df[df[dist_col] == code].copy()
        median_val = _get_interpolated_median_age(sub, 'final_age')
        prov_code = int(str(code)[0])
        parent = PROVINCE_MAP.get(prov_code, "Unknown")
        results.append({"Location": name, "Value": median_val, "Type": "District", "Parent": parent})
        
    if reg_col:
        for code, name in PROVINCE_MAP.items():
            sub = df[df[reg_col] == code].copy()
            median_val = _get_interpolated_median_age(sub, 'final_age')
            results.append({"Location": name, "Value": median_val, "Type": "Province", "Parent": "Rwanda"})
            
    nat_median = _get_interpolated_median_age(df, 'final_age')
    results.append({"Location": "Rwanda", "Value": nat_median, "Type": "National", "Parent": ""})
    
    return pd.DataFrame(results)

def calc_birth_interval(datasets, group_by=None):
    """3.2 Median Birth Interval (Months)"""
    from .dhs_core import DISTRICT_MAP, PROVINCE_MAP
    
    df = datasets['IR'].copy()
    df, dist_col = prep_common_vars(df, 'v005')
    
    if 'w' not in df.columns:
        df['w'] = df['v005'].astype(float) / 1000000.0
    
    b3_cols = [f'b3_{i:02d}' for i in range(1, 21)] + [f'b3_{i}' for i in range(1, 21)]
    b11_cols = [f'b11_{i:02d}' for i in range(1, 21)] + [f'b11_{i}' for i in range(1, 21)]
    
    b3_cols = [c for c in b3_cols if c in df.columns]
    b11_cols = [c for c in b11_cols if c in df.columns]
    
    if not b3_cols or not b11_cols or 'v008' not in df.columns:
        return pd.DataFrame()
    
    df['row_id'] = df.index
    
    try:
        df_long = pd.wide_to_long(
            df, stubnames=["b3", "b11"], i="row_id", j="birth_idx", 
            sep="_", suffix='\\d+'
        ).reset_index()
    except:
        return pd.DataFrame()
    
    df_long = df_long.dropna(subset=["b3"])
    
    if 'v008' in df_long.columns:
        df_long['months_ago'] = df_long['v008'] - df_long['b3']
        df_long = df_long[df_long['months_ago'] < 60]
    
    df_long = df_long.dropna(subset=["b11"])
    df_long = df_long[df_long['b11'] < 90]
    
    if df_long.empty:
        return pd.DataFrame()
    
    results = []
    reg_col = next((c for c in ['v024', 'hv024', 'mv024'] if c in df.columns), None)
    
    def get_interpolated_median(subset, val_col, wt_col):
        if subset.empty or subset[wt_col].sum() == 0:
            return np.nan
        
        data = subset[[val_col, wt_col]].dropna()
        if data.empty:
            return np.nan
        
        freq = data.groupby(val_col)[wt_col].sum().sort_index()
        if freq.empty:
            return np.nan
        
        total_wt = freq.sum()
        props = freq / total_wt
        cum_props = props.cumsum()
        
        try:
            median_bin = cum_props[cum_props >= 0.5].index[0]
            idx_loc = cum_props.index.get_loc(median_bin)
            prop_prev = cum_props.iloc[idx_loc - 1] if idx_loc > 0 else 0.0
            prop_curr = props.loc[median_bin]
            median_val = median_bin + ((0.5 - prop_prev) / prop_curr)
            return round(median_val, 1)
        except (IndexError, KeyError):
            return np.nan
    
    if dist_col:
        for code, name in DISTRICT_MAP.items():
            sub = df_long[df_long[dist_col] == code]
            median_val = get_interpolated_median(sub, 'b11', 'w')
            prov_code = int(str(code)[0])
            parent = PROVINCE_MAP.get(prov_code, "Unknown")
            results.append({"Location": name, "Value": median_val, "Type": "District", "Parent": parent})
    
    if reg_col:
        for code, name in PROVINCE_MAP.items():
            sub = df_long[df_long[reg_col] == code]
            median_val = get_interpolated_median(sub, 'b11', 'w')
            results.append({"Location": name, "Value": median_val, "Type": "Province", "Parent": "Rwanda"})
    
    nat_median = get_interpolated_median(df_long, 'b11', 'w')
    results.append({"Location": "Rwanda", "Value": nat_median, "Type": "National", "Parent": ""})
    
    return pd.DataFrame(results)

def calc_teenage_pregnancy(datasets, group_by=None):
    """3.4 Teenage pregnancy and motherhood (15-19)"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    df = df[df['v012'].between(15, 19)]
    df['val'] = ((df['v201'] > 0) | (df['v213'] == 1)).astype(int)
    return aggregate_by_location(df, 'val', d, group_by)

def calc_fertility_rate_proxy(datasets, group_by=None):
    """3.5 Mean Children Ever Born and TFR proxy"""
    from .dhs_core import DISTRICT_MAP, PROVINCE_MAP
    
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    results = []
    
    df_ceb = df[df['v012'].between(40, 49)].copy()
    df_ceb['val'] = df_ceb['v201']
    res_ceb = aggregate_by_location_for_means(df_ceb, 'val', d, group_by)
    res_ceb['Category'] = "Mean Children Ever Born (40-49)"
    results.append(res_ceb)
    
    bh_cols = [f'b3_{i:02d}' for i in range(1, 21)] + [f'b3_{i}' for i in range(1, 21)]
    existing_bh_cols = [c for c in bh_cols if c in df.columns]
    reg_col = next((c for c in ['hv024', 'v024'] if c in df.columns), None)
    
    if existing_bh_cols and 'v008' in df.columns:
        df_fert = df[df['v012'].between(15, 49)].copy()
        
        if 'w' not in df_fert.columns:
            df_fert['w'] = df_fert['v005'].astype(float) / 1000000.0
            
        df_fert['age_group'] = pd.cut(df_fert['v012'], bins=[14, 19, 24, 29, 34, 39, 44, 49], 
                                      labels=['15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49'])
        
        births_cols = []
        for col in existing_bh_cols:
            if col in df_fert.columns:
                birth_dates = pd.to_numeric(df_fert[col], errors='coerce')
                in_3yr = ((birth_dates >= (df_fert['v008'] - 35)) & (birth_dates <= df_fert['v008'])).astype(int)
                df_fert[col + '_in_3yr'] = in_3yr * df_fert['w']
                births_cols.append(col + '_in_3yr')
                
        df_fert['births_in_3yr'] = df_fert[births_cols].sum(axis=1)
        tfr_rows = []
        
        def compute_tfr(sub, location, type_val, parent_val):
            if sub.empty or sub['w'].sum() == 0:
                return None, None
            
            asfr_sum = 0.0
            for age_group in ['15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49']:
                sub_age = sub[sub['age_group'] == age_group]
                women_w = sub_age['w'].sum()
                if women_w > 0:
                    births_w = sub_age['births_in_3yr'].sum()
                    asfr = births_w / (women_w * 3)
                    asfr_sum += asfr
            
            tfr_val = round(asfr_sum * 5, 2)
            
            has_ideal = 'v613' in sub.columns
            if has_ideal:
                sub_copy = sub.copy()
                sub_copy['ideal_num'] = pd.to_numeric(sub_copy['v613'], errors='coerce')
                sub_copy['ceb'] = pd.to_numeric(sub_copy['v201'], errors='coerce').fillna(0)
                valid = sub_copy.dropna(subset=['ideal_num'])
                if not valid.empty and valid['w'].sum() > 0:
                    reached_ideal = np.average((valid['ceb'] <= valid['ideal_num']).astype(float), weights=valid['w'])
                    wanted_tfr_val = round(tfr_val * reached_ideal, 2)
                else:
                    wanted_tfr_val = round(tfr_val * 0.8, 2)
            else:
                wanted_tfr_val = round(tfr_val * 0.8, 2)
                
            return tfr_val, wanted_tfr_val
            
        if d:
            for code, name in DISTRICT_MAP.items():
                sub = df_fert[df_fert[d] == code]
                prov_code = int(str(code)[0])
                parent = PROVINCE_MAP.get(prov_code, "Unknown")
                obs, wnt = compute_tfr(sub, name, "District", parent)
                if obs is not None:
                    tfr_rows.append({"Location": name, "Value": obs, "Type": "District", "Parent": parent, "Category": "Observed TFR (15-49)"})
                    tfr_rows.append({"Location": name, "Value": wnt, "Type": "District", "Parent": parent, "Category": "Wanted TFR (15-49)"})
                    
        if reg_col:
            for code, name in PROVINCE_MAP.items():
                sub = df_fert[df_fert[reg_col] == code]
                obs, wnt = compute_tfr(sub, name, "Province", "Rwanda")
                if obs is not None:
                    tfr_rows.append({"Location": name, "Value": obs, "Type": "Province", "Parent": "Rwanda", "Category": "Observed TFR (15-49)"})
                    tfr_rows.append({"Location": name, "Value": wnt, "Type": "Province", "Parent": "Rwanda", "Category": "Wanted TFR (15-49)"})
                    
        obs, wnt = compute_tfr(df_fert, "Rwanda", "National", "World")
        if obs is not None:
            tfr_rows.append({"Location": "Rwanda", "Value": obs, "Type": "National", "Parent": "World", "Category": "Observed TFR (15-49)"})
            tfr_rows.append({"Location": "Rwanda", "Value": wnt, "Type": "National", "Parent": "World", "Category": "Wanted TFR (15-49)"})
            
        if tfr_rows:
            results.append(pd.DataFrame(tfr_rows))
            
    if results:
        return pd.concat(results, ignore_index=True)
    return pd.DataFrame()

# ==============================================================================
# CHAPTER 4: FAMILY PLANNING
# ==============================================================================
def calc_contraception(datasets, group_by=None):
    """4.1 Current use of contraception"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    df = df[df['v502'] == 1]
    
    results = []
    df['val'] = (df['v313'] >= 1).astype(int)
    res_any = aggregate_by_location(df, 'val', d, group_by)
    res_any['Category'] = "Any Method"
    
    df['val'] = (df['v313'] == 3).astype(int)
    res_mod = aggregate_by_location(df, 'val', d, group_by)
    res_mod['Category'] = "Modern Method"
    
    return pd.concat([res_any, res_mod], ignore_index=True)

def calc_fp_demand(datasets, group_by=None):
    """4.2 Demand for family planning (Met + Unmet)"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    df = df[df['v502'] == 1] 
    df['val'] = (df['v626'].isin([1, 2, 3, 4])).astype(int)
    return aggregate_by_location(df, 'val', d, group_by)

def calc_fp_messages(datasets, group_by=None):
    """4.3 Exposure to family planning messages"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    results = []
    for lbl, col in {'Radio':'v384a', 'TV':'v384b', 'Paper':'v384c', 'Mobile':'v384d'}.items():
        if col in df.columns:
            df['val'] = (df[col] == 1).astype(int)
            res = aggregate_by_location(df, 'val', d, group_by)
            res['Category'] = lbl
            results.append(res)
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

# ==============================================================================
# CHAPTER 5: MATERNAL HEALTH
# ==============================================================================
def calc_anc_care(datasets, group_by=None):
    """5.1 Antenatal care (Skilled Provider)"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    b3 = get_dhs_col(df, 'b3')
    if b3: df = df[(df['v008'] - df[b3]) < 60]
    
    vars = [get_dhs_col(df, c) for c in ['m2a', 'm2b', 'm2c']]
    vars = [v for v in vars if v is not None]
    if not vars: return pd.DataFrame()
    
    df['val'] = df[vars].max(axis=1).apply(lambda x: 1 if x == 1 else 0)
    return aggregate_by_location(df, 'val', d, group_by)

def calc_tetanus(datasets, group_by=None):
    """5.2 Mothers protected against neonatal tetanus"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    m1 = get_dhs_col(df, 'm1')
    if m1 in df.columns:
        df['val'] = (df[m1] >= 2).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_delivery_place(datasets, group_by=None):
    """5.3 Place of delivery (Health Facility)"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    m15 = get_dhs_col(df, 'm15')
    if m15:
        df['val'] = df[m15].between(20, 39).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_delivery_assist(datasets, group_by=None):
    """5.4 Assistance during delivery (Skilled)"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    vars = [get_dhs_col(df, c) for c in ['m3a', 'm3b', 'm3c']]
    vars = [v for v in vars if v is not None]
    if vars:
        df['val'] = df[vars].max(axis=1).apply(lambda x: 1 if x == 1 else 0)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_pnc_checkup(datasets, group_by=None):
    """5.5 Postnatal checkups (Mother within 2 days)"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    
    b3 = get_dhs_col(df, 'b3')
    if b3:
        df = df[(df['v008'] - df[b3]) < 60]
        
    m62 = get_dhs_col(df, 'm62')
    m63 = get_dhs_col(df, 'm63')
    m66 = get_dhs_col(df, 'm66')
    m67 = get_dhs_col(df, 'm67')
    
    in_facility_pnc = False
    if m62 and m63:
        in_facility_pnc = (df[m62] == 1) & (df[m63].between(100, 147) | df[m63].between(200, 202))
        
    out_facility_pnc = False
    if m66 and m67:
        out_facility_pnc = (df[m66] == 1) & (df[m67].between(100, 147) | df[m67].between(200, 202))
        
    df['val'] = (in_facility_pnc | out_facility_pnc).astype(int)
    return aggregate_by_location(df, 'val', d, group_by)

# ==============================================================================
# CHAPTER 6: CHILD HEALTH
# ==============================================================================
def calc_child_health_indicators(datasets, group_by=None):
    """6.1-6.3 Prevalence of ARI, Fever, Diarrhea"""
    df = datasets['KR'].copy(); df, d = prep_common_vars(df, 'v005')
    df = df[df['b19'] < 60]
    
    results = []
    if 'h31b' in df.columns:
        df['val'] = (df['h31b'] == 1).astype(int)
        res = aggregate_by_location(df, 'val', d, group_by)
        res['Category'] = "ARI"
        results.append(res)
    
    if 'h22' in df.columns:
        df['val'] = (df['h22'] == 1).astype(int)
        res = aggregate_by_location(df, 'val', d, group_by)
        res['Category'] = "Fever"
        results.append(res)
        
    if 'h11' in df.columns:
        df['val'] = (df['h11'] == 1).astype(int)
        res = aggregate_by_location(df, 'val', d, group_by)
        res['Category'] = "Diarrhea"
        results.append(res)
        
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

def calc_child_anemia(datasets, group_by=None):
    """6.4 Anemia among children (Hb < 11.0)"""
    df = datasets['PR'].copy(); df, d = prep_common_vars(df, 'hv005')
    df = df[df['hc1'].between(6, 59)]
    if 'hc56' in df.columns:
        df['val'] = (df['hc56'] < 110).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

# ==============================================================================
# CHAPTER 7: NUTRITION
# ==============================================================================
def calc_nutrition_children(datasets, group_by=None):
    """7.1 Nutritional status of children"""
    df = datasets['PR'].copy(); df, d = prep_common_vars(df, 'hv005')
    df = df[df['hc1'] < 60]
    
    results = []
    df['val'] = (df['hc70'] < -200).astype(int)
    res1 = aggregate_by_location(df, 'val', d, group_by)
    res1['Category'] = "Stunting (Height-for-Age)"
    results.append(res1)
    
    df['val'] = (df['hc72'] < -200).astype(int)
    res2 = aggregate_by_location(df, 'val', d, group_by)
    res2['Category'] = "Wasting (Weight-for-Height)"
    results.append(res2)
    
    if 'hc71' in df.columns:
        df['val'] = (df['hc71'] < -200).astype(int)
        res3 = aggregate_by_location(df, 'val', d, group_by)
        res3['Category'] = "Underweight (Weight-for-Age)"
        results.append(res3)
        
    return pd.concat(results, ignore_index=True)

def calc_nutrition_women(datasets, group_by=None):
    """7.2 Nutritional status among women (BMI)"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    df = df[df['v213'] == 0]
    df = df[df['v445'] < 6000]
    
    def bmi_cat(x):
        if x < 1850: return "Thin"
        if 1850 <= x < 2500: return "Normal"
        return "Overweight"
        
    df['cols'] = df['v445'].apply(bmi_cat)
    return aggregate_distribution_by_location(df, 'cols', d, None, group_by)

def calc_anemia_women(datasets, group_by=None):
    """7.3 Prevalence of anemia among women"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    df['val'] = df['v457'].isin([1, 2, 3]).astype(int)
    return aggregate_by_location(df, 'val', d, group_by)

# ==============================================================================
# CHAPTER 8: MALARIA
# ==============================================================================
def calc_itn_use_total(datasets, group_by=None):
    """8.1 Use of ITNs (Household Population)"""
    df = datasets['PR'].copy(); df, d = prep_common_vars(df, 'hv005')
    df['val'] = (df['hml12'] == 1).astype(int)
    return aggregate_by_location(df, 'val', d, group_by)

def calc_itn_use_children(datasets, group_by=None):
    """8.2 Use of ITNs among children <5"""
    df = datasets['PR'].copy(); df, d = prep_common_vars(df, 'hv005')
    df = df[df['hc1'] < 60]
    df['val'] = (df['hml12'] == 1).astype(int)
    return aggregate_by_location(df, 'val', d, group_by)

def calc_malaria_prevalence(datasets, group_by=None):
    """8.3 & 8.4 Prevalence of Malaria"""
    df = datasets['PR'].copy(); df, d = prep_common_vars(df, 'hv005')
    if 'hml32' not in df.columns: return pd.DataFrame()
    
    results = []
    ch = df[df['hc1'].between(6, 59)].copy()
    ch = ch[ch['hml32'].isin([0, 1])]
    ch['val'] = (ch['hml32'] == 1).astype(int)
    res_ch = aggregate_by_location(ch, 'val', d, group_by)
    res_ch['Category'] = "Children 6-59m"
    results.append(res_ch)
    
    wm = df[(df['hv104'] == 2) & (df['hv105'].between(15, 49))].copy()
    wm = wm[wm['hml32'].isin([0, 1])]
    wm['val'] = (wm['hml32'] == 1).astype(int)
    res_wm = aggregate_by_location(wm, 'val', d, group_by)
    res_wm['Category'] = "Women 15-49"
    results.append(res_wm)
    
    return pd.concat(results, ignore_index=True)

# ==============================================================================
# CHAPTER 9: HIV ATTITUDE AND KNOWLEDGE
# ==============================================================================
def calc_hiv_knowledge_prevent(datasets, group_by=None):
    """9.1 Complete knowledge of HIV prevention methods"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    if 'v754cp' in df.columns and 'v754dp' in df.columns:
        df['val'] = ((df['v754cp'] == 1) & (df['v754dp'] == 1)).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_hiv_knowledge_comprehensive(datasets, group_by=None):
    """9.2 Comprehensive knowledge about HIV transmission"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    req = ['v754cp', 'v754dp', 'v754jp', 'v754wp', 'v756']
    if all(c in df.columns for c in req):
        df['val'] = ((df['v754cp'] == 1) & (df['v754dp'] == 1) & 
                     (df['v754jp'] == 0) & (df['v754wp'] == 0) & 
                     (df['v756'] == 1)).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_multiple_partners(datasets, group_by=None):
    """9.3 Multiple sexual partners (Men)"""
    if 'MR' not in datasets: return pd.DataFrame()
    df = datasets['MR'].copy(); df, d = prep_common_vars(df, 'mv005')
    if 'mv766b' in df.columns:
        df = df[df['mv766b'] < 99]
        df['val'] = (df['mv766b'] >= 2).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_paid_sex(datasets, group_by=None):
    """9.4 Payment for sex (Men, last 12m)"""
    if 'MR' not in datasets: return pd.DataFrame()
    df = datasets['MR'].copy(); df, d = prep_common_vars(df, 'mv005')
    if 'mv793' in df.columns:
        df['val'] = (df['mv793'] == 1).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_sti_prevalence(datasets, group_by=None):
    """9.5 Self-reported STI/Symptoms (Women)"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    vars = [c for c in ['v763a', 'v763b', 'v763c'] if c in df.columns]
    if vars:
        df['val'] = df[vars].max(axis=1).apply(lambda x: 1 if x==1 else 0)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_circumcision(datasets, group_by=None):
    """9.6 Practice of Circumcision (Men)"""
    if 'MR' not in datasets: return pd.DataFrame()
    df = datasets['MR'].copy(); df, d = prep_common_vars(df, 'mv005')
    col = 'mg102' if 'mg102' in df.columns else 'mv483'
    if col in df.columns:
        df['val'] = (df[col] == 1).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

# ==============================================================================
# CHAPTER 10: WOMEN EMPOWERMENT
# ==============================================================================
def calc_women_earnings(datasets, group_by=None):
    """10.1 Control over women's cash earnings"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    if 'v731' not in df.columns: return pd.DataFrame()
    df = df[df['v731'].isin([1, 2, 3])]
    if 'v739' in df.columns:
        df['val'] = (df['v739'].isin([1, 2])).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_men_earnings_control(datasets, group_by=None):
    """10.2 Control over men's cash earnings"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    df = df[df['v502'] == 1]
    if 'v743f' in df.columns:
        df['val'] = (df['v743f'].isin([1, 2])).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_decision_making(datasets, group_by=None):
    """10.3 Women's participation in decision-making"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    df = df[df['v502'] == 1]
    if all(c in df.columns for c in ['v743a', 'v743b', 'v743d']):
        df['val'] = ((df['v743a'].isin([1,2])) & 
                     (df['v743b'].isin([1,2])) & 
                     (df['v743d'].isin([1,2]))).astype(int)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

def calc_wife_beating(datasets, group_by=None):
    """10.4 Attitude toward wife beating"""
    df = datasets['IR'].copy(); df, d = prep_common_vars(df, 'v005')
    vars = [c for c in ['v744a','v744b','v744c','v744d','v744e'] if c in df.columns]
    if vars:
        df['val'] = df[vars].max(axis=1).apply(lambda x: 1 if x == 1 else 0)
        return aggregate_by_location(df, 'val', d, group_by)
    return pd.DataFrame()

# ==============================================================================
# INDICATOR REGISTRY
# ==============================================================================
INDICATORS = {
    "Chapter 1: Household characteristics": {
        "1.1 Electricity coverage": {"fn": calc_electricity, "req": ["HR"]},
        "1.2 Household durable goods": {"fn": calc_durable_goods, "req": ["HR"]},
        "1.3 Hand washing place": {"fn": calc_handwashing_place, "req": ["HR"]},
    },
    "Chapter 2: Respondent characteristics": {
        "2.1 Education (Women)": {"fn": calc_education_women, "req": ["PR"]},
        "2.1 Education (Men)": {"fn": calc_education_men, "req": ["PR"]},
        "2.2 Birth Registration": {"fn": calc_birth_registration, "req": ["PR"]},
        "2.3 Orphanhood": {"fn": calc_orphanhood, "req": ["PR"]},
        "2.4 Health Insurance": {"fn": calc_health_insurance, "req": ["IR", "MR"]},
        "2.5 Media Exposure": {"fn": calc_media_exposure, "req": ["IR", "MR"]},
        "2.6 Marital Status (Women)": {"fn": calc_marital_status, "req": ["IR"]},
    },
    "Chapter 3: Fertility determinants and fertility rates": {
        "3.1 Median Age at First Marriage": {"fn": calc_median_age_marriage, "req": ["IR"]},
        "3.2 Birth Interval": {"fn": calc_birth_interval, "req": ["IR"]},
        "3.3 Median Age at First Birth": {"fn": calc_median_age_birth, "req": ["IR"]},
        "3.4 Teenage Pregnancy": {"fn": calc_teenage_pregnancy, "req": ["IR"]},
        "3.5 Fertility (Mean Children Ever Born)": {"fn": calc_fertility_rate_proxy, "req": ["IR"]},
    },
    "Chapter 4: Family planning": {
        "4.1 Current Contraception": {"fn": calc_contraception, "req": ["IR"]},
        "4.2 Demand for FP": {"fn": calc_fp_demand, "req": ["IR"]},
        "4.3 Exposure to Messages": {"fn": calc_fp_messages, "req": ["IR"]},
    },
    "Chapter 5: Maternal health": {
        "5.1 Antenatal Care (Skilled)": {"fn": calc_anc_care, "req": ["IR"]},
        "5.2 Tetanus Protection": {"fn": calc_tetanus, "req": ["IR"]},
        "5.3 Place of Delivery": {"fn": calc_delivery_place, "req": ["IR"]},
        "5.4 Assistance at Delivery": {"fn": calc_delivery_assist, "req": ["IR"]},
        "5.5 Postnatal Checkups": {"fn": calc_pnc_checkup, "req": ["IR"]},
    },
    "Chapter 6: Child health": {
        "6.1-6.3 Illness Prevalence (ARI/Fever/Diarrhea)": {"fn": calc_child_health_indicators, "req": ["KR"]},
        "6.4 Anemia (Children)": {"fn": calc_child_anemia, "req": ["PR"]},
    },
    "Chapter 7: Nutrition among children and women": {
        "7.1 Child Nutrition Status": {"fn": calc_nutrition_children, "req": ["PR"]},
        "7.2 Women's BMI": {"fn": calc_nutrition_women, "req": ["IR"]},
        "7.3 Women's Anemia": {"fn": calc_anemia_women, "req": ["IR"]},
    },
    "Chapter 8: Malaria": {
        "8.1 ITN Use (Total HH Pop)": {"fn": calc_itn_use_total, "req": ["PR"]},
        "8.2 ITN Use (Children)": {"fn": calc_itn_use_children, "req": ["PR"]},
        "8.3/8.4 Malaria Prevalence": {"fn": calc_malaria_prevalence, "req": ["PR"]},
    },
    "Chapter 9: HIV Attitude and Knowledge": {
        "9.1 HIV Knowledge (Prevention)": {"fn": calc_hiv_knowledge_prevent, "req": ["IR"]},
        "9.2 HIV Knowledge (Comprehensive)": {"fn": calc_hiv_knowledge_comprehensive, "req": ["IR"]},
        "9.3 Multiple Partners (Men)": {"fn": calc_multiple_partners, "req": ["MR"]},
        "9.4 Paid Sex (Men)": {"fn": calc_paid_sex, "req": ["MR"]},
        "9.5 STI Prevalence (Women)": {"fn": calc_sti_prevalence, "req": ["IR"]},
        "9.6 Circumcision (Men)": {"fn": calc_circumcision, "req": ["MR"]},
    },
    "Chapter 10: Women empowerment": {
        "10.1 Control Women's Earnings": {"fn": calc_women_earnings, "req": ["IR"]},
        "10.2 Control Men's Earnings": {"fn": calc_men_earnings_control, "req": ["IR"]},
        "10.3 Decision Making": {"fn": calc_decision_making, "req": ["IR"]},
        "10.4 Wife Beating Justified": {"fn": calc_wife_beating, "req": ["IR"]},
    }
}
