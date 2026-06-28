#!/usr/bin/env python3
"""Fix union type syntax for Python 3.9 compatibility."""

import re
import os
from pathlib import Path
from typing import Set

def fix_file(filepath: Path) -> bool:
    """Fix a single Python file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Check if file has future annotations - if not, add it
    if 'from __future__ import annotations' not in content:
        lines = content.split('\n')
        # Find the first non-docstring, non-comment line
        insert_pos = 0
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
                in_docstring = True
                continue
            if in_docstring and (stripped.endswith('"""') or stripped.endswith("'''")):
                in_docstring = False
                insert_pos = i + 1
                continue
            if in_docstring:
                continue
            if stripped and not stripped.startswith('#'):
                insert_pos = i
                break
        
        lines.insert(insert_pos, 'from __future__ import annotations\n')
        content = '\n'.join(lines)
    
    # Add necessary imports if using Union/Optional
    needs_union = ' | ' in content
    
    if needs_union:
        # Check what's already imported from typing
        has_typing_import = False
        has_union = 'Union' in content
        has_optional = 'Optional' in content
        
        # Add imports line after future import
        lines = content.split('\n')
        
        # Find where to add imports
        import_pos = 0
        for i, line in enumerate(lines):
            if 'from __future__ import' in line:
                import_pos = i + 1
                break
        
        # Check existing typing imports
        import_line = None
        import_end = import_pos
        for i in range(import_pos, len(lines)):
            line = lines[i]
            if 'from typing import' in line:
                import_line = i
                import_end = i
                # Check if it goes to multiple lines
                while i + 1 < len(lines) and (lines[i+1].strip().startswith(',') or 
                                               (not lines[i+1].strip().startswith('from') and 
                                                not lines[i+1].strip().startswith('import') and
                                                lines[i+1].strip() and
                                                not lines[i+1].startswith('def') and
                                                not lines[i+1].startswith('class'))):
                    i += 1
                    import_end = i
                break
            elif line.strip() and not line.startswith('#') and 'import' not in line:
                break
        
        # Now fix the union types
        # Pattern: Type | Type2 | Type3
        # Replace with Union[Type, Type2, Type3]
        
        # First, handle simple X | None patterns -> Optional[X]
        def replace_optional(match):
            type_str = match.group(1).strip()
            return f'Optional[{type_str}]'
        
        # Match Type | None but not Type | None | Type
        content = re.sub(r'(\w+(?:\[.*?\])?)\s*\|\s*None(?!\s*\|)', replace_optional, content)
        content = re.sub(r'None\s*\|\s*(\w+(?:\[.*?\])?)', replace_optional, content)
        
        # Handle remaining union types: Type1 | Type2 | Type3
        def replace_union(match):
            types = [t.strip() for t in match.group(0).split('|')]
            return f'Union[{", ".join(types)}]'
        
        # Match patterns with | but be careful with complex types
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if ' | ' in line and not line.strip().startswith('#'):
                # Avoid replacing in strings
                if '"""' not in line and "'''" not in line:
                    # Check if already has Optional or Union
                    if 'Optional[' not in line and 'Union[' not in line:
                        # Try to fix remaining pipes
                        # Find type annotations (after : and before = or at end of line)
                        line = re.sub(r':\s+([^=\n]+?\|[^=\n]*?)(?:\s*=|\s*\n|,|\))', 
                                     lambda m: f': {replace_union(m)}{m.group(0)[m.start() + len(m.group(1)):]}',
                                     line)
                        lines[i] = line
        
        content = '\n'.join(lines)
        
        # Add Union and Optional to imports
        if import_line is not None:
            existing_line = lines[import_line]
            # Extract what's imported
            match = re.search(r'from typing import (.+)', existing_line)
            if match:
                imports_str = match.group(1).strip()
                if imports_str.endswith('\\'):
                    # Multi-line import
                    imports_str = ' '.join([lines[i].strip() for i in range(import_line, import_end + 1)])
                    imports_str = re.sub(r'from typing import\s*', '', imports_str)
                
                imports = set(i.strip() for i in re.split('[,\\n]', imports_str) if i.strip())
                
                if ' | ' in content:
                    if 'Optional' not in imports:
                        imports.add('Optional')
                    if 'Union' not in imports and 'Union[' in content:
                        imports.add('Union')
                
                imports = sorted(imports)
                new_import = f'from typing import {", ".join(imports)}'
                
                # Replace the import line
                if import_end > import_line:
                    for j in range(import_line, import_end + 1):
                        del lines[import_line]
                    lines.insert(import_line, new_import)
                else:
                    lines[import_line] = new_import
                
                content = '\n'.join(lines)
        elif needs_union:
            # No existing typing import, add one
            imports = []
            if 'Optional[' in content:
                imports.append('Optional')
            if 'Union[' in content:
                imports.append('Union')
            
            if imports:
                import_line = 'from typing import ' + ', '.join(sorted(imports))
                lines.insert(import_pos, import_line)
                content = '\n'.join(lines)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False


def main():
    """Fix all Python files in the src directory."""
    src_dir = Path('SignalProcessingToolkit/src')
    
    fixed_files: Set[str] = set()
    
    for py_file in src_dir.rglob('*.py'):
        try:
            if fix_file(py_file):
                fixed_files.add(str(py_file))
                print(f"✓ Fixed: {py_file}")
            else:
                print(f"  OK: {py_file}")
        except Exception as e:
            print(f"✗ Error in {py_file}: {e}")
    
    print(f"\nTotal files fixed: {len(fixed_files)}")


if __name__ == '__main__':
    main()
