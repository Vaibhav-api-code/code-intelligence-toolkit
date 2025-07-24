#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced smart diff tool for semantic code comparison.

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
import difflib
from collections import OrderedDict, defaultdict
import hashlib

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

def normalize_code_for_comparison(code, ignore_whitespace=True, ignore_comments=True):
    """Normalize code for semantic comparison."""
    if ignore_comments:
        # Remove single-line comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove JavaDoc comments
        code = re.sub(r'/\*\*.*?\*/', '', code, flags=re.DOTALL)
    
    if ignore_whitespace:
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        code = re.sub(r'\s*([{}();,=+\-*/])\s*', r'\1', code)
        code = code.strip()
    
    return code

def extract_logic_elements(code):
    """Extract logical elements from code for comparison."""
    elements = {
        'control_structures': [],
        'method_calls': [],
        'variable_assignments': [],
        'conditions': [],
        'loops': [],
        'exception_handling': []
    }
    
    # Control structures
    control_patterns = [
        (r'if\s*\([^)]+\)', 'if'),
        (r'else\s*(?:if\s*\([^)]+\))?', 'else'),
        (r'switch\s*\([^)]+\)', 'switch'),
        (r'case\s+[^:]+:', 'case'),
        (r'default\s*:', 'default')
    ]
    
    for pattern, structure_type in control_patterns:
        matches = re.findall(pattern, code, re.MULTILINE)
        elements['control_structures'].extend([(structure_type, match) for match in matches])
    
    # Loops
    loop_patterns = [
        (r'for\s*\([^)]+\)', 'for'),
        (r'while\s*\([^)]+\)', 'while'),
        (r'do\s*\{', 'do-while')
    ]
    
    for pattern, loop_type in loop_patterns:
        matches = re.findall(pattern, code, re.MULTILINE)
        elements['loops'].extend([(loop_type, match) for match in matches])
    
    # Method calls
    method_calls = re.findall(r'(\w+)\s*\([^)]*\)', code)
    elements['method_calls'] = method_calls
    
    # Variable assignments
    assignments = re.findall(r'(\w+)\s*=\s*([^;]+)', code)
    elements['variable_assignments'] = assignments
    
    # Exception handling
    exception_patterns = [
        (r'try\s*\{', 'try'),
        (r'catch\s*\([^)]+\)', 'catch'),
        (r'finally\s*\{', 'finally'),
        (r'throw\s+[^;]+', 'throw')
    ]
    
    for pattern, exc_type in exception_patterns:
        matches = re.findall(pattern, code, re.MULTILINE)
        elements['exception_handling'].extend([(exc_type, match) for match in matches])
    
    return elements

def calculate_semantic_similarity(code1, code2):
    """Calculate semantic similarity between two code blocks."""
    elements1 = extract_logic_elements(code1)
    elements2 = extract_logic_elements(code2)
    
    similarities = {}
    total_score = 0
    total_weight = 0
    
    weights = {
        'control_structures': 3,
        'method_calls': 2,
        'loops': 3,
        'exception_handling': 2,
        'variable_assignments': 1
    }
    
    for element_type, weight in weights.items():
        set1 = set(str(item) for item in elements1[element_type])
        set2 = set(str(item) for item in elements2[element_type])
        
        if set1 or set2:
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            similarity = intersection / union if union > 0 else 0
        else:
            similarity = 1.0  # Both empty
        
        similarities[element_type] = similarity
        total_score += similarity * weight
        total_weight += weight
    
    overall_similarity = total_score / total_weight if total_weight > 0 else 1.0
    return overall_similarity, similarities

def detect_change_types(method1, method2):
    """Detect specific types of changes between methods."""
    changes = {
        'signature_change': False,
        'logic_change': False,
        'variable_rename': False,
        'control_flow_change': False,
        'method_call_change': False,
        'exception_handling_change': False,
        'comment_only_change': False
    }
    
    # Check signature changes
    sig1 = extract_method_signature(method1)
    sig2 = extract_method_signature(method2)
    changes['signature_change'] = sig1 != sig2
    
    # Normalize both methods for comparison
    norm1 = normalize_code_for_comparison(method1, ignore_whitespace=True, ignore_comments=True)
    norm2 = normalize_code_for_comparison(method2, ignore_whitespace=True, ignore_comments=True)
    
    # Check if only comments changed
    if norm1 == norm2:
        changes['comment_only_change'] = True
        return changes
    
    # Extract logic elements
    elements1 = extract_logic_elements(method1)
    elements2 = extract_logic_elements(method2)
    
    # Check for control flow changes
    if elements1['control_structures'] != elements2['control_structures']:
        changes['control_flow_change'] = True
    
    if elements1['loops'] != elements2['loops']:
        changes['control_flow_change'] = True
    
    # Check for method call changes
    if set(elements1['method_calls']) != set(elements2['method_calls']):
        changes['method_call_change'] = True
    
    # Check for exception handling changes
    if elements1['exception_handling'] != elements2['exception_handling']:
        changes['exception_handling_change'] = True
    
    # Check for variable renames (same assignments with different names)
    if len(elements1['variable_assignments']) == len(elements2['variable_assignments']):
        assignments1 = [assign[1] for assign in elements1['variable_assignments']]
        assignments2 = [assign[1] for assign in elements2['variable_assignments']]
        if assignments1 == assignments2:
            vars1 = [assign[0] for assign in elements1['variable_assignments']]
            vars2 = [assign[0] for assign in elements2['variable_assignments']]
            if vars1 != vars2:
                changes['variable_rename'] = True
    
    # General logic change if semantic similarity is low
    similarity, _ = calculate_semantic_similarity(method1, method2)
    if similarity < 0.7:
        changes['logic_change'] = True
    
    return changes

def extract_method_signature(method_code):
    """Extract method signature for comparison."""
    # Find the method declaration line
    lines = method_code.split('\n')
    for line in lines:
        if '(' in line and (')' in line or '{' in line):
            # Clean up the signature
            signature = re.sub(r'\s+', ' ', line.strip())
            signature = re.sub(r'\s*\{\s*$', '', signature)
            return signature
    return ""

def generate_change_summary(changes, method_name):
    """Generate a human-readable summary of changes."""
    summary = []
    
    if changes['comment_only_change']:
        summary.append("📝 Comments/documentation only")
        return summary
    
    if changes['signature_change']:
        summary.append("🔧 Method signature changed")
    
    if changes['logic_change']:
        summary.append("⚡ Core logic modified")
    
    if changes['control_flow_change']:
        summary.append("🔀 Control flow altered (if/else, loops)")
    
    if changes['method_call_change']:
        summary.append("📞 Method calls changed")
    
    if changes['exception_handling_change']:
        summary.append("🛡️ Exception handling modified")
    
    if changes['variable_rename']:
        summary.append("🏷️ Variables renamed")
    
    if not summary:
        summary.append("📊 Minor changes detected")
    
    return summary

def extract_methods_dict(content):
    """Extract all methods from Java content into a dictionary."""
    # This function is now self-contained by calling the utility below
    def _find_closing_brace(text, open_pos):
        if text[open_pos] != '{':
            return -1
        level = 1
        for i in range(open_pos + 1, len(text)):
            if text[i] == '{':
                level += 1
            elif text[i] == '}':
                level -= 1
            if level == 0:
                return i
        return -1

    methods = OrderedDict()
    
    # Pattern to find methods with their complete body
    method_pattern = r'((?:(?:/\*\*[\s\S]*?\*/)\s*)?(?:@\w+(?:\([^)]*\))?\s*)*)?((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.\s]+\s+)?)?(\w+)\s*\(([^)]*)\)(?:\s+throws\s+[^{]+)?\s*\{'
    
    for match in re.finditer(method_pattern, content, re.MULTILINE):
        # Check if this match is in a commented line
        match_line_start = content.rfind('\n', 0, match.start()) + 1
        match_line_end = content.find('\n', match.start())
        if match_line_end == -1:
            match_line_end = len(content)
        match_line = content[match_line_start:match_line_end].strip()
        
        # Skip if the line starts with a comment
        if match_line.startswith('//') or match_line.startswith('/*'):
            continue
            
        javadoc = match.group(1) if match.group(1) else ""
        visibility = match.group(2) if match.group(2) else "package-private"
        modifiers = match.group(3) if match.group(3) else ""
        return_type = match.group(4) if match.group(4) else ""
        method_name = match.group(5)
        parameters = match.group(6)
        
        # Find the complete method body using proper brace counting
        start_pos = match.start()
        brace_pos = match.end() - 1  # Position of opening brace
        
        # Use proper brace counting utility to find the end of the method
        end_pos = _find_closing_brace(content, brace_pos)
        
        if end_pos != -1:
            # The method content includes the signature and the full body
            method_content = content[start_pos:end_pos + 1]
            
            # Create method signature for key
            signature = f"{method_name}({parameters})"
            
            methods[signature] = {
                'content': method_content,
                'visibility': visibility.strip(),
                'modifiers': modifiers.strip(),
                'return_type': return_type.strip(),
                'name': method_name,
                'parameters': parameters,
                'javadoc': javadoc.strip()
            }
    
    return methods

def remove_comments_and_whitespace(content):
    """Remove comments and normalize whitespace."""
    # Remove single-line comments
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    
    # Remove multi-line comments
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    
    # Normalize whitespace
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'\s*([{}();,])\s*', r'\1', content)
    
    return content.strip()

def compare_methods(methods1, methods2):
    """Compare two method dictionaries and return differences."""
    added = OrderedDict()
    removed = OrderedDict()
    modified = OrderedDict()
    
    # Find removed and modified methods
    for sig, method1 in methods1.items():
        if sig not in methods2:
            removed[sig] = method1
        else:
            # Compare method content (normalized)
            content1 = remove_comments_and_whitespace(method1['content'])
            content2 = remove_comments_and_whitespace(methods2[sig]['content'])
            
            if content1 != content2:
                modified[sig] = {
                    'old': method1,
                    'new': methods2[sig]
                }
    
    # Find added methods
    for sig, method2 in methods2.items():
        if sig not in methods1:
            added[sig] = method2
    
    return added, removed, modified

def compare_files(file1_path, file2_path, methods_only=False, ignore_comments=False):
    """Compare two Java files."""
    with open(file1_path, 'r', encoding='utf-8') as f:
        content1 = f.read()
    
    with open(file2_path, 'r', encoding='utf-8') as f:
        content2 = f.read()
    
    if methods_only:
        # Extract and compare methods
        methods1 = extract_methods_dict(content1)
        methods2 = extract_methods_dict(content2)
        
        return compare_methods(methods1, methods2)
    else:
        # Full file comparison
        if ignore_comments:
            content1 = remove_comments_and_whitespace(content1)
            content2 = remove_comments_and_whitespace(content2)
            lines1 = [content1]
            lines2 = [content2]
        else:
            lines1 = content1.splitlines(keepends=True)
            lines2 = content2.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(lines1, lines2, 
                                        fromfile=str(file1_path),
                                        tofile=str(file2_path)))
        
        return diff

def print_method_diff(added, removed, modified):
    """Print method-level differences."""
    print("=" * 80)
    print("METHOD-LEVEL COMPARISON")
    print("=" * 80)
    
    if removed:
        print(f"\nREMOVED METHODS ({len(removed)}):")
        print("-" * 60)
        for sig, method in removed.items():
            visibility = f"{method['visibility']} {method['modifiers']}".strip()
            print(f"- {visibility} {method['return_type']} {sig}")
    
    if added:
        print(f"\nADDED METHODS ({len(added)}):")
        print("-" * 60)
        for sig, method in added.items():
            visibility = f"{method['visibility']} {method['modifiers']}".strip()
            print(f"+ {visibility} {method['return_type']} {sig}")
    
    if modified:
        print(f"\nMODIFIED METHODS ({len(modified)}):")
        print("-" * 60)
        for sig, changes in modified.items():
            print(f"~ {sig}")
            
            # Show what changed
            old_method = changes['old']
            new_method = changes['new']
            
            # Check signature changes
            if old_method['visibility'] != new_method['visibility']:
                print(f"  Visibility: {old_method['visibility']} → {new_method['visibility']}")
            
            if old_method['modifiers'] != new_method['modifiers']:
                print(f"  Modifiers: {old_method['modifiers']} → {new_method['modifiers']}")
            
            if old_method['return_type'] != new_method['return_type']:
                print(f"  Return type: {old_method['return_type']} → {new_method['return_type']}")
            
            # Show size change
            old_lines = old_method['content'].count('\n') + 1
            new_lines = new_method['content'].count('\n') + 1
            if old_lines != new_lines:
                diff_lines = new_lines - old_lines
                sign = '+' if diff_lines > 0 else ''
                print(f"  Size: {old_lines} → {new_lines} lines ({sign}{diff_lines})")
    
    # Summary
    print(f"\nSUMMARY:")
    print(f"  Methods removed: {len(removed)}")
    print(f"  Methods added: {len(added)}")
    print(f"  Methods modified: {len(modified)}")
    print(f"  Total changes: {len(removed) + len(added) + len(modified)}")

def analyze_structural_changes(file1_path, file2_path):
    """Analyze structural changes between files."""
    with open(file1_path, 'r', encoding='utf-8') as f:
        content1 = f.read()
    
    with open(file2_path, 'r', encoding='utf-8') as f:
        content2 = f.read()
    
    changes = {
        'imports': {'added': [], 'removed': []},
        'fields': {'added': [], 'removed': []},
        'inner_classes': {'added': [], 'removed': []},
        'annotations': {'added': [], 'removed': []}
    }
    
    # Compare imports
    imports1 = set(re.findall(r'import\s+(?:static\s+)?([\w.*]+);', content1))
    imports2 = set(re.findall(r'import\s+(?:static\s+)?([\w.*]+);', content2))
    
    changes['imports']['removed'] = sorted(imports1 - imports2)
    changes['imports']['added'] = sorted(imports2 - imports1)
    
    # Compare fields
    field_pattern = r'^\s*((?:public|private|protected)\s+)?((?:static|final|volatile|transient)\s+)*([\w<>\[\],.\s]+)\s+(\w+)\s*(?:=|;)'
    
    fields1 = set(match.group(4) for match in re.finditer(field_pattern, content1, re.MULTILINE))
    fields2 = set(match.group(4) for match in re.finditer(field_pattern, content2, re.MULTILINE))
    
    changes['fields']['removed'] = sorted(fields1 - fields2)
    changes['fields']['added'] = sorted(fields2 - fields1)
    
    return changes

def print_structural_changes(changes):
    """Print structural changes."""
    print("\n" + "=" * 80)
    print("STRUCTURAL CHANGES")
    print("=" * 80)
    
    # Imports
    if changes['imports']['removed'] or changes['imports']['added']:
        print("\nImport Changes:")
        for imp in changes['imports']['removed']:
            print(f"  - {imp}")
        for imp in changes['imports']['added']:
            print(f"  + {imp}")
    
    # Fields
    if changes['fields']['removed'] or changes['fields']['added']:
        print("\nField Changes:")
        for field in changes['fields']['removed']:
            print(f"  - {field}")
        for field in changes['fields']['added']:
            print(f"  + {field}")

def enhanced_method_comparison(methods1, methods2, highlight_logic_changes=True):
    """Enhanced method comparison with semantic analysis."""
    added, removed, modified = compare_methods(methods1, methods2)
    
    # Enhance modified methods with semantic analysis
    enhanced_modified = OrderedDict()
    
    for sig, changes in modified.items():
        old_method = changes['old']['content']
        new_method = changes['new']['content']
        
        # Detect change types
        change_types = detect_change_types(old_method, new_method)
        
        # Calculate semantic similarity
        similarity, detailed_similarities = calculate_semantic_similarity(old_method, new_method)
        
        # Generate change summary
        summary = generate_change_summary(change_types, sig)
        
        enhanced_modified[sig] = {
            **changes,
            'change_types': change_types,
            'semantic_similarity': similarity,
            'detailed_similarities': detailed_similarities,
            'change_summary': summary
        }
    
    return added, removed, enhanced_modified

def print_enhanced_method_diff(added, removed, modified, show_details=True):
    """Print enhanced method-level differences with semantic analysis."""
    print("=" * 80)
    print("ENHANCED SEMANTIC COMPARISON")
    print("=" * 80)
    
    if removed:
        print(f"\n🗑️  REMOVED METHODS ({len(removed)}):")
        print("-" * 60)
        for sig, method in removed.items():
            visibility = f"{method['visibility']} {method['modifiers']}".strip()
            print(f"  - {visibility} {method['return_type']} {sig}")
    
    if added:
        print(f"\n➕ ADDED METHODS ({len(added)}):")
        print("-" * 60)
        for sig, method in added.items():
            visibility = f"{method['visibility']} {method['modifiers']}".strip()
            print(f"  + {visibility} {method['return_type']} {sig}")
    
    if modified:
        print(f"\n🔄 MODIFIED METHODS ({len(modified)}):")
        print("-" * 60)
        
        for sig, changes in modified.items():
            print(f"\n  📝 {sig}")
            
            # Show change summary
            for summary_item in changes['change_summary']:
                print(f"    {summary_item}")
            
            # Show semantic similarity
            similarity = changes['semantic_similarity']
            sim_emoji = "🟢" if similarity > 0.8 else "🟡" if similarity > 0.5 else "🔴"
            print(f"    {sim_emoji} Semantic similarity: {similarity:.1%}")
            
            if show_details and similarity < 0.9:
                # Show detailed similarities
                detailed = changes['detailed_similarities']
                print(f"      Control structures: {detailed.get('control_structures', 0):.1%}")
                print(f"      Method calls: {detailed.get('method_calls', 0):.1%}")
                print(f"      Loops: {detailed.get('loops', 0):.1%}")
            
            # Show size change
            old_method = changes['old']
            new_method = changes['new']
            old_lines = old_method['content'].count('\n') + 1
            new_lines = new_method['content'].count('\n') + 1
            if old_lines != new_lines:
                diff_lines = new_lines - old_lines
                sign = '+' if diff_lines > 0 else ''
                size_emoji = "📈" if diff_lines > 0 else "📉"
                print(f"    {size_emoji} Size: {old_lines} → {new_lines} lines ({sign}{diff_lines})")
    
    # Enhanced summary
    print(f"\n📊 SUMMARY:")
    print(f"  Methods removed: {len(removed)}")
    print(f"  Methods added: {len(added)}")
    print(f"  Methods modified: {len(modified)}")
    
    if modified:
        # Categorize changes
        logic_changes = sum(1 for changes in modified.values() if changes['change_types']['logic_change'])
        signature_changes = sum(1 for changes in modified.values() if changes['change_types']['signature_change'])
        comment_only = sum(1 for changes in modified.values() if changes['change_types']['comment_only_change'])
        
        print(f"    Logic changes: {logic_changes}")
        print(f"    Signature changes: {signature_changes}")
        print(f"    Comment-only changes: {comment_only}")
        
        # Average semantic similarity
        if modified:
            avg_similarity = sum(changes['semantic_similarity'] for changes in modified.values()) / len(modified)
            print(f"  Average semantic similarity: {avg_similarity:.1%}")
    
    print(f"  Total changes: {len(removed) + len(added) + len(modified)}")

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Enhanced smart diff for semantic code comparison')
    else:
        parser = argparse.ArgumentParser(description='Enhanced smart diff for semantic code comparison', formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('file1', help='First file to compare')
    parser.add_argument('file2', help='Second file to compare')
    
    # Comparison modes
    parser.add_argument('--methods-only', action='store_true',
                       help='Compare only at method level with semantic analysis')
    parser.add_argument('--ignore-whitespace', action='store_true',
                       help='Ignore whitespace differences')
    parser.add_argument('--ignore-comments', action='store_true',
                       help='Ignore comments and documentation changes')
    
    # Analysis options
    parser.add_argument('--highlight-logic-changes', action='store_true', default=True,
                       help='Highlight significant logic changes (default: true)')
    parser.add_argument('--show-details', action='store_true',
                       help='Show detailed semantic analysis')
    parser.add_argument('--show-structural', action='store_true',
                       help='Show structural changes (imports, fields)')
    parser.add_argument('--show-all', action='store_true',
                       help='Show all available analysis')
    
    # Filtering options
    parser.add_argument('--logic-changes-only', action='store_true',
                       help='Show only methods with significant logic changes')
    parser.add_argument('--min-similarity', type=float, default=0.0,
                       help='Minimum semantic similarity to show (0.0-1.0)')
    parser.add_argument('--max-changes', type=int,
                       help='Maximum number of changes to display')
    
    args = parser.parse_args()
    
    # Validate files
    if not Path(args.file1).exists():
        print(f"Error: File '{args.file1}' not found")
        sys.exit(1)
    
    if not Path(args.file2).exists():
        print(f"Error: File '{args.file2}' not found")
        sys.exit(1)
    
    # Handle show-all flag
    if args.show_all:
        args.methods_only = True
        args.show_details = True
        args.show_structural = True
        args.highlight_logic_changes = True
    
    print(f"🔍 Comparing: {args.file1}")
    print(f"      with: {args.file2}")
    
    try:
        if args.methods_only:
            # Enhanced method-level comparison
            with open(args.file1, 'r', encoding='utf-8') as f:
                content1 = f.read()
            with open(args.file2, 'r', encoding='utf-8') as f:
                content2 = f.read()
            
            methods1 = extract_methods_dict(content1)
            methods2 = extract_methods_dict(content2)
            
            added, removed, modified = enhanced_method_comparison(
                methods1, methods2, args.highlight_logic_changes
            )
            
            # Filter by logic changes if requested
            if args.logic_changes_only:
                modified = OrderedDict([
                    (sig, changes) for sig, changes in modified.items()
                    if changes['change_types']['logic_change']
                ])
            
            # Filter by semantic similarity
            if args.min_similarity > 0:
                modified = OrderedDict([
                    (sig, changes) for sig, changes in modified.items()
                    if changes['semantic_similarity'] >= args.min_similarity
                ])
            
            # Limit number of changes
            if args.max_changes:
                # Sort by semantic similarity (lowest first for most interesting changes)
                sorted_modified = sorted(modified.items(), 
                                       key=lambda x: x[1]['semantic_similarity'])
                modified = OrderedDict(sorted_modified[:args.max_changes])
            
            print_enhanced_method_diff(added, removed, modified, args.show_details)
        
        else:
            # Traditional file comparison
            diff = compare_files(args.file1, args.file2, 
                               ignore_comments=args.ignore_comments)
            if diff:
                max_lines = args.max_changes or 100
                for line in diff[:max_lines]:
                    print(line, end='')
                if len(diff) > max_lines:
                    print(f"\n... and {len(diff) - max_lines} more lines")
            else:
                print("\n✅ No differences found")
        
        # Structural analysis
        if args.show_structural:
            changes = analyze_structural_changes(args.file1, args.file2)
            print_structural_changes(changes)
    
    except Exception as e:
        print(f"Error during comparison: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()