import random

def generate_insights(indicator, values):
    """
    Generates data-driven insights for a given indicator based on its values.
    """
    if not values:
        return ["No data available to generate insights."]

    # Extract raw values for calculations
    raw_values = [v.value for v in values]
    avg_val = sum(raw_values) / len(raw_values)
    max_val = max(raw_values)
    min_val = min(raw_values)
    
    max_districts = [v.district.name for v in values if v.value == max_val]
    min_districts = [v.district.name for v in values if v.value == min_val]
    
    insights = []
    
    # 1. General Summary
    insights.append(f"The average for <strong>{indicator.name}</strong> across all districts is <strong>{avg_val:.1f}%</strong>.")
    
    # 2. Performance Extremes
    insights.append(f"<strong>{', '.join(max_districts)}</strong> shows the highest performance at <strong>{max_val:.1f}%</strong>.")
    insights.append(f"Conversely, <strong>{', '.join(min_districts)}</strong> has the lowest recorded value of <strong>{min_val:.1f}%</strong>.")
    
    # 3. Variability Insight
    spread = max_val - min_val
    if spread > 30:
        insights.append(f"There is a significant disparity (<strong>{spread:.1f}%</strong>) between the highest and lowest performing districts, suggesting targeted interventions may be needed.")
    elif spread < 10:
        insights.append(f"Performance is relatively uniform across districts, with a narrow spread of only <strong>{spread:.1f}%</strong>.")
    
    # 4. Contextual "AI" Tips (Simulated Logic)
    tips = [
        "Consistent monitoring of these figures is recommended to track long-term health trends.",
        "Cross-referencing this data with population density could yield deeper insights.",
        "Consider historical RDHS data to determine if this represents an improvement over previous years.",
        "Infrastructure and accessibility often correlate with these results; investigate local resource allocation."
    ]
    insights.append(random.choice(tips))
    
    return insights
