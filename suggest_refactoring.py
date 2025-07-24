#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Suggest refactoring opportunities for Java files.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
import hashlib
from java_parsing_utils import extract_method_body
from standard_arg_parser import create_standard_parser, parse_standard_args

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

def analyze_method_complexity(method_content):
    """Analyze complexity metrics for a method."""
    metrics = {
        'lines': method_content.count('\n') + 1,
        'cyclomatic_complexity': 1,  # Start with 1
        'nesting_depth': 0,
        'parameters': 0,
        'local_variables': 0,
        'return_statements': 0,
        'branches': 0,
        'loops': 0,
        'try_blocks': 0
    }
    
    # Count control flow statements (approximate cyclomatic complexity)
    metrics['cyclomatic_complexity'] += len(re.findall(r'\bif\s*\(', method_content))
    metrics['cyclomatic_complexity'] += len(re.findall(r'\belse\s+if\s*\(', method_content))
    metrics['cyclomatic_complexity'] += len(re.findall(r'\belse\s*\{', method_content))
    metrics['cyclomatic_complexity'] += len(re.findall(r'\bcase\s+\w+:', method_content))
    metrics['cyclomatic_complexity'] += len(re.findall(r'\bcatch\s*\(', method_content))
    metrics['cyclomatic_complexity'] += len(re.findall(r'\bwhile\s*\(', method_content))
    metrics['cyclomatic_complexity'] += len(re.findall(r'\bfor\s*\(', method_content))
    
    # Count specific constructs
    metrics['branches'] = len(re.findall(r'\b(if|switch)\s*\(', method_content))
    metrics['loops'] = len(re.findall(r'\b(for|while|do)\s*[\(\{]', method_content))
    metrics['try_blocks'] = len(re.findall(r'\btry\s*\{', method_content))
    metrics['return_statements'] = len(re.findall(r'\breturn\b', method_content))
    
    # Estimate nesting depth
    max_depth = 0
    current_depth = 0
    for char in method_content:
        if char == '{':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char == '}':
            current_depth -= 1
    metrics['nesting_depth'] = max_depth
    
    # Count parameters (from method signature)
    param_match = re.search(r'\([^)]*\)', method_content)
    if param_match:
        params = param_match.group(0)[1:-1].strip()
        if params:
            metrics['parameters'] = len(params.split(','))
    
    # Count local variables (approximate)
    # Look for variable declarations
    var_pattern = r'^\s*(?:(?:public|private|protected|final|static)\s+)*([A-Za-z_]\w*(?:<[^>]+>)?(?:\[\])*)\s+([A-Za-z_]\w+)\s*[=;]'
    metrics['local_variables'] = len(re.findall(var_pattern, method_content, re.MULTILINE))
    
    return metrics

def find_duplicate_blocks(content, min_lines=5):
    """Find duplicate code blocks in the file."""
    # Extract all code blocks (simplified approach)
    lines = content.splitlines()
    duplicates = defaultdict(list)
    
    # Look for duplicate sequences of lines
    for i in range(len(lines) - min_lines + 1):
        block_lines = []
        for j in range(min_lines):
            # Normalize the line (remove leading/trailing whitespace)
            normalized = lines[i + j].strip()
            # Skip empty lines and single braces
            if normalized and normalized not in ['{', '}']:
                block_lines.append(normalized)
        
        if len(block_lines) >= min_lines:
            block_text = '\n'.join(block_lines)
            block_hash = hashlib.md5(block_text.encode()).hexdigest()
            duplicates[block_hash].append({
                'start_line': i + 1,
                'end_line': i + min_lines,
                'text': block_text
            })
    
    # Filter out non-duplicates
    actual_duplicates = {}
    for block_hash, occurrences in duplicates.items():
        if len(occurrences) > 1:
            actual_duplicates[block_hash] = occurrences
    
    return actual_duplicates

def find_long_parameter_lists(content):
    """Find methods with too many parameters."""
    long_param_methods = []
    
    method_pattern = r'((?:public|private|protected)\s+)?(?:static\s+)?(?:final\s+)?(?:\w+\s+)?(\w+)\s*\(([^)]+)\)'
    
    for match in re.finditer(method_pattern, content, re.MULTILINE):
        method_name = match.group(2)
        params = match.group(3).strip()
        
        if params:
            param_list = [p.strip() for p in params.split(',')]
            if len(param_list) >= 4:  # 4 or more parameters
                lines_before = content[:match.start()].count('\n')
                long_param_methods.append({
                    'name': method_name,
                    'line': lines_before + 1,
                    'param_count': len(param_list),
                    'params': param_list
                })
    
    return long_param_methods

def find_unused_private_elements(content):
    """Find potentially unused private methods and fields."""
    unused = {
        'methods': [],
        'fields': []
    }
    
    # Find all private methods
    private_method_pattern = r'private\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)?(\w+)\s*\([^)]*\)'
    for match in re.finditer(private_method_pattern, content):
        method_name = match.group(1)
        lines_before = content[:match.start()].count('\n')
        
        # Check if method is called anywhere in the file
        # Look for: methodName( or this.methodName( or super.methodName(
        call_pattern = rf'(?:this\.|super\.)?{method_name}\s*\('
        calls = re.findall(call_pattern, content)
        
        # Subtract 1 for the definition itself
        if len(calls) <= 1:
            unused['methods'].append({
                'name': method_name,
                'line': lines_before + 1,
                'calls': len(calls) - 1
            })
    
    # Find all private fields
    private_field_pattern = r'private\s+(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?(?:\[\])*)\s+(\w+)\s*[=;]'
    for match in re.finditer(private_field_pattern, content):
        field_type = match.group(1)
        field_name = match.group(2)
        lines_before = content[:match.start()].count('\n')
        
        # Check if field is used anywhere in the file
        # Look for: fieldName in various contexts
        usage_pattern = rf'\b{field_name}\b'
        usages = re.findall(usage_pattern, content)
        
        # Subtract 1 for the definition itself
        if len(usages) <= 1:
            unused['fields'].append({
                'name': field_name,
                'type': field_type,
                'line': lines_before + 1,
                'usages': len(usages) - 1
            })
    
    return unused

def suggest_extract_method_opportunities(method_content, method_name):
    """Suggest parts of a method that could be extracted."""
    suggestions = []
    
    # Look for large if blocks
    if_blocks = re.findall(r'if\s*\([^)]+\)\s*\{[^}]+\}', method_content, re.DOTALL)
    for i, block in enumerate(if_blocks):
        lines = block.count('\n')
        if lines > 10:
            suggestions.append({
                'type': 'if_block',
                'lines': lines,
                'description': f'Large if block ({lines} lines) could be extracted'
            })
    
    # Look for large try blocks
    try_blocks = re.findall(r'try\s*\{[^}]+\}', method_content, re.DOTALL)
    for i, block in enumerate(try_blocks):
        lines = block.count('\n')
        if lines > 15:
            suggestions.append({
                'type': 'try_block',
                'lines': lines,
                'description': f'Large try block ({lines} lines) could be extracted'
            })
    
    # Look for repeated code patterns within the method
    lines = method_content.splitlines()
    line_groups = defaultdict(list)
    
    for i, line in enumerate(lines):
        normalized = line.strip()
        if len(normalized) > 20 and normalized not in ['{', '}']:
            line_groups[normalized].append(i)
    
    for line, occurrences in line_groups.items():
        if len(occurrences) > 2:
            suggestions.append({
                'type': 'repeated_line',
                'occurrences': len(occurrences),
                'description': f'Line repeated {len(occurrences)} times: {line[:50]}...'
            })
    
    return suggestions

def analyze_file(file_path, min_method_size=50, check_duplication=True):
    """Analyze a Java file for refactoring opportunities."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    refactoring_suggestions = {
        'large_methods': [],
        'complex_methods': [],
        'long_parameter_lists': [],
        'duplicate_code': [],
        'unused_private': {},
        'extract_method_opportunities': []
    }
    
    # Extract all methods
    method_pattern = r'((?:(?:/\*\*[\s\S]*?\*/)\s*)?(?:@\w+(?:\([^)]*\))?\s*)*)?((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.\s]+\s+)?)?(\w+)\s*\(([^)]*)\)(?:\s+throws\s+[^{]+)?\s*\{'
    
    for match in re.finditer(method_pattern, content, re.MULTILINE):
        method_name = match.group(5)
        
        # Extract the complete method body using proper brace counting
        method_info = extract_method_body(content, match)
        
        if method_info:
            method_content = method_info['content']
            lines_before = method_info['start_line'] - 1
            
            # Analyze method complexity
            metrics = analyze_method_complexity(method_content)
            
            # Check for large methods
            if metrics['lines'] >= min_method_size:
                refactoring_suggestions['large_methods'].append({
                    'name': method_name,
                    'line': lines_before + 1,
                    'metrics': metrics
                })
            
            # Check for complex methods
            if metrics['cyclomatic_complexity'] > 10 or metrics['nesting_depth'] > 4:
                refactoring_suggestions['complex_methods'].append({
                    'name': method_name,
                    'line': lines_before + 1,
                    'metrics': metrics
                })
            
            # Look for extract method opportunities in large methods
            if metrics['lines'] > 30:
                opportunities = suggest_extract_method_opportunities(method_content, method_name)
                if opportunities:
                    refactoring_suggestions['extract_method_opportunities'].append({
                        'method': method_name,
                        'line': lines_before + 1,
                        'opportunities': opportunities
                    })
    
    # Find methods with long parameter lists
    refactoring_suggestions['long_parameter_lists'] = find_long_parameter_lists(content)
    
    # Find duplicate code blocks
    if check_duplication:
        duplicates = find_duplicate_blocks(content)
        for block_hash, occurrences in duplicates.items():
            refactoring_suggestions['duplicate_code'].append({
                'occurrences': len(occurrences),
                'locations': [occ['start_line'] for occ in occurrences],
                'preview': occurrences[0]['text'][:100] + '...' if len(occurrences[0]['text']) > 100 else occurrences[0]['text']
            })
    
    # Find unused private elements
    refactoring_suggestions['unused_private'] = find_unused_private_elements(content)
    
    return refactoring_suggestions

def print_refactoring_suggestions(suggestions, file_path):
    """Print refactoring suggestions in a readable format."""
    print("=" * 80)
    print(f"Refactoring Suggestions for: {file_path}")
    print("=" * 80)
    
    # Large methods
    if suggestions['large_methods']:
        print(f"\nLARGE METHODS ({len(suggestions['large_methods'])}):")
        print("-" * 60)
        for method in sorted(suggestions['large_methods'], key=lambda x: x['metrics']['lines'], reverse=True):
            print(f"- {method['name']} (line {method['line']}): {method['metrics']['lines']} lines")
            print(f"  Complexity: {method['metrics']['cyclomatic_complexity']}, Nesting: {method['metrics']['nesting_depth']}")
            print(f"  Suggestion: Consider breaking into smaller methods")
    
    # Complex methods
    complex_only = [m for m in suggestions['complex_methods'] 
                    if m not in suggestions['large_methods']]
    if complex_only:
        print(f"\nCOMPLEX METHODS ({len(complex_only)}):")
        print("-" * 60)
        for method in sorted(complex_only, key=lambda x: x['metrics']['cyclomatic_complexity'], reverse=True):
            print(f"- {method['name']} (line {method['line']})")
            print(f"  Cyclomatic Complexity: {method['metrics']['cyclomatic_complexity']}")
            print(f"  Nesting Depth: {method['metrics']['nesting_depth']}")
            print(f"  Suggestion: Simplify control flow, extract conditional logic")
    
    # Long parameter lists
    if suggestions['long_parameter_lists']:
        print(f"\nLONG PARAMETER LISTS ({len(suggestions['long_parameter_lists'])}):")
        print("-" * 60)
        for method in sorted(suggestions['long_parameter_lists'], key=lambda x: x['param_count'], reverse=True):
            print(f"- {method['name']} (line {method['line']}): {method['param_count']} parameters")
            print(f"  Suggestion: Consider using a parameter object or builder pattern")
    
    # Extract method opportunities
    if suggestions['extract_method_opportunities']:
        print(f"\nEXTRACT METHOD OPPORTUNITIES:")
        print("-" * 60)
        for method_info in suggestions['extract_method_opportunities']:
            print(f"\nIn {method_info['method']} (line {method_info['line']}):")
            for opp in method_info['opportunities']:
                print(f"  - {opp['description']}")
    
    # Duplicate code
    if suggestions['duplicate_code']:
        print(f"\nDUPLICATE CODE BLOCKS ({len(suggestions['duplicate_code'])}):")
        print("-" * 60)
        for dup in sorted(suggestions['duplicate_code'], key=lambda x: x['occurrences'], reverse=True):
            print(f"- Found {dup['occurrences']} times at lines: {', '.join(map(str, dup['locations']))}")
            print(f"  Preview: {dup['preview']}")
            print(f"  Suggestion: Extract to a shared method")
    
    # Unused private elements
    if suggestions['unused_private']['methods'] or suggestions['unused_private']['fields']:
        print(f"\nUNUSED PRIVATE ELEMENTS:")
        print("-" * 60)
        
        if suggestions['unused_private']['methods']:
            print(f"Unused Private Methods ({len(suggestions['unused_private']['methods'])}):")
            for method in suggestions['unused_private']['methods']:
                print(f"  - {method['name']} (line {method['line']})")
        
        if suggestions['unused_private']['fields']:
            print(f"\nUnused Private Fields ({len(suggestions['unused_private']['fields'])}):")
            for field in suggestions['unused_private']['fields']:
                print(f"  - {field['type']} {field['name']} (line {field['line']})")
    
    # Summary
    print("\n" + "=" * 80)
    print("REFACTORING PRIORITY:")
    print("=" * 80)
    
    total_issues = (len(suggestions['large_methods']) + 
                   len(complex_only) +
                   len(suggestions['long_parameter_lists']) +
                   len(suggestions['duplicate_code']) +
                   len(suggestions['unused_private']['methods']) +
                   len(suggestions['unused_private']['fields']))
    
    if total_issues == 0:
        print("No significant refactoring opportunities found!")
    else:
        print(f"Total issues found: {total_issues}")
        print("\nTop priorities:")
        
        priority = 1
        if suggestions['complex_methods']:
            print(f"{priority}. Reduce complexity in {len(suggestions['complex_methods'])} method(s)")
            priority += 1
        
        if suggestions['large_methods']:
            print(f"{priority}. Break down {len(suggestions['large_methods'])} large method(s)")
            priority += 1
        
        if suggestions['duplicate_code']:
            print(f"{priority}. Eliminate {len(suggestions['duplicate_code'])} duplicate code block(s)")
            priority += 1

def print_refactoring_suggestions_markdown(suggestions, file_path):
    """Print refactoring suggestions in Markdown format."""
    print(f"# Refactoring Suggestions for {file_path}")
    print()
    
    total_issues = (len(suggestions['large_methods']) + 
                   len([m for m in suggestions['complex_methods'] if m not in suggestions['large_methods']]) +
                   len(suggestions['long_parameter_lists']) +
                   len(suggestions['duplicate_code']) +
                   len(suggestions['unused_private']['methods']) +
                   len(suggestions['unused_private']['fields']))
    
    if total_issues == 0:
        print("✅ **No significant refactoring opportunities found!**")
        return
    
    print(f"**Total issues found:** {total_issues}")
    print()
    
    # Large methods
    if suggestions['large_methods']:
        print(f"## 🔧 Large Methods ({len(suggestions['large_methods'])})")
        print()
        for method in sorted(suggestions['large_methods'], key=lambda x: x['metrics']['lines'], reverse=True):
            print(f"- **{method['name']}** (line {method['line']}): {method['metrics']['lines']} lines")
            print(f"  - Complexity: {method['metrics']['cyclomatic_complexity']}, Nesting: {method['metrics']['nesting_depth']}")
            print(f"  - 💡 **Suggestion:** Consider breaking into smaller methods")
        print()
    
    # Complex methods
    complex_only = [m for m in suggestions['complex_methods'] 
                    if m not in suggestions['large_methods']]
    if complex_only:
        print(f"## 🧩 Complex Methods ({len(complex_only)})")
        print()
        for method in sorted(complex_only, key=lambda x: x['metrics']['cyclomatic_complexity'], reverse=True):
            print(f"- **{method['name']}** (line {method['line']})")
            print(f"  - Cyclomatic Complexity: {method['metrics']['cyclomatic_complexity']}")
            print(f"  - Nesting Depth: {method['metrics']['nesting_depth']}")
            print(f"  - 💡 **Suggestion:** Simplify control flow, extract conditional logic")
        print()
    
    # Long parameter lists
    if suggestions['long_parameter_lists']:
        print(f"## 📝 Long Parameter Lists ({len(suggestions['long_parameter_lists'])})")
        print()
        for method in sorted(suggestions['long_parameter_lists'], key=lambda x: x['param_count'], reverse=True):
            print(f"- **{method['name']}** (line {method['line']}): {method['param_count']} parameters")
            print(f"  - 💡 **Suggestion:** Consider using a parameter object or builder pattern")
        print()
    
    # Extract method opportunities
    if suggestions['extract_method_opportunities']:
        print(f"## ✂️ Extract Method Opportunities")
        print()
        for method_info in suggestions['extract_method_opportunities']:
            print(f"### In {method_info['method']} (line {method_info['line']})")
            for opp in method_info['opportunities']:
                print(f"- {opp['description']}")
        print()
    
    # Duplicate code
    if suggestions['duplicate_code']:
        print(f"## 🔄 Duplicate Code Blocks ({len(suggestions['duplicate_code'])})")
        print()
        for dup in sorted(suggestions['duplicate_code'], key=lambda x: x['occurrences'], reverse=True):
            print(f"- Found **{dup['occurrences']} times** at lines: {', '.join(map(str, dup['locations']))}")
            print(f"  - Preview: `{dup['preview']}`")
            print(f"  - 💡 **Suggestion:** Extract to a shared method")
        print()
    
    # Unused private elements
    if suggestions['unused_private']['methods'] or suggestions['unused_private']['fields']:
        print(f"## 🗑️ Unused Private Elements")
        print()
        
        if suggestions['unused_private']['methods']:
            print(f"### Unused Private Methods ({len(suggestions['unused_private']['methods'])})")
            for method in suggestions['unused_private']['methods']:
                print(f"- **{method['name']}** (line {method['line']})")
            print()
        
        if suggestions['unused_private']['fields']:
            print(f"### Unused Private Fields ({len(suggestions['unused_private']['fields'])})")
            for field in suggestions['unused_private']['fields']:
                print(f"- **{field['type']} {field['name']}** (line {field['line']})")
            print()
    
    # Summary
    print("## 🎯 Refactoring Priority")
    print()
    
    priority = 1
    if suggestions['complex_methods']:
        print(f"{priority}. **Reduce complexity** in {len(suggestions['complex_methods'])} method(s)")
        priority += 1
    
    if suggestions['large_methods']:
        print(f"{priority}. **Break down** {len(suggestions['large_methods'])} large method(s)")
        priority += 1
    
    if suggestions['duplicate_code']:
        print(f"{priority}. **Eliminate** {len(suggestions['duplicate_code'])} duplicate code block(s)")
        priority += 1

def main():
    parser = create_standard_parser('analyze', 
                                   'Suggest refactoring opportunities for Java files')
    
    # Add specific options for refactoring analysis
    parser.add_argument('--min-method-size', type=int, default=50,
                       help='Minimum lines for a method to be considered large (default: 50)')
    parser.add_argument('--check-duplication', action='store_true', default=True,
                       help='Check for duplicate code blocks')
    parser.add_argument('--no-duplication', dest='check_duplication', action='store_false',
                       help='Skip duplicate code detection')
    parser.add_argument('--output', choices=['text', 'markdown'], default='text',
                       help='Output format (default: text)')
    
    # Parse arguments without validation since this tool accepts file paths as target
    args = parser.parse_args()
    
    # Handle file specification - prioritize --file flag, fallback to target
    if hasattr(args, 'file') and args.file:
        file_path = args.file
    else:
        file_path = args.target
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    suggestions = analyze_file(file_path, args.min_method_size, args.check_duplication)
    
    if args.json:
        import json
        print(json.dumps(suggestions, indent=2))
    elif args.output == 'markdown':
        print_refactoring_suggestions_markdown(suggestions, file_path)
    else:
        print_refactoring_suggestions(suggestions, file_path)

if __name__ == "__main__":
    main()