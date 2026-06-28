#!/usr/bin/env python3
"""Fix union type syntax for Python 3.9 compatibility - simpler approach."""

import re
from pathlib import Path


def fix_file_simple(filepath):
    """Fix a single Python file using simple text replacement."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    lines = content.split('\n')
    
    # Step 1: Add future import if not present
    has_future = any('from __future__ import annotations' in line for line in lines)
    
    if not has_future:
        # Find insertion point (after docstrings and before other imports)
        insert_idx = 0
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
            elif not in_docstring and stripped and not stripped.startswith('#'):
                insert_idx = i
                break
        
        lines.insert(insert_idx, 'from __future__ import annotations\n')
        content = '\n'.join(lines)
    
    # Step 2: Replace union types
    # Handle Optional[X] cases first - X | None -> Optional[X]
    content = re.sub(r'(\w+(?:\[[\w\[\], ]*\])?)\s*\|\s*None\b', r'Optional[\1]', content)
    content = re.sub(r'None\s*\|\s*(\w+(?:\[[\w\[\], ]*\])?)', r'Optional[\1]', content)
    
    # Step 3: Add Optional import
    if 'Optional[' in content:
        content = add_import(content, 'Optional')
    
    if 'Union[' in content:
        content = add_import(content, 'Union')
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False


def add_import(content, import_name):
    """Add import to typing imports or create new import line."""
    lines = content.split('\n')
    
    # Find typing import
    typing_import_idx = None
    for i, line in enumerate(lines):
        if re.match(r'from typing import', line):
            typing_import_idx = i
            break
    
    if typing_import_idx is not None:
        # Add to existing typing import
        line = lines[typing_import_idx]
        if import_name not in line:
            # Extract imports
            match = re.search(r'from typing import (.+)$', line)
            if match:
                imports_str = match.group(1).strip()
                # Remove trailing backslash if present
                imports_str = imports_str.rstrip('\\').strip()
                imports = [i.strip() for i in imports_str.split(',')]
                if import_name not in imports:
                    imports.append(import_name)
                    imports.sort()
                    lines[typing_import_idx] = f'from typing import {", ".join(imports)}'
    else:
        # Create new typing import after future import
        future_idx = None
        for i, line in enumerate(lines):
            if 'from __future__ import' in line:
                future_idx = i
                break
        
        if future_idx is not None:
            insert_idx = future_idx + 1
            # Skip blank lines
            while insert_idx < len(lines) and lines[insert_idx].strip() == '':
                insert_idx += 1
            lines.insert(insert_idx, f'from typing import {import_name}')
        else:
            lines.insert(0, f'from typing import {import_name}')
    
    return '\n'.join(lines)


def main():
    """Fix all Python files."""
    src_dir = Path('src')
    
    if not src_dir.exists():
        print(f"Error: {src_dir} not found")
        return
    
    fixed_count = 0
    for py_file in sorted(src_dir.rglob('*.py')):
        if fix_file_simple(py_file):
            print(f"✓ Fixed: {py_file}")
            fixed_count += 1
        else:
            print(f"  Skipped: {py_file}")
    
    print(f"\nTotal files fixed: {fixed_count}")


if __name__ == '__main__':
    main()
