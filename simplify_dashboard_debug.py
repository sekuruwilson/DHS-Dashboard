import io
import os

def simplify_dashboard():
    path = 'd:/my project/templates/indicators/dashboard.html'
    backup = path + '.debug_bak'
    
    # Backup
    if not os.path.exists(backup):
        with io.open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        with io.open(backup, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Backup created.")
    
    # Simplify
    simple_content = """{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <h1>Hello Debug</h1>
    <p>If you see this, the view logic is working fine.</p>
</div>
{% endblock %}"""
    
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(simple_content)
    print("Dashboard simplified.")

if __name__ == "__main__":
    simplify_dashboard()
