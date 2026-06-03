import requests

def verify_dashboard():
    url = 'http://localhost:8080/'
    print(f"Checking URL: {url}")
    try:
        r = requests.get(url, timeout=10)
        print(f"Status Code: {r.status_code}")
        print("-" * 30)
        print("Page Snippet (first 500 chars):")
        print(r.text[:500])
        print("-" * 30)
        content = r.text
        
        checks = {
            'provinceMap Container': 'id="provinceMap"',
            'mapIndicatorSelect Dropdown': 'id="mapIndicatorSelect"',
            'focus-data-script (JSON)': 'id="focus-data-script"',
            'Leaflet JS Dependency': 'leaflet.js',
            'Leaflet CSS Dependency': 'leaflet.css'
        }
        
        print("\nVerification Results (Should FAIL if successfully removed):")
        print("-" * 30)
        for name, pattern in checks.items():
            found = pattern in content
            status = "[PASS - REMOVED]" if not found else "[FAIL - STILL PRESENT]"
            print(f"{status} {name}")
            
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    verify_dashboard()
