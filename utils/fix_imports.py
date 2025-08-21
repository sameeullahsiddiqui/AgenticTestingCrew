import os
import re
from pathlib import Path

def fix_relative_imports(directory):
    """Fix relative imports in Python files"""
    backend_dir = Path(directory)
    
    for py_file in backend_dir.glob("*.py"):
        print(f"Processing {py_file.name}...")
        
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace relative imports with absolute imports
        # Pattern: from .module import something
        content = re.sub(r'from \.(\w+)', r'from \1', content)
        
        # Pattern: from . import something  
        content = re.sub(r'from \. import', 'import', content)
        
        # Write back the fixed content
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed imports in {py_file.name}")

if __name__ == "__main__":
    fix_relative_imports("backend")
    print("✅ All relative imports have been fixed!")