#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Analyze dependencies between Java files and classes using ripgrep.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from pathlib import Path
import subprocess
from collections import defaultdict
import shutil
import json
from preflight_checks import run_preflight_checks

# Import standard argument parser
try:
    from standard_arg_parser import create_standard_parser as create_parser
    HAS_STANDARD_PARSER = True
except ImportError:
    import argparse
    HAS_STANDARD_PARSER = False
    
    def create_parser(tool_type, description):
        return argparse.ArgumentParser(description=description)

# Import configuration support with fallback
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass

try:
    import javalang
    HAS_JAVALANG = True
except ImportError:
    HAS_JAVALANG = False

def check_ripgrep():
    """Check if ripgrep is installed."""
    try:
        from dependency_checker import check_ripgrep as check_rg
        check_rg()
    except ImportError:
        # Fallback if dependency_checker not available
        if not shutil.which('rg'):
            print("Error: ripgrep (rg) is not installed.", file=sys.stderr)
            print("Install it from: https://github.com/BurntSushi/ripgrep#installation", file=sys.stderr)
            sys.exit(1)

def extract_class_name(file_path):
    """Extract the main class name from a Java file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if HAS_JAVALANG:
        try:
            tree = javalang.parse.parse(content)
            for path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    return node.name
        except Exception:
            # Fall through to regex method
            pass

    return Path(file_path).stem

def find_dependencies(file_path, depth=2):
    """Find what classes/files this file depends on."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    dependencies = {
        'imports': set(),
        'class_uses': set(),
        'extends': set(),
        'implements': set(),
        'annotations': set()
    }

    if HAS_JAVALANG:
        try:
            tree = javalang.parse.parse(content)
        except Exception:
            # Fallback to regex if parsing fails
            return find_dependencies_regex(content)
    else:
        # No javalang available, use regex
        return find_dependencies_regex(content)

    for imp in tree.imports:
        if not imp.wildcard:
            dependencies['imports'].add(imp.path.split('.')[-1])

    for path, node in tree:
        if isinstance(node, javalang.tree.ClassDeclaration):
            if node.extends:
                dependencies['extends'].add(node.extends.name)
            if node.implements:
                for impl in node.implements:
                    dependencies['implements'].add(impl.name)
        if isinstance(node, javalang.tree.Annotation):
            dependencies['annotations'].add(node.name)
        if isinstance(node, javalang.tree.ClassCreator):
            dependencies['class_uses'].add(node.type.name)
        if isinstance(node, javalang.tree.MemberReference) and node.qualifier:
            # Only add if qualifier looks like a class name (starts with uppercase)
            if isinstance(node.qualifier, str) and node.qualifier and node.qualifier[0].isupper():
                dependencies['class_uses'].add(node.qualifier)

    return dependencies

def find_dependencies_regex(content):
    """Fallback regex-based dependency finder."""
    dependencies = {
        'imports': set(),
        'class_uses': set(),
        'extends': set(),
        'implements': set(),
        'annotations': set()
    }
    for match in re.finditer(r'import\s+(?:static\s+)?([\w.]+);', content):
        import_class = match.group(1).split('.')[-1]
        if not import_class == '*':
            dependencies['imports'].add(import_class)
    class_decl = re.search(r'class\s+\w+(?:\s+extends\s+([\w.]+))?(?:\s+implements\s+([\w.,\s]+))?', content)
    if class_decl:
        if class_decl.group(1):
            dependencies['extends'].add(class_decl.group(1))
        if class_decl.group(2):
            for interface in class_decl.group(2).split(','):
                dependencies['implements'].add(interface.strip())
    for match in re.finditer(r'\b([A-Z]\w+)(?:\s*\.|<|\s+\w+\s*=|\s*\()', content):
        potential_class = match.group(1)
        if potential_class not in ['String', 'System', 'Override', 'Test', 'Before', 'After']:
            dependencies['class_uses'].add(potential_class)
    for match in re.finditer(r'@(\w+)', content):
        dependencies['annotations'].add(match.group(1))
    return dependencies

def find_reverse_dependencies(target_file, search_scope="src/"):
    """Find what files depend on this file using ripgrep."""
    check_ripgrep()
    target_class = extract_class_name(target_file)
    
    reverse_deps = {
        'imported_by': [],
        'extended_by': [],
        'implemented_by': [],
        'used_by': []
    }
    
    # Search for files that import or use this class
    escaped = re.escape(target_class)
    patterns = [
        (fr'import.*{escaped};', 'imported_by'),
        (fr'extends\s+{escaped}', 'extended_by'),
        (fr'implements\s+.*{escaped}', 'implemented_by'),
        (fr'\b{escaped}\s*\(|\b{escaped}\s+\w+\s*=|new\s+{escaped}', 'used_by')
    ]
    
    for pattern, dep_type in patterns:
        cmd = ['rg', '-l', '-t', 'java', pattern, search_scope]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                for file in files:
                    if file and file != target_file:
                        reverse_deps[dep_type].append(file)
        except Exception as e:
            print(f"Error searching for pattern {pattern}: {e}")
    
    return reverse_deps

def find_circular_dependencies(file_path, all_deps=None, visited=None, path=None):
    """Detect circular dependencies starting from a file."""
    if all_deps is None:
        all_deps = {}
    if visited is None:
        visited = set()
    if path is None:
        path = []
    
    if file_path in path:
        # Found circular dependency
        cycle_start = path.index(file_path)
        return path[cycle_start:] + [file_path]
    
    if file_path in visited:
        return None
    
    visited.add(file_path)
    path.append(file_path)
    
    # Get or compute dependencies for this file
    if file_path not in all_deps:
        all_deps[file_path] = find_dependencies(file_path)
    
    deps = all_deps[file_path]
    
    # Check all dependencies
    for dep_type in ['imports', 'extends', 'implements', 'class_uses']:
        for dep_class in deps[dep_type]:
            # Try to find the file for this class
            dep_file = find_file_for_class_rg(dep_class)
            if dep_file and dep_file != file_path:
                result = find_circular_dependencies(dep_file, all_deps, visited, path[:])
                if result:
                    return result
    
    return None

def find_file_for_class_rg(class_name, search_scope="src/"):
    """Find the Java file containing a class definition using ripgrep."""
    check_ripgrep()
    escaped = re.escape(class_name)
    # Look for class declaration
    cmd = ['rg', '-l', '-t', 'java', fr'class\s+{escaped}\b', search_scope]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            files = result.stdout.strip().split('\n')
            if files and files[0]:
                return files[0]  # Return first match
    except Exception:
        pass
    return None

def analyze_dependency_tree(file_path, max_depth=3, current_depth=0, visited=None):
    """Build a dependency tree for visualization."""
    if visited is None:
        visited = set()
    
    if file_path in visited or current_depth >= max_depth:
        return None
    
    visited.add(file_path)
    
    deps = find_dependencies(file_path)
    
    tree = {
        'file': file_path,
        'class': extract_class_name(file_path),
        'dependencies': {
            'imports': list(deps['imports']),
            'extends': list(deps['extends']),
            'implements': list(deps['implements']),
            'uses': list(deps['class_uses']),
            'annotations': list(deps['annotations'])
        },
        'children': []
    }
    
    # Recursively analyze dependencies
    all_deps = set()
    for dep_type in ['imports', 'extends', 'implements', 'class_uses']:
        all_deps.update(deps[dep_type])
    
    for dep_class in all_deps:
        dep_file = find_file_for_class_rg(dep_class)
        if dep_file and dep_file != file_path:
            child_tree = analyze_dependency_tree(dep_file, max_depth, current_depth + 1, visited)
            if child_tree:
                tree['children'].append(child_tree)
    
    return tree

def print_dependencies(deps):
    """Print dependencies in a readable format."""
    for dep_type, items in deps.items():
        if items:
            print(f"\n{dep_type.replace('_', ' ').title()}:")
            for item in sorted(items):
                print(f"  - {item}")

def print_reverse_dependencies(reverse_deps):
    """Print reverse dependencies in a readable format."""
    for dep_type, files in reverse_deps.items():
        if files:
            print(f"\n{dep_type.replace('_', ' ').title()}:")
            for file in sorted(files):
                print(f"  - {file}")

def print_dependency_tree(tree, indent=0):
    """Print dependency tree in a readable format."""
    if not tree:
        return
    
    prefix = "  " * indent
    print(f"{prefix}{tree['class']} ({tree['file']})")
    
    # Print direct dependencies
    deps = tree['dependencies']
    has_deps = any(deps[k] for k in deps)
    if has_deps and indent < 2:  # Limit detail depth
        for dep_type, items in deps.items():
            if items:
                print(f"{prefix}  {dep_type}:")
                for item in items[:5]:  # Limit items shown
                    print(f"{prefix}    - {item}")
                if len(items) > 5:
                    print(f"{prefix}    ... and {len(items) - 5} more")
    
    # Print children
    for child in tree['children']:
        print_dependency_tree(child, indent + 1)

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Analyze Java file dependencies using ripgrep')
    else:
        parser = argparse.ArgumentParser(description='Analyze Java file dependencies using ripgrep')
    
    # Add additional arguments not provided by standard parser
    if not HAS_STANDARD_PARSER:
        parser.add_argument('target', help='Java file to analyze')
    
    parser.add_argument('--reverse', action='store_true', 
                       help='Find what depends on this file')
    parser.add_argument('--circular', action='store_true',
                       help='Check for circular dependencies')
    parser.add_argument('--tree', action='store_true',
                       help='Show dependency tree')
    parser.add_argument('--depth', type=int, default=3,
                       help='Max depth for tree analysis (default: 3)')
    
    args = parser.parse_args()
    
    # Run preflight checks
    from preflight_checks import PreflightChecker
    run_preflight_checks([(PreflightChecker.check_ripgrep_installed, ())])
    
    # Handle file path mapping for standard parser compatibility
    file_path = getattr(args, 'target', getattr(args, 'file', None))
    if not file_path:
        print('Error: File path required', file=sys.stderr)
        sys.exit(1)
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    print(f"Analyzing: {file_path}")
    print("=" * 80)
    
    if args.reverse:
        reverse_deps = find_reverse_dependencies(file_path, args.scope)
        print("\nReverse Dependencies (what depends on this file):")
        print_reverse_dependencies(reverse_deps)
    
    elif args.circular:
        print("\nChecking for circular dependencies...")
        result = find_circular_dependencies(file_path)
        if result:
            print("Circular dependency detected:")
            for i, file in enumerate(result):
                prefix = "→ " if i < len(result) - 1 else "↻ "
                print(f"  {prefix}{file}")
        else:
            print("No circular dependencies found.")
    
    elif args.tree:
        print("\nBuilding dependency tree...")
        tree = analyze_dependency_tree(file_path, args.depth)
        if tree:
            print("\nDependency Tree:")
            print_dependency_tree(tree)
    
    else:
        # Default: show direct dependencies
        deps = find_dependencies(file_path)
        print("\nDirect Dependencies:")
        print_dependencies(deps)

if __name__ == "__main__":
    main()