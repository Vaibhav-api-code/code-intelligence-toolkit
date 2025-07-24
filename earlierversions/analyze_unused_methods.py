#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Analyze a Java file to find potentially unused methods by checking if they're called within the codebase.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import subprocess
from pathlib import Path
from collections import defaultdict

def extract_methods_from_file(file_path):
    """Extract all method signatures from a Java file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find method declarations
    method_pattern = r'^\s*(public|private|protected)(?:\s+(?:static|final|synchronized|abstract))*\s+(?:(?:<[^>]+>\s+)?([^(\s]+)\s+)?([a-zA-Z0-9_]+)\s*\([^{]*\)\s*(?:throws\s+[^{]+)?\s*\{'
    
    methods = []
    for match in re.finditer(method_pattern, content, re.MULTILINE):
        visibility = match.group(1)
        return_type = match.group(2) or 'void'
        method_name = match.group(3)
        
        # Get line number
        lines_before = content[:match.start()].count('\n')
        line_number = lines_before + 1
        
        methods.append({
            'name': method_name,
            'visibility': visibility,
            'return_type': return_type,
            'line': line_number,
            'full_match': match.group(0).strip()
        })
    
    return methods

def check_method_usage(method_name, search_path="src/", exclude_file=None):
    """Check if a method is called anywhere in the codebase using grep."""
    try:
        # Build grep command to search for method calls
        # Look for patterns like: .methodName( or methodName(
        patterns = [
            f'\\.{method_name}\\s*\\(',  # Instance method call
            f'\\b{method_name}\\s*\\(',   # Direct call or static call
        ]
        
        total_count = 0
        calling_files = set()
        
        for pattern in patterns:
            cmd = ['grep', '-r', '-l', '-E', pattern, search_path, '--include=*.java']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                files = [f for f in files if f and (exclude_file is None or not f.endswith(exclude_file))]
                calling_files.update(files)
        
        return len(calling_files), list(calling_files)
        
    except Exception as e:
        print(f"Error checking usage for {method_name}: {e}")
        return 0, []

def analyze_file(file_path, search_path="src/"):
    """Analyze a Java file to find potentially unused methods."""
    print(f"Analyzing {file_path}...")
    print("=" * 80)
    
    methods = extract_methods_from_file(file_path)
    print(f"Found {len(methods)} methods\n")
    
    # Categorize methods
    unused_methods = []
    rarely_used_methods = []
    commonly_used_methods = []
    
    # Methods that are typically not called directly
    special_methods = {
        'main', 'toString', 'equals', 'hashCode', 'compareTo', 
        'run', 'call', 'execute', 'finalize', 'clone',
        'readObject', 'writeObject', 'readResolve', 'writeReplace'
    }
    
    # Check each method
    for method in methods:
        # Skip constructors
        if method['name'] == Path(file_path).stem.split('.')[-1]:
            continue
            
        # Skip special methods
        if method['name'] in special_methods:
            continue
            
        # Skip getters/setters (they might be used via reflection)
        if method['name'].startswith(('get', 'set', 'is')) and method['visibility'] == 'public':
            continue
        
        usage_count, calling_files = check_method_usage(method['name'], search_path, file_path)
        
        method['usage_count'] = usage_count
        method['calling_files'] = calling_files
        
        if usage_count == 0:
            unused_methods.append(method)
        elif usage_count <= 2:
            rarely_used_methods.append(method)
        else:
            commonly_used_methods.append(method)
    
    # Report findings
    print(f"\n{'='*80}")
    print("ANALYSIS RESULTS")
    print(f"{'='*80}\n")
    
    if unused_methods:
        print(f"POTENTIALLY UNUSED METHODS ({len(unused_methods)}):")
        print("-" * 40)
        for method in sorted(unused_methods, key=lambda x: x['line']):
            print(f"Line {method['line']:4d}: {method['visibility']} {method['name']}(...)")
            print(f"           Full: {method['full_match'][:60]}...")
        print()
    
    if rarely_used_methods:
        print(f"\nRARELY USED METHODS ({len(rarely_used_methods)}) - Used in {1}-2 files:")
        print("-" * 40)
        for method in sorted(rarely_used_methods, key=lambda x: x['usage_count']):
            print(f"Line {method['line']:4d}: {method['visibility']} {method['name']}(...) - Used in {method['usage_count']} file(s)")
            for f in method['calling_files']:
                print(f"           Called from: {f}")
        print()
    
    print(f"\nSUMMARY:")
    print(f"  Total methods analyzed: {len(methods)}")
    print(f"  Potentially unused: {len(unused_methods)}")
    print(f"  Rarely used (1-2 files): {len(rarely_used_methods)}")
    print(f"  Commonly used (3+ files): {len(commonly_used_methods)}")
    
    # Calculate potential size reduction
    if unused_methods:
        print(f"\nRECOMMENDATIONS:")
        print(f"  - Consider removing {len(unused_methods)} unused methods")
        print(f"  - Review {len(rarely_used_methods)} rarely used methods for potential consolidation")
        
        # List specific methods good for removal
        print(f"\nMethods safe to remove (private and unused):")
        for method in unused_methods:
            if method['visibility'] == 'private':
                print(f"  - {method['name']} (line {method['line']})")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_unused_methods.py <java_file> [search_path]")
        print("Example: python analyze_unused_methods.py OrderSenderControllerV2.java src/")
        sys.exit(1)
    
    file_path = sys.argv[1]
    search_path = sys.argv[2] if len(sys.argv) > 2 else "src/"
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    analyze_file(file_path, search_path)

if __name__ == "__main__":
    main()