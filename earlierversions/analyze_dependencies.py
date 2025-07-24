#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Analyze dependencies between Java files and classes.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from pathlib import Path
import argparse
from collections import defaultdict
import subprocess

try:
    import javalang
    HAS_JAVALANG = True
except ImportError:
    HAS_JAVALANG = False

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
    """Find what files depend on this file."""
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
        (fr'extends\\s+{escaped}', 'extended_by'),
        (fr'implements\\s+.*{escaped}', 'implemented_by'),
        (fr'\\b{escaped}\\s*\\(|\\b{escaped}\\s+\\w+\\s*=|new\\s+{escaped}', 'used_by')
    ]
    
    for pattern, dep_type in patterns:
        cmd = ['grep', '-r', '-l', '-E', pattern, search_scope, '--include=*.java']
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
        return [path[cycle_start:] + [file_path]]
    
    if file_path in visited:
        return []
    
    visited.add(file_path)
    path.append(file_path)
    
    # Get or compute dependencies
    if file_path not in all_deps:
        deps = find_dependencies(file_path)
        all_deps[file_path] = deps
    
    cycles = []
    
    # Check dependencies
    for dep_class in all_deps[file_path]['imports'] | all_deps[file_path]['extends'] | all_deps[file_path]['implements']:
        # Try to find the file for this dependency
        dep_files = find_class_files(dep_class)
        for dep_file in dep_files:
            if dep_file and Path(dep_file).exists():
                sub_cycles = find_circular_dependencies(dep_file, all_deps, visited, path.copy())
                cycles.extend(sub_cycles)
    
    path.pop()
    return cycles

def find_class_files(class_name, search_scope="src/"):
    """Find Java files that define a given class."""
    files = []
    escaped = re.escape(class_name)
    cmd = ['grep', '-r', '-l', fr'class\\s+{escaped}\\b', search_scope, '--include=*.java']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            files = [f for f in result.stdout.strip().split('\n') if f]
    except Exception:
        pass
    return files

def create_dependency_graph(file_path, depth=2):
    """Create a text-based dependency graph."""
    visited = set()
    graph = []
    
    def build_graph(current_file, current_depth=0, prefix=""):
        if current_depth > depth or current_file in visited:
            return
        
        visited.add(current_file)
        class_name = extract_class_name(current_file)
        
        # Add current node
        if current_depth == 0:
            graph.append(f"{class_name} ({Path(current_file).name})")
        else:
            graph.append(f"{prefix}└── {class_name}")
        
        if current_depth < depth:
            deps = find_dependencies(current_file)
            all_deps = deps['imports'] | deps['extends'] | deps['implements']
            
            for i, dep in enumerate(sorted(all_deps)):
                is_last = (i == len(all_deps) - 1)
                new_prefix = prefix + ("    " if is_last else "│   ")
                
                # Try to find file for this dependency
                dep_files = find_class_files(dep)
                if dep_files:
                    for dep_file in dep_files[:1]:  # Only take first match
                        build_graph(dep_file, current_depth + 1, new_prefix)
                else:
                    # Show external dependency
                    graph.append(f"{new_prefix}└── {dep} (external)")
    
    build_graph(file_path)
    return graph

def print_dependencies(file_path, deps, reverse_deps, cycles):
    """Print dependency analysis results."""
    class_name = extract_class_name(file_path)
    
    print("=" * 80)
    print(f"Dependency Analysis for: {class_name}")
    print(f"File: {file_path}")
    print("=" * 80)
    
    # Forward dependencies
    print("\nDEPENDENCIES (what this file depends on):")
    print("-" * 60)
    
    if deps['extends']:
        print(f"Extends: {', '.join(deps['extends'])}")
    
    if deps['implements']:
        print(f"Implements: {', '.join(deps['implements'])}")
    
    if deps['imports']:
        print(f"\nImported Classes ({len(deps['imports'])}):")
        for imp in sorted(deps['imports']):
            print(f"  - {imp}")
    
    if deps['class_uses']:
        print(f"\nClass References ({len(deps['class_uses'])}):")
        # Show top 10 most referenced
        for cls in sorted(deps['class_uses'])[:10]:
            print(f"  - {cls}")
        if len(deps['class_uses']) > 10:
            print(f"  ... and {len(deps['class_uses']) - 10} more")
    
    # Reverse dependencies
    print("\n\nREVERSE DEPENDENCIES (what depends on this file):")
    print("-" * 60)
    
    total_reverse = sum(len(files) for files in reverse_deps.values())
    if total_reverse == 0:
        print("No files depend on this class")
    else:
        if reverse_deps['extended_by']:
            print(f"\nExtended by ({len(reverse_deps['extended_by'])}):")
            for file in reverse_deps['extended_by']:
                print(f"  - {file}")
        
        if reverse_deps['implemented_by']:
            print(f"\nImplemented by ({len(reverse_deps['implemented_by'])}):")
            for file in reverse_deps['implemented_by']:
                print(f"  - {file}")
        
        if reverse_deps['imported_by']:
            print(f"\nImported by ({len(reverse_deps['imported_by'])}):")
            for file in reverse_deps['imported_by'][:5]:
                print(f"  - {file}")
            if len(reverse_deps['imported_by']) > 5:
                print(f"  ... and {len(reverse_deps['imported_by']) - 5} more")
        
        if reverse_deps['used_by']:
            print(f"\nUsed by ({len(reverse_deps['used_by'])}):")
            for file in reverse_deps['used_by'][:5]:
                print(f"  - {file}")
            if len(reverse_deps['used_by']) > 5:
                print(f"  ... and {len(reverse_deps['used_by']) - 5} more")
    
    # Circular dependencies
    if cycles:
        print("\n\nCIRCULAR DEPENDENCIES DETECTED:")
        print("-" * 60)
        for cycle in cycles:
            print("Cycle: " + " -> ".join(Path(f).name for f in cycle))

def main():
    parser = argparse.ArgumentParser(description='Analyze Java file dependencies')
    parser.add_argument('file', help='Java file to analyze')
    parser.add_argument('--depth', type=int, default=2, 
                       help='Depth for dependency graph (default: 2)')
    parser.add_argument('--reverse', action='store_true',
                       help='Focus on reverse dependencies')
    parser.add_argument('--graph', action='store_true',
                       help='Show dependency graph')
    parser.add_argument('--check-circular', action='store_true',
                       help='Check for circular dependencies')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    # Analyze dependencies
    deps = find_dependencies(args.file, args.depth)
    reverse_deps = find_reverse_dependencies(args.file)
    
    cycles = []
    if args.check_circular:
        cycles = find_circular_dependencies(args.file)
    
    # Print results
    print_dependencies(args.file, deps, reverse_deps, cycles)
    
    # Show graph if requested
    if args.graph:
        print("\n\nDEPENDENCY GRAPH:")
        print("-" * 60)
        graph = create_dependency_graph(args.file, args.depth)
        for line in graph:
            print(line)

if __name__ == "__main__":
    main()