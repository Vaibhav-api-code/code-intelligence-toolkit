#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
semantic_diff v2 - Semantic code comparison with standardized interface.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import argparse
import ast
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import standard parser
try:
    from standard_arg_parser import create_standard_parser, parse_standard_args
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False

# Import pre-flight checks
try:
    from preflight_checks import PreflightChecker, run_preflight_checks
except ImportError:
    PreflightChecker = None
    run_preflight_checks = None


def compare_files_semantic(file1: str, file2: str, args) -> Dict:
    """Compare files semantically, focusing on logic differences."""
    results = {
        'file1': file1,
        'file2': file2,
        'identical': False,
        'logic_changes': [],
        'structural_changes': [],
        'whitespace_only': False
    }

    try:
        # Read files
        with open(file1, 'r', encoding='utf-8') as f1:
            content1 = f1.read()
        with open(file2, 'r', encoding='utf-8') as f2:
            content2 = f2.read()

        # Quick check - identical files
        if content1 == content2:
            results['identical'] = True
            return results

        # Check if only whitespace differences
        clean1 = ''.join(content1.split())
        clean2 = ''.join(content2.split())

        if clean1 == clean2:
            results['whitespace_only'] = True
            return results

        # AST-based comparison
        try:
            tree1 = ast.parse(content1)
            tree2 = ast.parse(content2)

            # This is a more sophisticated AST comparison that recursively checks the trees.
            differences = []
            compare_nodes(tree1, tree2, differences)

            if not differences:
                results['structural_changes'].append({
                    'line': 0,
                    'type': 'structural',
                    'old': 'Files have the same structure but different content',
                    'new': ''
                })
            else:
                for diff in differences:
                    results['logic_changes'].append({
                        'line': diff['line'],
                        'type': 'logic',
                        'old': diff['old'],
                        'new': diff['new'],
                        'source': diff.get('source', '')
                    })

        except SyntaxError as e:
            results['error'] = f"Syntax error: {e}"

        return results

    except Exception as e:
        return {'error': str(e)}

def compare_nodes(node1, node2, differences):
    """Recursively compare two AST nodes."""
    if type(node1) != type(node2):
        differences.append({
            'line': getattr(node1, 'lineno', 0),
            'old': f"Node type changed from {type(node1).__name__} to {type(node2).__name__}",
            'new': '',
            'source': ast.dump(node1)
        })
        return

    for field, value1 in ast.iter_fields(node1):
        value2 = getattr(node2, field, None)
        if isinstance(value1, list) and isinstance(value2, list):
            # Compare lists of nodes
            dumped_value1 = {ast.dump(node): node for node in value1}
            dumped_value2 = {ast.dump(node): node for node in value2}

            # Nodes removed from value1
            for dumped_node_str, node in dumped_value1.items():
                if dumped_node_str not in dumped_value2:
                    differences.append({
                        'line': getattr(node, 'lineno', 0),
                        'type': 'removed_node',
                        'old': f"Removed: {ast.dump(node)}",
                        'new': '',
                        'source': ast.dump(node)
                    })
            
            # Nodes added to value2
            for dumped_node_str, node in dumped_value2.items():
                if dumped_node_str not in dumped_value1:
                    differences.append({
                        'line': getattr(node, 'lineno', 0),
                        'type': 'added_node',
                        'old': '',
                        'new': f"Added: {ast.dump(node)}",
                        'source': ast.dump(node)
                    })
            
            # Recursively compare common nodes
            for dumped_node_str, node1_item in dumped_value1.items():
                if dumped_node_str in dumped_value2:
                    node2_item = dumped_value2[dumped_node_str]
                    compare_nodes(node1_item, node2_item, differences)

        elif isinstance(value1, ast.AST) and isinstance(value2, ast.AST):
            compare_nodes(value1, value2, differences)
        elif value1 != value2:
            differences.append({
                'line': getattr(node1, 'lineno', 0),
                'old': f"{field} = {value1}",
                'new': f"{field} = {value2}",
                'source': ast.dump(node1)
            })


def format_comparison_output(results: Dict, args) -> None:
    """Format and display comparison results."""
    if args.json:
        import json
        # Convert results to JSON-serializable format
        output = {
            'file1': results['file1'],
            'file2': results['file2'],
            'identical': results.get('identical', False),
            'whitespace_only': results.get('whitespace_only', False),
            'logic_changes_count': len(results.get('logic_changes', [])),
            'structural_changes_count': len(results.get('structural_changes', [])),
            'logic_changes': results.get('logic_changes', []),
            'structural_changes': results.get('structural_changes', [])
        }
        print(json.dumps(output, indent=2))
        return
    
    # Text output
    print(f"📊 SEMANTIC COMPARISON")
    print(f"{'=' * 60}")
    print(f"File 1: {results['file1']}")
    print(f"File 2: {results['file2']}")
    print()
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    if results.get('identical'):
        print("✅ Files are identical")
        return
    
    if results.get('whitespace_only'):
        print("📝 Files differ only in whitespace/formatting")
        if not args.ignore_whitespace:
            print("   (use --ignore-whitespace to suppress this)")
        return
    
    # Logic changes
    logic_changes = results.get('logic_changes', [])
    if logic_changes:
        print(f"🔄 LOGIC CHANGES ({len(logic_changes)}):")
        print("-" * 40)
        for change in logic_changes[:10]:  # Limit to 10
            print(f"Line {change['line']:3d}: {change['type']}")
            if change['type'] == 'removed_node':
                print(f"  - {change['old']}")
            elif change['type'] == 'added_node':
                print(f"  + {change['new']}")
            else:
                print(f"  - {change['old']}")
                print(f"  + {change['new']}")
            if 'source' in change:
                print(f"    Source: {change['source']}")
            print()
    
    # Structural changes
    structural_changes = results.get('structural_changes', [])
    if structural_changes and not args.logic_only:
        print(f"🏗️  STRUCTURAL CHANGES ({len(structural_changes)}):")
        print("-" * 40)
        for change in structural_changes[:5]:  # Limit to 5
            print(f"Line {change['line']:3d}: {change['type']}")
            if change['type'] == 'removed_node':
                print(f"  - {change['old']}")
            elif change['type'] == 'added_node':
                print(f"  + {change['new']}")
            else:
                print(f"  - {change['old']}")
                print(f"  + {change['new']}")
            if 'source' in change:
                print(f"    Source: {change['source']}")
            print()
    
    # Summary
    print(f"📈 SUMMARY:")
    print(f"   Logic changes: {len(logic_changes)}")
    if not args.logic_only:
        print(f"   Structural changes: {len(structural_changes)}")
    print(f"   Total significant differences: {len(logic_changes) + len(structural_changes)}")


def main():
    if HAS_STANDARD_PARSER:
        # Create custom parser since semantic_diff has specific needs
        parser = argparse.ArgumentParser(
            description='semantic_diff v2 - Semantic code comparison',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
EXAMPLES:
  # Basic semantic comparison
  %(prog)s file1.java file2.java
  
  # Focus only on logic changes
  %(prog)s old.py new.py --logic-only
  
  # Ignore whitespace differences
  %(prog)s v1.js v2.js --ignore-whitespace
  
  # JSON output for integration
  %(prog)s before.cpp after.cpp --json
  
  # Show detailed differences
  %(prog)s original.py modified.py --show-diff --verbose

COMPARISON TYPES:
  - Logic changes: Control flow, function definitions, algorithms
  - Added nodes: New code blocks, functions, or statements
  - Removed nodes: Deleted code blocks, functions, or statements
  - Structural changes: Variable names, comments, formatting
  - Whitespace-only: Indentation, spacing, line endings
            '''
        )
        
        # File arguments (required)
        parser.add_argument('file1', help='First file to compare')
        parser.add_argument('file2', help='Second file to compare')
        
        # Comparison options
        parser.add_argument('--logic-only', action='store_true',
                           help='Show only logic changes, ignore structural')
        parser.add_argument('--ignore-whitespace', action='store_true',
                           help='Ignore whitespace-only differences')
        parser.add_argument('--show-diff', action='store_true',
                           help='Show detailed line-by-line differences')
        
        # Standard flags
        parser.add_argument('--json', action='store_true', help='Output in JSON format')
        parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
        parser.add_argument('-q', '--quiet', action='store_true', help='Minimal output')
        
    else:
        # Fallback parser
        parser = argparse.ArgumentParser(description='semantic_diff v2 - Semantic comparison')
        parser.add_argument('file1', help='First file')
        parser.add_argument('file2', help='Second file')
        parser.add_argument('--logic-only', action='store_true')
        parser.add_argument('--ignore-whitespace', action='store_true')
        parser.add_argument('--show-diff', action='store_true')
        parser.add_argument('--json', action='store_true')
        parser.add_argument('--verbose', action='store_true')
        parser.add_argument('--quiet', action='store_true')
    
    args = parser.parse_args()
    
    # Pre-flight checks
    if PreflightChecker and run_preflight_checks:
        run_preflight_checks([
            (PreflightChecker.check_file_readable, (args.file1,)),
            (PreflightChecker.check_file_readable, (args.file2,))
        ])
    
    try:
        # Perform comparison
        if not args.quiet:
            print(f"Comparing {args.file1} and {args.file2}...", file=sys.stderr)
        
        results = compare_files_semantic(args.file1, args.file2, args)
        
        # Display results
        format_comparison_output(results, args)
        
    except KeyboardInterrupt:
        print("\\nComparison interrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()