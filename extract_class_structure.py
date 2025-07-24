#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Extract and display the structure of a Java class file.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from pathlib import Path
import argparse

# Import standard argument parser
try:
    from standard_arg_parser import create_standard_parser as create_parser
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False
    
    def create_parser(tool_type, description):
        return argparse.ArgumentParser(description=description)

# Import preflight checks
try:
    from preflight_checks import run_preflight_checks, PreflightChecker
except ImportError:
    def run_preflight_checks(checks, exit_on_fail=True):
        pass
    class PreflightChecker:
        @staticmethod
        def check_file_readable(path):
            return True, ""
        @staticmethod
        def check_directory_accessible(path):
            return True, ""
        @staticmethod
        def check_ripgrep_installed():
            return True, ""
        @staticmethod
        def check_regex_pattern(pattern):
            return True, ""

def extract_class_structure(file_path, include_fields=False, include_inner_classes=False):
    """Extract the complete structure of a Java class."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract package
    package_match = re.search(r'package\s+([\w.]+);', content)
    package = package_match.group(1) if package_match else "default"
    
    # Extract imports
    imports = re.findall(r'import\s+(?:static\s+)?([\w.*]+);', content)
    
    # Extract main class declaration
    class_pattern = r'((?:@\w+(?:\([^)]*\))?\s*)*)?((?:public|private|protected)\s+)?(?:(abstract|final)\s+)?class\s+(\w+)(?:<[^>]+>)?(?:\s+extends\s+([\w<>,\s]+))?(?:\s+implements\s+([\w<>,\s]+))?'
    class_match = re.search(class_pattern, content, re.MULTILINE | re.DOTALL)
    
    if not class_match:
        return {"error": "Could not find class declaration"}
    
    class_annotations = class_match.group(1) if class_match.group(1) else ""
    class_visibility = class_match.group(2) if class_match.group(2) else "package-private"
    class_modifier = class_match.group(3) if class_match.group(3) else ""
    class_name = class_match.group(4)
    extends_class = class_match.group(5) if class_match.group(5) else None
    implements_interfaces = class_match.group(6) if class_match.group(6) else None
    
    # Extract fields if requested
    fields = []
    if include_fields:
        field_pattern = r'^\s*((?:@\w+(?:\([^)]*\))?\s*)*)?((?:public|private|protected)\s+)?((?:static|final|volatile|transient)\s+)*([\w<>\[\],.\s]+)\s+(\w+)\s*(?:=\s*[^;]+)?;'
        for match in re.finditer(field_pattern, content, re.MULTILINE):
            annotations = match.group(1) if match.group(1) else ""
            visibility = match.group(2).strip() if match.group(2) else "package-private"
            modifiers = match.group(3) if match.group(3) else ""
            field_type = match.group(4).strip()
            field_name = match.group(5)
            
            fields.append({
                'name': field_name,
                'type': field_type,
                'visibility': visibility,
                'modifiers': modifiers.strip(),
                'annotations': annotations.strip()
            })
    
    # Extract methods
    method_pattern = r'^\s*((?:@\w+(?:\([^)]*\))?\s*)*)?((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.\s]+\s+)?)?(\w+)\s*\(([^)]*)\)(?:\s+throws\s+([^{]+))?'
    methods = []
    
    for match in re.finditer(method_pattern, content, re.MULTILINE):
        # Skip if it's inside a comment
        lines_before = content[:match.start()].count('\n')
        
        annotations = match.group(1) if match.group(1) else ""
        visibility = match.group(2).strip() if match.group(2) else "package-private"
        modifiers = match.group(3) if match.group(3) else ""
        return_type = match.group(4).strip() if match.group(4) else "constructor"
        method_name = match.group(5)
        parameters = match.group(6).strip()
        throws_clause = match.group(7).strip() if match.group(7) else ""
        
        # Skip variables and other non-method matches
        if method_name in ['new', 'class', 'interface', 'enum']:
            continue
            
        methods.append({
            'name': method_name,
            'return_type': return_type if return_type != "constructor" else "",
            'visibility': visibility,
            'modifiers': modifiers.strip(),
            'parameters': parameters,
            'throws': throws_clause,
            'annotations': annotations.strip(),
            'line': lines_before + 1
        })
    
    # Extract inner classes if requested
    inner_classes = []
    if include_inner_classes:
        inner_class_pattern = r'((?:public|private|protected|static)\s+)*(?:class|interface|enum)\s+(\w+)'
        # Look for classes after the main class declaration
        main_class_end = class_match.end()
        inner_content = content[main_class_end:]
        
        for match in re.finditer(inner_class_pattern, inner_content):
            modifiers = match.group(1) if match.group(1) else ""
            inner_class_name = match.group(2)
            inner_classes.append({
                'name': inner_class_name,
                'modifiers': modifiers.strip()
            })
    
    return {
        'package': package,
        'imports': imports,
        'class': {
            'name': class_name,
            'visibility': class_visibility.strip(),
            'modifier': class_modifier,
            'extends': extends_class,
            'implements': implements_interfaces.split(',') if implements_interfaces else [],
            'annotations': class_annotations.strip()
        },
        'fields': fields,
        'methods': methods,
        'inner_classes': inner_classes
    }

def print_structure(structure):
    """Print the class structure in a readable format."""
    print("=" * 80)
    print(f"Package: {structure['package']}")
    print("=" * 80)
    
    # Print imports summary
    if structure['imports']:
        print(f"\nImports ({len(structure['imports'])}):")
        # Group imports
        java_imports = [i for i in structure['imports'] if i.startswith('java.')]
        javax_imports = [i for i in structure['imports'] if i.startswith('javax.')]
        other_imports = [i for i in structure['imports'] if not i.startswith(('java.', 'javax.'))]
        
        if java_imports:
            print("  Java standard library:", len(java_imports))
        if javax_imports:
            print("  Java extended library:", len(javax_imports))
        if other_imports:
            print("  Project/third-party:", len(other_imports))
    
    # Print class declaration
    print(f"\nClass Declaration:")
    cls = structure['class']
    class_decl = f"{cls['visibility']} {cls['modifier']} class {cls['name']}".strip()
    if cls['extends']:
        class_decl += f" extends {cls['extends']}"
    if cls['implements']:
        class_decl += f" implements {', '.join(cls['implements'])}"
    print(f"  {class_decl}")
    if cls['annotations']:
        print(f"  Annotations: {cls['annotations']}")
    
    # Print fields if included
    if structure['fields']:
        print(f"\nFields ({len(structure['fields'])}):")
        print("-" * 60)
        print(f"{'Visibility':<12} {'Type':<25} {'Name':<25}")
        print("-" * 60)
        for field in sorted(structure['fields'], key=lambda x: (x['visibility'], x['name'])):
            visibility = field['visibility']
            if field['modifiers']:
                visibility += f" {field['modifiers']}"
            print(f"{visibility:<12} {field['type']:<25} {field['name']:<25}")
    
    # Print methods
    if structure['methods']:
        print(f"\nMethods ({len(structure['methods'])}):")
        print("-" * 80)
        
        # Group methods by visibility
        public_methods = [m for m in structure['methods'] if m['visibility'] == 'public']
        protected_methods = [m for m in structure['methods'] if m['visibility'] == 'protected']
        private_methods = [m for m in structure['methods'] if m['visibility'] == 'private']
        package_methods = [m for m in structure['methods'] if m['visibility'] == 'package-private']
        
        for visibility, methods in [
            ("Public", public_methods),
            ("Protected", protected_methods),
            ("Package-private", package_methods),
            ("Private", private_methods)
        ]:
            if methods:
                print(f"\n{visibility} Methods ({len(methods)}):")
                for method in sorted(methods, key=lambda x: x['name']):
                    method_sig = f"{method['name']}({method['parameters']})"
                    if method['return_type']:
                        method_sig = f"{method['return_type']} {method_sig}"
                    if method['modifiers']:
                        method_sig = f"{method['modifiers']} {method_sig}"
                    print(f"  {method_sig}")
                    if method['throws']:
                        print(f"    throws {method['throws']}")
    
    # Print inner classes if included
    if structure['inner_classes']:
        print(f"\nInner Classes ({len(structure['inner_classes'])}):")
        for inner in structure['inner_classes']:
            print(f"  {inner['modifiers']} {inner['name']}")

    # Print summary
    print(f"\n{'='*80}")
    print("Summary:")
    print(f"  Methods: {len(structure['methods'])}")
    if structure['fields']:
        print(f"  Fields: {len(structure['fields'])}")
    if structure['inner_classes']:
        print(f"  Inner Classes: {len(structure['inner_classes'])}")

def main():
    # Don't use standard parser - needs simple positional argument
    parser = argparse.ArgumentParser(description='Extract Java class structure')
    parser.add_argument('file', help='Java file to analyze')
    parser.add_argument('--include-fields', action='store_true', help='Include field declarations')
    parser.add_argument('--include-inner-classes', action='store_true', help='Include inner classes')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    structure = extract_class_structure(args.file, args.include_fields, args.include_inner_classes)
    
    if 'error' in structure:
        print(f"Error: {structure['error']}")
        sys.exit(1)
    
    print_structure(structure)

if __name__ == "__main__":
    main()