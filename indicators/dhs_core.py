import pandas as pd
import numpy as np
import pyreadstat
import os
import tempfile

# ==========================================
# CONSTANTS & CONFIG
# ==========================================

REQUIRED_VARS = {
    "v005", "hv005", "mv005", "v012", "mv012", "v024", "hv024", "mv024", "v023", "hv023", "mv023",
    "shdistrict", "sdistrict", "sdist", "sdstr", "hv015", "hv206", "hv201", "hv205", 
    "hv213", "hv244", "hv247", "hv103", "hv104", "hv105", "hv106", "mv106", "v155", "mv155", 
    "v157", "v158", "v159", "mv157", "mv158", "mv159", "v481", "hv140", "hc1", "v201", "v213", 
    "v212", "v502", "v313", "v626", "v624", "v384a", "v384b", "v384c", "v384d", "v008", 
    "b3_01", "b3_1", "m3a_1", "m3b_1", "m3c_1", "m14_1", "m15_1", "m17_1", "m51_1", "m71_1", "b5", "b19", 
    "h22", "h11", "h31", "h31b", "h31c", "h1", "h2", "h3", "h4", "h5", "h6", "h7", 
    "h8", "h9", "hc70", "hc71", "hc72", "v457", "hc57", "hml12", "hml1", "hml32", 
    "hml35", "v763a", "v763b", "v763c", "mv763a", "mv763b", "mv763c", "v781", "v751", 
    "v744a", "v744b", "v744c", "v744d", "v744e", "v743a", "v743b", "v743d", "v746", "v731", 
    "hv243a", "hv207", "hv208", "hv243e", "hv230a", "hv230b", "v501", "mv501", "hv111", "hv113", 
    "hv102", "v743f", "b11", "v445", "hml10", "sm301", "sm213", "smdistrict",
    "m1_1", "m1a_1", "m1b_1", "m62_1", "m70_1", "m72_1", "m51_1", "m50_1", "m71_1", "m15_1", "m3a_1", "m3b_1", "m3c_1", "m3d_1", "m3e_1", "m3f_1", "m3g_1", "m3h_1", "m3i_1", "m3j_1", "m3k_1", "m3l_1", "m3m_1", "m3n_1", "b3_1", "m63_1", "m66_1", "m67_1", "m74_1", "m75_1",
    "m1_01", "m1a_01", "m1b_01", "m62_01", "m70_01", "m72_01", "m51_01", "m50_01", "m71_01", "m15_01", "m3a_01", "m3b_01", "m3c_01", "m3d_01", "m3e_01", "m3f_01", "m3g_01", "m3h_01", "m3i_01", "m3j_01", "m3k_01", "m3l_01", "m3m_01", "m3n_01", "b3_01", "m63_01", "m66_01", "m67_01", "m74_01", "m75_01",
    "m1$01", "m1a$01", "m1b$01", "m62$01", "m70$01", "m72$01", "m51$01", "m50$01", "m71$01", "m15$01", "m3a$01", "m3b$01", "m3c$01", "m3d$01", "m3e$01", "m3f$01", "m3g$01", "m3h$01", "m3i$01", "m3j$01", "m3k$01", "m3l$01", "m3m$01", "m3n$01", "b3$01", "m63$01", "m66$01", "m67$01", "m74$01", "m75$01",
    "hc56", "v754cp", "v754dp", "v756", "v754jp", "v754wp",
    "v190", "v106", "hv270", "mv384a", "mv384b", "mv384c", "mv384d",
    "b3_02", "b3_2", "b3$02",
    "mv481", "hv209", "hv210", "hv211", "hv212", "v511",
    "mv766b", "mv793", "mg102", "mv483",
    "v739",
    "m2a", "m2a1", "m2a01", "m2a_1", "m2a_01", "m2a$01",
    "m2b", "m2b1", "m2b01", "m2b_1", "m2b_01", "m2b$01",
    "m2c", "m2c1", "m2c01", "m2c_1", "m2c_01", "m2c$01"
}

DISTRICT_MAP = {
    11: "Nyarugenge", 12: "Gasabo", 13: "Kicukiro",
    21: "Nyanza", 22: "Gisagara", 23: "Nyaruguru", 24: "Huye", 25: "Ruhango", 26: "Nyamagabe", 27: "Kamonyi", 28: "Muhanga",
    31: "Karongi", 32: "Rutsiro", 33: "Rubavu", 34: "Nyabihu", 35: "Ngororero", 36: "Rusizi", 37: "Nyamasheke",
    41: "Rulindo", 42: "Gakenke", 43: "Musanze", 44: "Burera", 45: "Gicumbi",
    51: "Rwamagana", 52: "Nyagatare", 53: "Gatsibo", 54: "Kayonza", 55: "Kirehe", 56: "Ngoma", 57: "Bugesera"
}

PROVINCE_MAP = {
    1: "Kigali City", 2: "South", 3: "West", 4: "North", 5: "East"
}

# ==========================================
# DATA LOADING
# ==========================================
def load_data(uploaded_file, version=1):
    """
    Loads a Stata file (.dta), filtering for required columns to save memory.
    """
    try:
        if isinstance(uploaded_file, str):
            tmp_path = uploaded_file
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dta") as tmp:
                if hasattr(uploaded_file, 'read'):
                    tmp.write(uploaded_file.read())
                elif hasattr(uploaded_file, 'getbuffer'):
                    tmp.write(uploaded_file.getbuffer())
                else:
                    tmp.write(uploaded_file)
                tmp_path = tmp.name
        
        # Read metadata first to filter columns
        _, meta = pyreadstat.read_dta(tmp_path, metadataonly=True)
        cols_to_load = [c for c in meta.column_names if c.lower() in REQUIRED_VARS]
        
        if not cols_to_load:
            if not isinstance(uploaded_file, str):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            return pd.DataFrame()
        
        df, _ = pyreadstat.read_dta(tmp_path, usecols=cols_to_load)
        df.columns = df.columns.str.lower()
        
        if not isinstance(uploaded_file, str):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def get_dhs_col(df, base):
    """Finds a column in a DHS DataFrame checking common suffixes (_1, _01, $01, etc.)."""
    for s in ['_1', '_01', '$01', '1', '01', '']:
        col = f"{base}{s}"
        if col in df.columns: return col
    return None

def standard_round(n):
    """Standard definition of rounding (0.5 rounds up)."""
    return int(np.floor(n + 0.5))

def get_weighted_pct(df, target_col, weight_col='w'):
    """
    Calculates the weighted percentage of 'target_col' being True/1.
    Returns integer percentage after standard rounding.
    """
    if df.empty or weight_col not in df.columns or df[weight_col].sum() == 0:
        return 0.0
    
    valid = df[[target_col, weight_col]].dropna()
    if valid.empty:
        return 0.0
        
    val = np.average(valid[target_col], weights=valid[weight_col]) * 100
    return standard_round(val)

def get_weighted_mean(df, target_col, weight_col='w'):
    """
    Calculates the weighted mean of 'target_col' (for non-binary values like children ever born).
    Returns the weighted average without multiplying by 100.
    """
    if df.empty or weight_col not in df.columns or df[weight_col].sum() == 0:
        return 0.0
    
    valid = df[[target_col, weight_col]].dropna()
    if valid.empty:
        return 0.0
    
    val = np.average(valid[target_col], weights=valid[weight_col])
    return round(val, 2)

def prep_common_vars(df, weight_col_name=None):
    """
    Standardizes weights (divides by 1,000,000) and finds the district column.
    """
    df.columns = df.columns.str.lower()
    
    weight_candidates = [weight_col_name] if weight_col_name else ['v005', 'hv005', 'mv005']
    w_col = next((c for c in weight_candidates if c in df.columns), None)
    
    if w_col:
        df['w'] = df[w_col].astype(float) / 1000000.0
    else:
        df['w'] = 1.0 # Fallback unweighted
        
    dist_candidates = ['shdistrict', 'sdistrict', 'sdist', 'sdstr', 'hv023', 'v023', 'mv023']
    dist_col = next((c for c in dist_candidates if c in df.columns), None)
    
    return df, dist_col

def aggregate_by_location(df, indicator_col, dist_col, group_by=None):
    """
    Aggregates a boolean indicator (0/1) by National, Province, and District.
    """
    results = []
    
    def add_result(subset, location, type_, parent="Rubavu"):
        if subset.empty: return
        
        if group_by and group_by in subset.columns:
            grp = subset.groupby(group_by)
            for cat, sub in grp:
                val = get_weighted_pct(sub, indicator_col)
                results.append({
                    "Location": location, 
                    "Value": val, 
                    "Type": type_, 
                    "Parent": parent,
                    "Category": str(cat)
                })
        else:
            val = get_weighted_pct(subset, indicator_col)
            results.append({"Location": location, "Value": val, "Type": type_, "Parent": parent})

    reg_col = next((c for c in ['hv024', 'v024', 'mv024'] if c in df.columns), None)
    
    if reg_col and dist_col:
        for code, name in DISTRICT_MAP.items():
            sub = df[df[dist_col] == code]
            prov_code = int(str(code)[0]) 
            parent = PROVINCE_MAP.get(prov_code, "Unknown")
            add_result(sub, name, "District", parent)
            
        for code, name in PROVINCE_MAP.items():
            sub = df[df[reg_col] == code]
            add_result(sub, name, "Province", "Rwanda")
        
    add_result(df, "Rwanda", "National", "World")
    
    return pd.DataFrame(results)

def aggregate_by_location_for_means(df, indicator_col, dist_col, group_by=None):
    """
    Aggregates a continuous/numeric variable by National, Province, and District.
    """
    results = []
    
    def add_result(subset, location, type_, parent="Rubavu"):
        if subset.empty: return
        
        if group_by and group_by in subset.columns:
            grp = subset.groupby(group_by)
            for cat, sub in grp:
                val = get_weighted_mean(sub, indicator_col)
                results.append({
                    "Location": location, 
                    "Value": val, 
                    "Type": type_, 
                    "Parent": parent,
                    "Category": str(cat)
                })
        else:
            val = get_weighted_mean(subset, indicator_col)
            results.append({"Location": location, "Value": val, "Type": type_, "Parent": parent})

    reg_col = next((c for c in ['hv024', 'v024', 'mv024'] if c in df.columns), None)
    
    if reg_col and dist_col:
        for code, name in DISTRICT_MAP.items():
            sub = df[df[dist_col] == code]
            prov_code = int(str(code)[0])
            parent = PROVINCE_MAP.get(prov_code, "Unknown")
            add_result(sub, name, "District", parent)
            
        for code, name in PROVINCE_MAP.items():
            sub = df[df[reg_col] == code]
            add_result(sub, name, "Province", "Rwanda")
    
    add_result(df, "Rwanda", "National", "World")
    
    return pd.DataFrame(results)

def aggregate_distribution_by_location(df, indicator_col, dist_col, category_map=None, group_by=None):
    """
    Aggregates a categorical variable by location and optionally demographic group.
    """
    reg_col = next((c for c in ['hv024', 'v024'] if c in df.columns), None)
    results = []

    def get_dist_subset(subset, label, type_, parent="Rubavu"):
        if subset.empty or subset['w'].sum() == 0:
            return
        
        groups = [indicator_col]
        if group_by and group_by in subset.columns:
            groups.append(group_by)
            
        counts = subset.groupby(groups)['w'].sum()
        
        if group_by and group_by in subset.columns:
            totals = subset.groupby(group_by)['w'].sum()
            for (cat, grp_val), count in counts.items():
                total = totals.get(grp_val, 0)
                if total == 0: continue
                val = (count / total) * 100
                cat_name = category_map.get(cat, str(cat)) if category_map else str(cat)
                results.append({
                    "Location": label, 
                    "Category": cat_name, 
                    "Value": standard_round(val), 
                    "Type": type_,
                    "Parent": parent,
                    "Group": str(grp_val)
                })
        else:
            total_w = subset['w'].sum()
            pcts = (counts / total_w) * 100
            for cat, val in pcts.items():
                cat_name = category_map.get(cat, str(cat)) if category_map else str(cat)
                results.append({
                    "Location": label, 
                    "Category": cat_name, 
                    "Value": standard_round(val), 
                    "Type": type_,
                    "Parent": parent
                })

    if reg_col and dist_col:
        for code, name in DISTRICT_MAP.items():
            prov_code = int(str(code)[0]) 
            parent = PROVINCE_MAP.get(prov_code, "Unknown")
            get_dist_subset(df[df[dist_col] == code], name, "District", parent)
            
        for code, name in PROVINCE_MAP.items():
            get_dist_subset(df[df[reg_col] == code], name, "Province", "Rwanda")

    get_dist_subset(df, "Rwanda", "National", "World")

    return pd.DataFrame(results)
