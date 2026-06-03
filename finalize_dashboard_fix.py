import io
import os

def finalize_dashboard():
    path = 'd:/my project/templates/indicators/dashboard.html'
    backup = path + '.debug_bak'
    
    if not os.path.exists(backup):
        print("Backup not found, cannot restore.")
        return

    print(f"Restoring and fixing: {path}")
    
    with io.open(backup, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 1. Fix line 213 (ind.id==focus_indicator.id)
    target_if = '{% if ind.id==focus_indicator.id %}'
    replacement_if = '{% if ind == focus_indicator %}'
    content = content.replace(target_if, replacement_if)
    
    # 2. Fix json_script (line 250)
    target_json = '{% json_script focus_data "focus-data-script" %}'
    replacement_json = '<script id="focus-data-script" type="application/json">{{ focus_data_json|safe }}</script>'
    content = content.replace(target_json, replacement_json)
    
    # Also handle the old version in case it's there
    target_json_old = '{{ focus_data|json_script:"focus-data-script" }}'
    content = content.replace(target_json_old, replacement_json)

    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Dashboard restored and fixed successfully.")

if __name__ == "__main__":
    finalize_dashboard()
