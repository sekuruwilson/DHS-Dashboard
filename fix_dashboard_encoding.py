import io
import os

def fix_encoding_and_syntax():
    path = 'd:/my project/templates/indicators/dashboard.html'
    print(f"Fixing file: {path}")
    
    # Read with error handling to avoid charmap crash
    try:
        with io.open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        print("UTF-8 read failed, trying latin-1...")
        with io.open(path, 'r', encoding='latin-1') as f:
            lines = f.readlines()

    # Find and fix the line containing ind.id==focus_indicator.id
    target = 'ind.id==focus_indicator.id'
    fixed = False
    for i, line in enumerate(lines):
        if target in line:
            print(f"Found target at line {i+1}")
            lines[i] = line.replace(target, 'ind == focus_indicator')
            fixed = True
    
    if not fixed:
        print("Target string not found, checking line 213 specifically...")
        # Line 213 is index 212
        if len(lines) > 212:
            lines[212] = '                                <option value="{{ ind.id }}" {% if ind == focus_indicator %}selected{% endif %}>\n'
            fixed = True

    if fixed:
        with io.open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("File updated successfully.")
    else:
        print("Could not find or fix the target line.")

if __name__ == "__main__":
    fix_encoding_and_syntax()
