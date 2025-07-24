#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Cross-file dependency analysis tool for finding all callers of methods or classes.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import json
import re
import sys
import argparse
import os
from pathlib import Path
import shutil
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Tuple

# Import common utilities if available

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

try:
    from common_utils import check_ripgrep, detect_language, add_common_args
except ImportError:
    # Fallback if common_utils not available
    def check_ripgrep():
        if not shutil.which('rg'):
            print("Error: ripgrep (rg) is not installed or not in your PATH.", file=sys.stderr)
            print("Please install it from: https://github.com/BurntSushi/ripgrep#installation", file=sys.stderr)
            sys.exit(1)

def find_all_callers(target: str, scope: str = ".", language: str = None, 
                    whole_word: bool = True, ignore_case: bool = False) -> str:
    """
    Finds all files and locations that reference the target using ripgrep's JSON output.

    Args:
        target: The method or class name to search for.
        scope: The directory to search within.
        language: The language to filter for (e.g., 'java', 'python').
        whole_word: Whether to match whole words only.
        ignore_case: Whether to ignore case in matching.

    Returns:
        The raw JSON string output from ripgrep.
    """
    check_ripgrep()
    
    # Input validation and sanitization
    if not target or not target.strip():
        print("Error: Target cannot be empty", file=sys.stderr)
        return ""
    
    # Sanitize target to prevent command injection
    if any(char in target for char in ['`', '$', ';', '|', '&', '>', '<', '(', ')', '\n', '\r']):
        print(f"Error: Invalid characters in target '{target}'", file=sys.stderr)
        return ""
    
    # Validate scope path
    scope_path = Path(scope)
    if not scope_path.exists():
        print(f"Error: Scope path '{scope}' does not exist", file=sys.stderr)
        return ""
    
    # Sanitize language parameter
    if language and not re.match(r'^[a-zA-Z0-9_-]+$', language):
        print(f"Error: Invalid language identifier '{language}'", file=sys.stderr)
        return ""

    # Use ripgrep with JSON output for robust parsing
    cmd = ['rg']
    
    if whole_word:
        cmd.append('-w')
    
    if ignore_case:
        cmd.append('-i')
    
    if language:
        cmd.extend(['-t', language])
    
    # Use absolute path for scope to prevent path traversal
    cmd.extend([target, str(scope_path.resolve())])
    
    try:
        # Enhanced subprocess security
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120,
            cwd=scope_path.resolve(),  # Set working directory explicitly
            shell=False,  # Never use shell=True
            env={'PATH': os.environ.get('PATH', '')},  # Minimal environment
            check=False  # Don't raise on non-zero exit
        )
        
        if result.returncode != 0 and result.stderr:
            print(f"Warning: ripgrep returned error: {result.stderr.strip()}", file=sys.stderr)
        
        return result.stdout
        
    except subprocess.TimeoutExpired:
        print(f"Search timed out for target: {target}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"Search failed: {e}", file=sys.stderr)
        return ""

def is_likely_definition(content: str, filepath: str) -> bool:
    """
    Determines if a line is likely a definition rather than a usage.
    
    Args:
        content: The line content.
        filepath: The file path (to determine language).
        
    Returns:
        True if likely a definition, False otherwise.
    """
    content_lower = content.lower().strip()
    
    # Language-specific definition patterns
    if filepath.endswith(('.py', '.pyw')):
        # Python function/class definitions
        return bool(re.match(r'^\s*(def|class)\s+', content))
    
    elif filepath.endswith(('.java', '.scala', '.kt')):
        # Java/JVM language method/class definitions
        # Look for access modifiers, return types, etc.
        patterns = [
            r'^\s*(public|private|protected|static|final|abstract|synchronized|native|strictfp)*\s*class\s+',
            r'^\s*(public|private|protected|static|final|abstract|synchronized|native)*\s*\w+\s+\w+\s*\(',
            r'^\s*@\w+\s*$',  # Annotations often precede definitions
        ]
        return any(re.search(pattern, content) for pattern in patterns)
    
    elif filepath.endswith(('.js', '.jsx', '.ts', '.tsx')):
        # JavaScript/TypeScript definitions
        patterns = [
            r'^\s*function\s+\w+\s*\(',
            r'^\s*(?:export\s+)?(?:async\s+)?function\s+',
            r'^\s*class\s+\w+',
            r'^\s*(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>)',
        ]
        return any(re.search(pattern, content) for pattern in patterns)
    
    elif filepath.endswith(('.c', '.cpp', '.cc', '.cxx', '.h', '.hpp')):
        # C/C++ definitions
        # Look for function signatures (return type followed by name and parentheses)
        return bool(re.search(r'^\s*(?:\w+\s+)*\w+\s+\w+\s*\([^)]*\)\s*\{?', content))
    
    elif filepath.endswith('.go'):
        # Go definitions
        return bool(re.match(r'^\s*func\s+', content))
    
    elif filepath.endswith('.rs'):
        # Rust definitions
        return bool(re.match(r'^\s*(fn|struct|enum|trait|impl)\s+', content))
    
    elif filepath.endswith('.rb'):
        # Ruby definitions
        return bool(re.match(r'^\s*(def|class|module)\s+', content))
    
    elif filepath.endswith('.php'):
        # PHP definitions
        return bool(re.match(r'^\s*(function|class)\s+', content))
    
    # Generic heuristic for unknown languages
    # Look for common definition keywords
    generic_patterns = [
        r'^\s*(function|def|class|struct|interface|enum)\s+',
        r'^\s*(public|private|protected)\s+.*\(',
    ]
    return any(re.search(pattern, content_lower) for pattern in generic_patterns)

def parse_caller_results(output: str) -> List[Dict]:
    """
    Parses ripgrep's JSON output to extract structured caller information.

    Args:
        output: The raw JSON string from ripgrep.

    Returns:
        A list of dictionaries, where each dictionary represents a caller.
    """
    callers = []
    line_count = 0
    max_lines = 10000  # Prevent memory issues with huge outputs
    
    for line in output.strip().split('\n'):
        line_count += 1
        if line_count > max_lines:
            print(f"Warning: Output truncated after {max_lines} lines", file=sys.stderr)
            break
            
        if not line:
            continue
            
        try:
            data = json.loads(line)
            # We only care about the 'match' events
            if data['type'] == 'match':
                match_data = data['data']
                
                # Security: Validate file path
                file_path = match_data['path']['text']
                if not file_path or '..' in file_path or file_path.startswith('/'):
                    continue  # Skip suspicious paths
                
                # Extract context lines if available
                context_before = []
                context_after = []
                
                # ripgrep JSON format includes submatches for exact positions
                submatches = match_data.get('submatches', [])
                match_positions = [(sm['start'], sm['end']) for sm in submatches] if submatches else []
                
                # Determine if this is a definition or usage
                content = match_data['lines']['text'].strip()
                
                # Limit content length to prevent memory issues
                if len(content) > 1000:
                    content = content[:1000] + "..."
                
                is_definition = is_likely_definition(content, file_path)
                
                callers.append({
                    'file': file_path,
                    'line_number': match_data['line_number'],
                    'content': content,
                    'match_positions': match_positions,
                    'context_before': context_before,
                    'context_after': context_after,
                    'is_definition': is_definition
                })
                
                # Limit total results to prevent memory issues
                if len(callers) > 5000:
                    print(f"Warning: Results truncated after {len(callers)} matches", file=sys.stderr)
                    break
                    
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Log parsing errors but continue
            if line_count <= 10:  # Only log first few errors
                print(f"Warning: Failed to parse line {line_count}: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Unexpected error parsing line {line_count}: {e}", file=sys.stderr)
            continue
            
    return callers

def analyze_method_usage(calls: List[Dict], target: str) -> Dict:
    """
    Analyzes a list of method calls to calculate frequency and usage patterns.

    Args:
        calls: A list of call-site dictionaries from parse_caller_results.
        target: The target method/class name for context.

    Returns:
        A dictionary containing the analysis.
    """
    # Separate definitions from usages
    definitions = [c for c in calls if c.get('is_definition', False)]
    usages = [c for c in calls if not c.get('is_definition', False)]
    
    analysis = {
        'target': target,
        'total_references': len(calls),
        'total_definitions': len(definitions),
        'total_usages': len(usages),
        'unique_files': len(set(c['file'] for c in calls)),
        'by_file': Counter(c['file'] for c in usages),  # Count only usages per file
        'definitions': definitions,
        'calling_contexts': Counter(),
        'usage_patterns': defaultdict(list)
    }
    
    # Analyze calling contexts (only for usages, not definitions)
    for call in usages:
        content = call['content']
        content_lower = content.lower()
        
        # Detect calling context
        if re.search(r'\bif\s*\(|else\s+if\s*\(|\belse\b', content):
            analysis['calling_contexts']['conditional'] += 1
            analysis['usage_patterns']['conditional'].append(call)
        elif re.search(r'\bfor\s*\(|\bwhile\s*\(|\bdo\s*{', content):
            analysis['calling_contexts']['loop'] += 1
            analysis['usage_patterns']['loop'].append(call)
        elif re.search(r'\breturn\s+', content):
            analysis['calling_contexts']['return_statement'] += 1
            analysis['usage_patterns']['return'].append(call)
        elif re.search(r'\bcatch\s*\(|\btry\s*{|\bthrow\s+', content):
            analysis['calling_contexts']['exception_handling'] += 1
            analysis['usage_patterns']['exception'].append(call)
        elif re.search(r'=\s*' + re.escape(target), content):
            analysis['calling_contexts']['assignment'] += 1
            analysis['usage_patterns']['assignment'].append(call)
        elif re.search(r'\bnew\s+' + re.escape(target), content):
            analysis['calling_contexts']['instantiation'] += 1
            analysis['usage_patterns']['instantiation'].append(call)
        else:
            analysis['calling_contexts']['other'] += 1
            analysis['usage_patterns']['other'].append(call)
    
    # Detect if this is likely a utility method (called from many files)
    if analysis['unique_files'] > 5 and analysis['total_calls'] > 10:
        analysis['likely_utility'] = True
    else:
        analysis['likely_utility'] = False
    
    return analysis

def highlight_match(content: str, match_positions: List[Tuple[int, int]]) -> str:
    """
    Highlights matches within content using ANSI color codes.
    
    Args:
        content: The line content.
        match_positions: List of (start, end) positions for matches.
        
    Returns:
        Content with highlighted matches.
    """
    if not match_positions:
        return content
    
    # Sort positions by start index
    positions = sorted(match_positions, key=lambda x: x[0])
    
    # Build highlighted string
    result = []
    last_end = 0
    
    for start, end in positions:
        # Add text before match
        result.append(content[last_end:start])
        # Add highlighted match
        result.append(f"\033[93m{content[start:end]}\033[0m")  # Yellow highlight
        last_end = end
    
    # Add remaining text
    result.append(content[last_end:])
    
    return ''.join(result)

def format_analysis_report(analysis: Dict, show_samples: bool = True, 
                         max_samples: int = 3) -> str:
    """
    Formats the usage analysis into a readable report.

    Args:
        analysis: The analysis dictionary from analyze_method_usage.
        show_samples: Whether to show sample calls.
        max_samples: Maximum samples per category.

    Returns:
        Formatted report string.
    """
    output = []
    
    # Header
    output.append("=" * 80)
    output.append(f"CROSS-FILE USAGE ANALYSIS: '{analysis['target']}'")
    output.append("=" * 80)
    
    # Summary statistics
    output.append(f"\n📊 SUMMARY STATISTICS")
    output.append("-" * 40)
    output.append(f"Total References: {analysis['total_references']}")
    output.append(f"  Definitions: {analysis['total_definitions']}")
    output.append(f"  Usages: {analysis['total_usages']}")
    output.append(f"Unique Files: {analysis['unique_files']}")
    output.append(f"Average Usages per File: {analysis['total_usages'] / max(1, analysis['unique_files']):.1f}")
    
    if analysis['likely_utility']:
        output.append("\n⚡ This appears to be a utility method (used across many files)")
    
    # Show definitions if any
    if analysis['definitions']:
        output.append(f"\n📌 DEFINITIONS FOUND")
        output.append("-" * 40)
        for defn in analysis['definitions'][:3]:  # Show up to 3 definitions
            output.append(f"  {Path(defn['file']).name}:{defn['line_number']}")
            highlighted = highlight_match(defn['content'], defn.get('match_positions', []))
            output.append(f"    {highlighted}")
        if len(analysis['definitions']) > 3:
            output.append(f"  ... and {len(analysis['definitions']) - 3} more")
    
    # Top files by usage
    output.append(f"\n📁 TOP FILES BY USAGE (excluding definitions)")
    output.append("-" * 40)
    for file_path, count in analysis['by_file'].most_common(10):
        file_name = Path(file_path).name
        output.append(f"  {count:3d}x {file_name:30} ({file_path})")
    
    if len(analysis['by_file']) > 10:
        output.append(f"  ... and {len(analysis['by_file']) - 10} more files")
    
    # Calling contexts
    output.append(f"\n🔍 CALLING CONTEXTS")
    output.append("-" * 40)
    total_contexts = sum(analysis['calling_contexts'].values())
    for context, count in analysis['calling_contexts'].most_common():
        percentage = (count / total_contexts * 100) if total_contexts > 0 else 0
        context_name = context.replace('_', ' ').title()
        output.append(f"  {context_name:20} {count:4d} ({percentage:5.1f}%)")
    
    # Sample usage patterns
    if show_samples and analysis['usage_patterns']:
        output.append(f"\n💡 SAMPLE USAGE PATTERNS")
        output.append("-" * 40)
        
        for pattern, calls in analysis['usage_patterns'].items():
            if calls and pattern != 'other':
                output.append(f"\n{pattern.upper().replace('_', ' ')}:")
                for call in calls[:max_samples]:
                    output.append(f"  {Path(call['file']).name}:{call['line_number']}")
                    highlighted = highlight_match(call['content'], call.get('match_positions', []))
                    output.append(f"    {highlighted}")
                if len(calls) > max_samples:
                    output.append(f"  ... and {len(calls) - max_samples} more")
    
    return '\n'.join(output)

def build_recursive_call_tree(target: str, scope: str, language: str, 
                             whole_word: bool, ignore_case: bool,
                             max_depth: int, current_depth: int = 0,
                             seen_targets: Optional[set] = None) -> Dict:
    """
    Recursively builds a call tree by finding callers of callers.
    
    Args:
        target: The method/class to analyze.
        scope: Directory to search.
        language: Programming language filter.
        whole_word: Whether to match whole words only.
        ignore_case: Whether to ignore case.
        max_depth: Maximum recursion depth.
        current_depth: Current recursion depth.
        seen_targets: Set of already analyzed targets to prevent cycles.
        
    Returns:
        Dictionary representing the call tree.
    """
    if seen_targets is None:
        seen_targets = set()
    
    # Prevent infinite recursion
    if current_depth >= max_depth or target in seen_targets:
        return {'target': target, 'depth': current_depth, 'truncated': True}
    
    seen_targets.add(target)
    
    # Find all callers of this target
    search_results = find_all_callers(target, scope, language, whole_word, ignore_case)
    callers = parse_caller_results(search_results)
    
    # Separate definitions from usages
    definitions = [c for c in callers if c.get('is_definition', False)]
    usages = [c for c in callers if not c.get('is_definition', False)]
    
    # Build node
    node = {
        'target': target,
        'depth': current_depth,
        'total_references': len(callers),
        'definitions': len(definitions),
        'usages': len(usages),
        'callers': []
    }
    
    # Extract unique caller functions (simplified extraction)
    caller_functions = set()
    for usage in usages:
        # Try to extract the enclosing function name
        # This is a simplified heuristic - could be enhanced
        content = usage['content']
        # Look for function names before the target
        match = re.search(r'\b(\w+)\s*\([^)]*\b' + re.escape(target), content)
        if match and match.group(1) != target:
            caller_functions.add(match.group(1))
    
    # Recursively analyze each caller function
    for caller_func in list(caller_functions)[:5]:  # Limit to 5 callers per level
        if caller_func not in seen_targets:
            child_node = build_recursive_call_tree(
                caller_func, scope, language, whole_word, ignore_case,
                max_depth, current_depth + 1, seen_targets
            )
            node['callers'].append(child_node)
    
    return node

def format_call_tree(tree: Dict, indent: str = "") -> str:
    """
    Formats a call tree for display.
    
    Args:
        tree: The call tree dictionary.
        indent: Current indentation level.
        
    Returns:
        Formatted string representation.
    """
    output = []
    
    # Format current node
    truncated = " [TRUNCATED]" if tree.get('truncated', False) else ""
    refs = f"({tree.get('usages', 0)} usages, {tree.get('definitions', 0)} defs)"
    output.append(f"{indent}└─ {tree['target']} {refs}{truncated}")
    
    # Format children
    for i, child in enumerate(tree.get('callers', [])):
        is_last = i == len(tree['callers']) - 1
        child_indent = indent + ("   " if is_last else "│  ")
        output.extend(format_call_tree(child, child_indent).split('\n'))
    
    return '\n'.join(output).rstrip()

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Cross-file dependency analysis - Find all callers of methods or classes')
    else:
        parser = argparse.ArgumentParser(
            description='''Cross-file dependency analysis - Find all callers of methods or classes

Examples:
  # Find all usages of sendOrder method
  ./run_any_python_tool.sh cross_file_analysis.py sendOrder --scope src/ --language java
  
  # Find class instantiations  
  # Case-insensitive search  
  # With usage analysis  
  # Output as JSON  
  # Recursive call tree analysis  
  # Find definitions vs usages        ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
    
    parser.add_argument('target', help='Method or class name to find references for')
    
    # Search options
    parser.add_argument('--language', '--lang', choices=['python', 'java', 'javascript', 'cpp', 'go', 'rust'],
                       help='Filter by programming language')
    parser.add_argument('--no-whole-word', action='store_true', 
                       help='Don\'t require whole word matching')
    # Analysis options
    parser.add_argument('--analyze', action='store_true',
                       help='Perform usage frequency and pattern analysis')
    parser.add_argument('--show-samples', action='store_true', default=True,
                       help='Show sample usage patterns (default: true)')
    parser.add_argument('--max-samples', type=int, default=3,
                       help='Maximum samples per pattern (default: 3)')
    
    # Output options
    args = parser.parse_args()
    
    try:
        # Find all callers
        if not args.quiet:
            print(f"Searching for references to '{args.target}'...", file=sys.stderr)
        
        search_results = find_all_callers(
            args.target, 
            args.scope, 
            args.language,
            whole_word=not args.no_whole_word,
            ignore_case=args.ignore_case
        )
        
        # Parse results
        callers = parse_caller_results(search_results)
        
        if not callers:
            print(f"No references found for '{args.target}'")
            sys.exit(0)
        
        # Handle recursive analysis
        if args.recursive:
            if not args.quiet:
                print(f"Building recursive call tree (max depth: {args.max_depth})...", file=sys.stderr)
            
            call_tree = build_recursive_call_tree(
                args.target, args.scope, args.language,
                whole_word=not args.no_whole_word,
                ignore_case=args.ignore_case,
                max_depth=args.max_depth
            )
            
            if args.json:
                print(json.dumps(call_tree, indent=2))
            else:
                print(f"\n🌳 RECURSIVE CALL TREE for '{args.target}'")
                print("=" * 60)
                print(format_call_tree(call_tree))
                print("\nNote: Shows up to 5 callers per function, max depth: " + str(args.max_depth))
            sys.exit(0)
        
        # Output based on mode
        if args.json:
            if args.analyze:
                analysis = analyze_method_usage(callers, args.target)
                # Convert Counter objects to dicts for JSON serialization
                analysis['by_file'] = dict(analysis['by_file'])
                analysis['calling_contexts'] = dict(analysis['calling_contexts'])
                # Don't include full usage_patterns in JSON (too verbose)
                analysis.pop('usage_patterns', None)
                output = {
                    'analysis': analysis,
                    'callers': callers
                }
            else:
                output = {'callers': callers}
            
            print(json.dumps(output, indent=2))
        
        elif args.analyze:
            # Perform analysis and show report
            analysis = analyze_method_usage(callers, args.target)
            report = format_analysis_report(analysis, args.show_samples, args.max_samples)
            print(report)
        
        else:
            # Simple list of callers
            definitions = [c for c in callers if c.get('is_definition', False)]
            usages = [c for c in callers if not c.get('is_definition', False)]
            
            print(f"Found {len(callers)} reference(s) to '{args.target}':")
            if definitions:
                print(f"  {len(definitions)} definition(s)")
            if usages:
                print(f"  {len(usages)} usage(s)\n")
            
            # Show definitions first
            if definitions:
                print("DEFINITIONS:")
                for defn in definitions:
                    print(f"{defn['file']}:{defn['line_number']}")
                    if not args.quiet:
                        highlighted = highlight_match(defn['content'], defn.get('match_positions', []))
                        print(f"  {highlighted}")
                print()
            
            # Show usages
            if usages:
                print("USAGES:")
                for caller in usages:
                    print(f"{caller['file']}:{caller['line_number']}")
                    if not args.quiet:
                        highlighted = highlight_match(caller['content'], caller.get('match_positions', []))
                        print(f"  {highlighted}\n")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()