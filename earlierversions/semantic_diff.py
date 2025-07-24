#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Semantic code comparison tool that analyzes logic changes rather than just text differences.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import argparse
from pathlib import Path
from collections import OrderedDict
from typing import Dict, Tuple, List, Optional
import difflib

# Import utilities if available
try:
    from common_utils import safe_get_file_content, detect_language
except ImportError:
    def safe_get_file_content(filepath: str, max_size_mb: float = 10) -> Optional[str]:
        """Read file content safely with size limits."""
        try:
            path = Path(filepath)
            if not path.exists():
                return None
            
            # Check file size
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                print(f"Warning: File too large ({size_mb:.1f}MB), skipping", file=sys.stderr)
                return None
            
            return path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return None

def normalize_code(code: str, remove_comments: bool = True) -> str:
    """
    Normalizes code by removing comments and standardizing whitespace.
    
    Args:
        code: The source code to normalize.
        remove_comments: Whether to remove comments.
        
    Returns:
        Normalized code string.
    """
    if remove_comments:
        # Remove single-line comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        # Remove multi-line comments
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        # Remove Python-style comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    
    # Normalize whitespace
    code = re.sub(r'\s+', ' ', code)
    # Remove leading/trailing whitespace
    code = code.strip()
    
    return code

def extract_logic_elements(code: str) -> Dict[str, List[str]]:
    """
    Extracts logical elements from code for semantic comparison.
    
    Args:
        code: The source code to analyze.
        
    Returns:
        Dictionary of logic elements by category.
    """
    elements = {
        'control_structures': [],
        'method_calls': [],
        'assignments': [],
        'declarations': [],
        'exceptions': [],
        'loops': [],
        'conditions': [],
        'returns': []
    }
    
    # Control structures - capture the keyword, not the whole expression
    control_pattern = r'\b(if|else if|else|switch|case)(?=\s*\()'
    elements['control_structures'] = re.findall(control_pattern, code)
    
    # Method calls - match all potential methods first
    method_pattern = r'\b(\w+)\s*\([^)]*\)'
    all_methods = re.findall(method_pattern, code)
    # Also exclude common non-method patterns
    exclude_patterns = {'if', 'else', 'switch', 'while', 'for', 'catch', 'synchronized', 
                       'with', 'return', 'throw', 'new', 'typeof', 'instanceof', 'sizeof'}
    elements['method_calls'] = [m for m in all_methods if m not in exclude_patterns]
    
    # Variable assignments - avoid matching == or != operators
    assignment_pattern = r'(\w+)\s*=(?!=)\s*[^=]'
    elements['assignments'] = re.findall(assignment_pattern, code)
    
    # Variable/field declarations
    # Java-style declarations
    java_decl_pattern = r'\b(?:public|private|protected|static|final)?\s*(\w+)\s+(\w+)\s*[;=]'
    # Convert tuples to strings (type varname)
    declarations = [f"{match[0]} {match[1]}" for match in re.findall(java_decl_pattern, code)]
    elements['declarations'].extend(declarations)
    
    # Exception handling
    exception_pattern = r'\b(try|catch|finally|throw|throws)\b'
    elements['exceptions'] = re.findall(exception_pattern, code)
    
    # Loops
    loop_pattern = r'\b(for|while|do)\s*\('
    elements['loops'] = re.findall(loop_pattern, code)
    
    # Conditional expressions
    condition_pattern = r'([<>!=]=?|&&|\|\|)'
    elements['conditions'] = re.findall(condition_pattern, code)
    
    # Return statements
    return_pattern = r'\breturn\s+([^;]+);'
    elements['returns'] = re.findall(return_pattern, code)
    
    return elements

def compare_logic_elements(elements1: Dict, elements2: Dict) -> Dict[str, Dict]:
    """
    Compares two sets of logic elements to identify changes.
    
    Args:
        elements1: Logic elements from first code version.
        elements2: Logic elements from second code version.
        
    Returns:
        Dictionary of changes by element type.
    """
    changes = {}
    
    for category in elements1.keys():
        set1 = set(elements1[category])
        set2 = set(elements2[category])
        
        if set1 != set2:
            changes[category] = {
                'added': list(set2 - set1),
                'removed': list(set1 - set2),
                'changed': len(set1 ^ set2) > 0
            }
    
    return changes

def extract_methods(code: str, language: str = 'java') -> Dict[str, Dict]:
    """
    Extracts methods from code.
    
    Args:
        code: The source code.
        language: Programming language.
        
    Returns:
        Dictionary of methods by signature.
    """
    methods = OrderedDict()
    
    if language == 'java':
        # Java method pattern
        pattern = r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    elif language == 'python':
        # Python method pattern
        pattern = r'def\s+(\w+)\s*\([^)]*\):\n((?:\s{4,}.*\n)*)'
    else:
        # Generic pattern
        pattern = r'(\w+)\s*\([^)]*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    
    for match in re.finditer(pattern, code, re.MULTILINE | re.DOTALL):
        method_name = match.group(1)
        method_body = match.group(2)
        signature = match.group(0).split('{')[0].strip()
        
        methods[signature] = {
            'name': method_name,
            'signature': signature,
            'content': match.group(0),
            'body': method_body,
            'start_pos': match.start(),
            'end_pos': match.end()
        }
    
    return methods

def detect_change_types(code1: str, code2: str) -> Dict[str, bool]:
    """
    Detects the types of changes between two code versions.
    
    Args:
        code1: First version of code.
        code2: Second version of code.
        
    Returns:
        Dictionary indicating types of changes detected.
    """
    # Normalize for comparison
    norm1 = normalize_code(code1, remove_comments=True)
    norm2 = normalize_code(code2, remove_comments=True)
    
    # If normalized versions are identical, only comments changed
    if norm1 == norm2:
        return {
            'comment_only_change': True,
            'logic_change': False,
            'structure_change': False,
            'whitespace_only': normalize_code(code1, remove_comments=False) == normalize_code(code2, remove_comments=False)
        }
    
    # Extract and compare logic elements
    elements1 = extract_logic_elements(code1)
    elements2 = extract_logic_elements(code2)
    element_changes = compare_logic_elements(elements1, elements2)
    
    # Determine change types
    structure_changed = any(
        element_changes.get(cat, {}).get('changed', False) 
        for cat in ['control_structures', 'loops', 'exceptions']
    )
    
    logic_changed = any(
        element_changes.get(cat, {}).get('changed', False) 
        for cat in ['conditions', 'returns', 'method_calls']
    )
    
    return {
        'comment_only_change': False,
        'logic_change': logic_changed,
        'structure_change': structure_changed,
        'variable_change': element_changes.get('assignments', {}).get('changed', False),
        'declaration_change': element_changes.get('declarations', {}).get('changed', False),
        'element_changes': element_changes
    }

def enhanced_method_comparison(methods1: Dict, methods2: Dict) -> Tuple[Dict, Dict, Dict]:
    """
    Performs enhanced comparison of methods with semantic analysis.
    
    Args:
        methods1: Methods from first file.
        methods2: Methods from second file.
        
    Returns:
        Tuple of (added_methods, removed_methods, modified_methods).
    """
    added = OrderedDict()
    removed = OrderedDict()
    modified = OrderedDict()
    
    # Find removed methods
    for sig, method in methods1.items():
        if sig not in methods2:
            removed[sig] = method
    
    # Find added methods
    for sig, method in methods2.items():
        if sig not in methods1:
            added[sig] = method
    
    # Find modified methods
    for sig, method1 in methods1.items():
        if sig in methods2:
            method2 = methods2[sig]
            
            # Quick check if content is identical
            if method1['content'] == method2['content']:
                continue
            
            # Perform semantic analysis
            change_types = detect_change_types(method1['content'], method2['content'])
            
            modified[sig] = {
                'old': method1,
                'new': method2,
                'change_types': change_types,
                'diff': list(difflib.unified_diff(
                    method1['content'].splitlines(keepends=True),
                    method2['content'].splitlines(keepends=True),
                    fromfile=f"{sig} (old)",
                    tofile=f"{sig} (new)",
                    lineterm=''
                ))
            }
    
    return added, removed, modified

def format_semantic_diff_report(added: Dict, removed: Dict, modified: Dict,
                              show_logic_only: bool = False,
                              show_details: bool = True) -> str:
    """
    Formats the semantic diff analysis into a readable report.
    
    Args:
        added: Dictionary of added methods.
        removed: Dictionary of removed methods.
        modified: Dictionary of modified methods.
        show_logic_only: Only show methods with logic changes.
        show_details: Show detailed change information.
        
    Returns:
        Formatted report string.
    """
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("SEMANTIC CODE COMPARISON REPORT")
    output.append("=" * 80)
    
    # Summary
    output.append("\n📊 SUMMARY")
    output.append("-" * 40)
    
    # Count logic changes
    logic_changes = sum(1 for m in modified.values() 
                       if m['change_types'].get('logic_change', False))
    comment_only = sum(1 for m in modified.values() 
                      if m['change_types'].get('comment_only_change', False))
    structure_changes = sum(1 for m in modified.values() 
                          if m['change_types'].get('structure_change', False))
    
    output.append(f"Methods Added: {len(added)}")
    output.append(f"Methods Removed: {len(removed)}")
    output.append(f"Methods Modified: {len(modified)}")
    if modified:
        output.append(f"  - Logic Changes: {logic_changes}")
        output.append(f"  - Structure Changes: {structure_changes}")
        output.append(f"  - Comment-Only Changes: {comment_only}")
    
    # Added methods
    if added:
        output.append("\n➕ ADDED METHODS")
        output.append("-" * 40)
        for sig, method in added.items():
            output.append(f"  + {sig}")
    
    # Removed methods
    if removed:
        output.append("\n➖ REMOVED METHODS")
        output.append("-" * 40)
        for sig, method in removed.items():
            output.append(f"  - {sig}")
    
    # Modified methods
    if modified:
        output.append("\n🔄 MODIFIED METHODS")
        output.append("-" * 40)
        
        for sig, changes in modified.items():
            change_types = changes['change_types']
            
            # Skip if only showing logic changes and this isn't one
            if show_logic_only and not change_types.get('logic_change', False):
                continue
            
            # Method header with change indicators
            indicators = []
            if change_types.get('logic_change'):
                indicators.append("LOGIC")
            if change_types.get('structure_change'):
                indicators.append("STRUCTURE")
            if change_types.get('comment_only_change'):
                indicators.append("COMMENTS")
            if change_types.get('variable_change'):
                indicators.append("VARIABLES")
            
            output.append(f"\n  {'*' if change_types.get('logic_change') else '○'} {sig}")
            if indicators:
                output.append(f"    Changes: {', '.join(indicators)}")
            
            # Show detailed changes if requested
            if show_details and change_types.get('element_changes'):
                element_changes = change_types['element_changes']
                for category, changes in element_changes.items():
                    if changes.get('added') or changes.get('removed'):
                        output.append(f"    {category.replace('_', ' ').title()}:")
                        if changes.get('added'):
                            output.append(f"      + Added: {', '.join(changes['added'][:3])}")
                        if changes.get('removed'):
                            output.append(f"      - Removed: {', '.join(changes['removed'][:3])}")
    
    return '\n'.join(output)

def main():
    parser = argparse.ArgumentParser(
        description='Semantic code comparison - Compare code based on logic rather than text',
        epilog='''
EXAMPLES:
  # Basic semantic comparison
  %(prog)s FileV1.java FileV2.java
  
  # Show only logic changes
  %(prog)s FileV1.java FileV2.java --logic-only
  
  # Show detailed change analysis
  %(prog)s FileV1.java FileV2.java --show-details
  
  # Compare Python files
  %(prog)s old_version.py new_version.py --language python
  
  # Show traditional diff for methods with logic changes
  %(prog)s FileV1.java FileV2.java --show-diff
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('file1', help='First file to compare')
    parser.add_argument('file2', help='Second file to compare')
    
    # Comparison options
    parser.add_argument('--language', '--lang', 
                       choices=['java', 'python', 'javascript', 'cpp'],
                       default='java', help='Programming language (default: java)')
    parser.add_argument('--logic-only', action='store_true',
                       help='Show only methods with logic changes')
    parser.add_argument('--show-details', action='store_true', default=True,
                       help='Show detailed change information (default: true)')
    parser.add_argument('--show-diff', action='store_true',
                       help='Show unified diff for modified methods')
    
    # Output options
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output')
    
    args = parser.parse_args()
    
    try:
        # Read files
        content1 = safe_get_file_content(args.file1)
        content2 = safe_get_file_content(args.file2)
        
        if content1 is None:
            print(f"Error: Cannot read file '{args.file1}'", file=sys.stderr)
            sys.exit(1)
        
        if content2 is None:
            print(f"Error: Cannot read file '{args.file2}'", file=sys.stderr)
            sys.exit(1)
        
        # Extract methods
        if not args.quiet:
            print(f"Analyzing {args.file1} vs {args.file2}...", file=sys.stderr)
        
        methods1 = extract_methods(content1, args.language)
        methods2 = extract_methods(content2, args.language)
        
        # Perform comparison
        added, removed, modified = enhanced_method_comparison(methods1, methods2)
        
        # Generate report
        report = format_semantic_diff_report(
            added, removed, modified,
            show_logic_only=args.logic_only,
            show_details=args.show_details
        )
        
        print(report)
        
        # Show diffs if requested
        if args.show_diff and modified:
            print("\n" + "=" * 80)
            print("DETAILED DIFFS FOR MODIFIED METHODS")
            print("=" * 80)
            
            for sig, changes in modified.items():
                if args.logic_only and not changes['change_types'].get('logic_change'):
                    continue
                
                print(f"\n{sig}:")
                print('\n'.join(changes['diff']))
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()