from .models import Indicator, IndicatorValue, District, Province
from django.db.models import Avg

# Names that are NOT actual districts (provinces + country) — excluded from district-level charts
def _non_district_names():
    province_names = list(Province.objects.values_list('name', flat=True))
    return province_names + ['Rwanda']

def get_ranking_data(indicator_pk, label='Total', district_names=None, year=None):
    """
    Returns a ranked list of districts for a specific indicator and label.
    Optionally filters by a list of district names.
    """
    indicator = Indicator.objects.get(pk=indicator_pk)
    
    if year is None:
        latest_val = IndicatorValue.objects.filter(indicator=indicator).order_by('-year').first()
        year = latest_val.year if latest_val else 2022
        
    excluded = _non_district_names()
    query_set = IndicatorValue.objects.filter(indicator=indicator, data_label=label, year=year).exclude(district__name__in=excluded).select_related('district')
    
    if district_names:
        query_set = query_set.filter(district__name__in=district_names)
        
    values = query_set.order_by('-value')
    
    if not values.exists() and label == 'Total':
        # Feedback: if 'Total' doesn't exist, try the first available label
        available_labels = IndicatorValue.objects.filter(indicator=indicator, year=year).values_list('data_label', flat=True).distinct()
        if available_labels.exists():
            label = available_labels.first()
            query_set = IndicatorValue.objects.filter(indicator=indicator, data_label=label, year=year).exclude(district__name__in=excluded).select_related('district')
            if district_names:
                query_set = query_set.filter(district__name__in=district_names)
            values = query_set.order_by('-value')

    ranking_list = []
    for v in values:
        ranking_list.append({
            'district': v.district.name,
            'value': v.value,
        })
    
    avg_val = values.aggregate(Avg('value'))['value__avg'] or 0
    
    # Generate Insight
    hit_count = len(ranking_list)
    insight = ""
    if hit_count > 0:
        top = ranking_list[0]
        bottom = ranking_list[-1]
        insight = f"<strong>{top['district']}</strong> is the top-performing district for <strong>{indicator.name} ({label}) in {year}</strong> with a value of <strong>{top['value']}{indicator.unit}</strong>. This is <strong>{round(top['value'] - avg_val, 1)}{indicator.unit}</strong> above the national average."
        if hit_count > 5:
            insight += f" Conversely, <strong>{bottom['district']}</strong> has the lowest value at <strong>{bottom['value']}{indicator.unit}</strong>."

    return {
        'indicator': indicator,
        'label': label,
        'data': ranking_list,
        'average': round(avg_val, 2),
        'insight': insight,
        'year': year
    }

def get_gap_analysis_data(indicator_pk, district_names=None, year=None):
    """
    Analyzes the 'Gap' (difference) between labels like 'Urban' and 'Rural' across districts.
    Optionally filters by a list of district names.
    """
    indicator = Indicator.objects.get(pk=indicator_pk)
    
    if year is None:
        latest_val = IndicatorValue.objects.filter(indicator=indicator).order_by('-year').first()
        year = latest_val.year if latest_val else 2022
        
    labels = list(IndicatorValue.objects.filter(indicator=indicator, year=year).values_list('data_label', flat=True).distinct())
    
    # Try to identify pairs for gap analysis (e.g., Urban vs Rural)
    target_pairs = [('Urban', 'Rural'), ('Male', 'Female'), ('Highest', 'Lowest')]
    active_pair = None
    
    for p1, p2 in target_pairs:
        if p1 in labels and p2 in labels:
            active_pair = (p1, p2)
            break
            
    if not active_pair and len(labels) >= 2:
        # Avoid using 'Total' in gap analysis if there are other segments
        non_total_labels = [l for l in labels if l.lower() != 'total']
        if len(non_total_labels) >= 2:
            active_pair = (non_total_labels[0], non_total_labels[1])
        else:
            active_pair = (labels[0], labels[1])
        
    if not active_pair:
        return {'error': 'Insufficient segments for gap analysis.'}

    if district_names:
        districts = District.objects.filter(name__in=district_names)
    else:
        excluded = _non_district_names()
        districts = District.objects.exclude(name__in=excluded)
    
    gap_data = []
    
    for dist in districts:
        v1 = IndicatorValue.objects.filter(indicator=indicator, district=dist, data_label=active_pair[0], year=year).first()
        v2 = IndicatorValue.objects.filter(indicator=indicator, district=dist, data_label=active_pair[1], year=year).first()
        
        if v1 and v2:
            gap = abs(v1.value - v2.value)
            gap_data.append({
                'district': dist.name,
                'val1': v1.value,
                'val2': v2.value,
                'gap': round(gap, 2)
            })
            
    # Sort by gap size
    gap_data.sort(key=lambda x: x['gap'], reverse=True)
    
    insight = ""
    if gap_data:
        max_gap = gap_data[0]
        insight = f"The largest disparity between <strong>{active_pair[0]}</strong> and <strong>{active_pair[1]}</strong> for <strong>{indicator.name} in {year}</strong> is found in <strong>{max_gap['district']}</strong>, with a gap of <strong>{max_gap['gap']}{indicator.unit}</strong>."

    return {
        'indicator': indicator,
        'labels': active_pair,
        'data': gap_data,
        'insight': insight,
        'year': year
    }

def get_correlation_data(ind1_pk, ind2_pk, year=None):
    """
    Returns paired data for two indicators across all districts for correlation analysis.
    """
    ind1 = Indicator.objects.get(pk=ind1_pk)
    ind2 = Indicator.objects.get(pk=ind2_pk)
    
    if year is None:
        latest_val = IndicatorValue.objects.filter(indicator=ind1).order_by('-year').first()
        year = latest_val.year if latest_val else 2022
        
    # We use 'Total' label for correlation by default
    excluded = _non_district_names()
    v1_qs = IndicatorValue.objects.filter(indicator=ind1, data_label='Total', year=year).exclude(district__name__in=excluded).select_related('district')
    v2_qs = IndicatorValue.objects.filter(indicator=ind2, data_label='Total', year=year).exclude(district__name__in=excluded).select_related('district')
    
    v2_map = {v.district.id: v.value for v in v2_qs}
    
    paired_data = []
    x_vals = []
    y_vals = []
    
    for v1 in v1_qs:
        if v1.district.id in v2_map:
            y_val = v2_map[v1.district.id]
            paired_data.append({
                'district': v1.district.name,
                'x': v1.value,
                'y': y_val
            })
            x_vals.append(v1.value)
            y_vals.append(y_val)
            
    # Simple correlation calculation (Pearson)
    correlation = 0
    if len(x_vals) > 1:
        try:
            import numpy as np
            correlation = np.corrcoef(x_vals, y_vals)[0,1]
        except ImportError:
            # Fallback to manual calculation if numpy is not available
            n = len(x_vals)
            sum_x = sum(x_vals)
            sum_y = sum(y_vals)
            sum_x_sq = sum(x**2 for x in x_vals)
            sum_y_sq = sum(y**2 for y in y_vals)
            sum_xy = sum(x*y for x, y in zip(x_vals, y_vals))
            
            numerator = (n * sum_xy) - (sum_x * sum_y)
            denominator = ((n * sum_x_sq - sum_x**2) * (n * sum_y_sq - sum_y**2))**0.5
            correlation = numerator / denominator if denominator != 0 else 0

    strength = "No"
    abs_corr = abs(correlation)
    if abs_corr > 0.7: strength = "Strong"
    elif abs_corr > 0.4: strength = "Moderate"
    elif abs_corr > 0.1: strength = "Weak"
    
    direction = "positive" if correlation > 0 else "negative"
    insight = f"There is a <strong>{strength} {direction} correlation</strong> ({round(correlation, 2)}) between <strong>{ind1.name}</strong> and <strong>{ind2.name} in {year}</strong> across the districts."

    return {
        'ind1': ind1,
        'ind2': ind2,
        'data': paired_data,
        'correlation': round(correlation, 2),
        'insight': insight,
        'year': year
    }
