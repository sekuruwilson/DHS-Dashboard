import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rdhs_viz.settings')
django.setup()

from indicators.models import Indicator, IndicatorValue, District, Category

def verify_json_logic():
    # User provided examples
    json_data_1 = {
        "indicator": "Test Birth Reg",
        "unit": "Percentage (%)",
        "data": {
            "Rwamagana": 85,
            "Nyagatare": 73
        }
    }
    
    json_data_2 = {
        "indicator": "Test Marital Status",
        "unit": "Percentage (%)",
        "data": {
            "Rwamagana": {
                "Never in union": 48,
                "Married": 27
            }
        }
    }
    
    # Mock category
    category, _ = Category.objects.get_or_create(name="Test Category")
    
    # Mock Districts (Ensure they exist for test)
    # Assuming Province exists, if not need to create
    from indicators.models import Province
    prov, _ = Province.objects.get_or_create(name="Test Province")
    District.objects.get_or_create(name="Rwamagana", province=prov)
    District.objects.get_or_create(name="Nyagatare", province=prov)
    
    datasets = [json_data_1, json_data_2]
    
    print("--- Starting JSON Logic Verification ---")
    
    for item in datasets:
        indicator_name = item.get('indicator')
        print(f"Processing: {indicator_name}")
        
        indicator, _ = Indicator.objects.get_or_create(
            name=indicator_name, category=category,
            defaults={'unit': item.get('unit')}
        )
        
        indicator_data = item.get('data', {})
        processed_count = 0
        
        for dist_name, dist_val in indicator_data.items():
            district = District.objects.filter(name=dist_name).first()
            if not district:
                print(f"  [WARN] District not found: {dist_name}")
                continue
            
            if isinstance(dist_val, dict):
                for label, val in dist_val.items():
                    IndicatorValue.objects.update_or_create(
                        indicator=indicator, district=district, data_label=label,
                        defaults={'value': val}
                    )
                    processed_count += 1
            else:
                IndicatorValue.objects.update_or_create(
                    indicator=indicator, district=district, data_label="Total",
                    defaults={'value': dist_val}
                )
                processed_count += 1
                
        print(f"  -> Saved {processed_count} values.")
        
    # Verify DB
    cnt1 = IndicatorValue.objects.filter(indicator__name="Test Birth Reg").count()
    cnt2 = IndicatorValue.objects.filter(indicator__name="Test Marital Status").count()
    print("--- Verification Results ---")
    print(f"Test Birth Reg count: {cnt1} (Expected 2)")
    print(f"Test Marital Status count: {cnt2} (Expected 2)")
    
    if cnt1 == 2 and cnt2 == 2:
        print("SUCCESS: Logic handles both formats correctly.")
    else:
        print("FAILURE: Logic did not save expected counts.")

if __name__ == "__main__":
    verify_json_logic()
