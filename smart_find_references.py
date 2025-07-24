#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Smart code-aware search tool for finding references with enhanced context and analysis.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import subprocess
from pathlib import Path
import argparse
import shutil
from collections import defaultdict, Counter
import json

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

def check_ripgrep():
    """Check if ripgrep is installed and suggest installation."""
    if not shutil.which('rg'):
        print("Error: ripgrep (rg) is not installed or not in your PATH.", file=sys.stderr)
        print("ripgrep is a prerequisite for this script.", file=sys.stderr)
        print("Please install it from: https://github.com/BurntSushi/ripgrep#installation", file=sys.stderr)
        sys.exit(1)

def detect_language(file_path):
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.java': 'java',
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php'
    }
    return lang_map.get(ext, 'unknown')

def build_java_patterns(target_name, pattern_type):
    """Build Java-specific search patterns."""
    patterns = {}
    
    if pattern_type in ['method', 'auto']:
        patterns['method_calls'] = [
            rf'\b{re.escape(target_name)}\s*\(',  # Method calls
            rf'\.{re.escape(target_name)}\s*\(',  # Object method calls
        ]
        patterns['method_definitions'] = [
            rf'(public|private|protected).*\b{re.escape(target_name)}\s*\(',  # Method declarations
            rf'^\s*\w+.*\b{re.escape(target_name)}\s*\(',  # Simple method declarations
        ]
    
    if pattern_type in ['field', 'auto']:
        patterns['field_access'] = [
            rf'\b{re.escape(target_name)}\b',  # Field access
            rf'\.{re.escape(target_name)}\b',  # Object field access
        ]
        patterns['field_definitions'] = [
            rf'(public|private|protected).*\b{re.escape(target_name)}\s*[=;]',  # Field declarations
            rf'^\s*(static\s+)?(final\s+)?\w+\s+{re.escape(target_name)}\s*[=;]',  # Simple field declarations
        ]
    
    if pattern_type in ['class', 'auto']:
        patterns['class_usage'] = [
            rf'\bnew\s+{re.escape(target_name)}\s*\(',  # Constructor calls
            rf'\b{re.escape(target_name)}\s+\w+',  # Variable declarations
            rf'extends\s+{re.escape(target_name)}\b',  # Inheritance
            rf'implements\s+{re.escape(target_name)}\b',  # Interface implementation
        ]
        patterns['class_definitions'] = [
            rf'(public\s+)?(class|interface|enum)\s+{re.escape(target_name)}\b',  # Class/interface declarations
        ]
    
    return patterns

def build_python_patterns(target_name, pattern_type):
    """Build Python-specific search patterns."""
    patterns = {}
    
    if pattern_type in ['method', 'function', 'auto']:
        patterns['function_calls'] = [
            rf'\b{re.escape(target_name)}\s*\(',  # Function calls
            rf'\.{re.escape(target_name)}\s*\(',  # Method calls
        ]
        patterns['function_definitions'] = [
            rf'def\s+{re.escape(target_name)}\s*\(',  # Function definitions
        ]
    
    if pattern_type in ['class', 'auto']:
        patterns['class_usage'] = [
            rf'\b{re.escape(target_name)}\s*\(',  # Constructor calls
            rf':\s*{re.escape(target_name)}\b',  # Type hints
            rf'isinstance\s*\(.*,\s*{re.escape(target_name)}\)',  # isinstance checks
        ]
        patterns['class_definitions'] = [
            rf'class\s+{re.escape(target_name)}\s*[\(:]',  # Class definitions
        ]
    
    return patterns

def execute_search(pattern, scope, language_filter=None, context_lines=3, ignore_case=False):
    """Execute ripgrep search with given pattern and get JSON output."""
    cmd = ['rg', '--json', '--no-heading']
    
    if ignore_case:
        cmd.append('--ignore-case')
    
    if context_lines > 0:
        cmd.extend(['--context', str(context_lines)])
    
    if language_filter:
        cmd.extend(['-t', language_filter])
    
    # Use -E to ensure the pattern is treated as a regex
    cmd.extend(['-E', pattern, scope])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Search timed out for pattern: {pattern}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"An error occurred while running ripgrep: {e}", file=sys.stderr)
        return ""

def parse_search_results(output, pattern_type):
    """Parse ripgrep's JSON output stream into structured results."""
    results = []
    
    for line in output.split('\n'):
        if not line.strip():
            continue
            
        # Match file:line:content format
        try:
            data = json.loads(line)
            if data['type'] == 'match':
                match_data = data['data']
                file_path = match_data['path']['text']
                results.append({
                    'file': file_path,
                    'line': match_data['line_number'],
                    'content': match_data['lines']['text'].strip(),
                    'language': detect_language(file_path),
                    'pattern_type': pattern_type,
                    'context_before': [ctx['text'].strip() for ctx in match_data.get('context', []) if ctx['line_number'] < match_data['line_number']],
                    'context_after': [ctx['text'].strip() for ctx in match_data.get('context', []) if ctx['line_number'] > match_data['line_number']]
                })
        except (json.JSONDecodeError, KeyError):
            # Ignore begin/end/summary messages and malformed lines
            continue
    
    return results

def analyze_results(results, target_name):
    """Analyze search results to provide insights."""
    analysis = {
        'total_references': len(results),
        'by_file': defaultdict(int),
        'by_language': defaultdict(int),
        'by_pattern_type': defaultdict(int),
        'frequent_contexts': Counter(),
        'call_patterns': Counter(),
        'definition_files': set()
    }
    
    for result in results:
        analysis['by_file'][result['file']] += 1
        analysis['by_language'][result['language']] += 1
        analysis['by_pattern_type'][result['pattern_type']] += 1
        
        # Extract call patterns for methods
        if 'call' in result['pattern_type'] or 'method' in result['pattern_type']:
            # Look for common calling patterns
            content = result['content'].lower()
            if 'if' in content:
                analysis['call_patterns']['conditional'] += 1
            if 'for' in content or 'while' in content:
                analysis['call_patterns']['loop'] += 1
            if 'try' in content or 'catch' in content:
                analysis['call_patterns']['exception_handling'] += 1
        
        # Track definition files
        if 'definition' in result['pattern_type']:
            analysis['definition_files'].add(result['file'])
    
    return analysis

def format_results(results, analysis, show_analysis=True, show_context=True, 
                  group_by_file=False, max_results=None):
    """Format results for display."""
    if max_results:
        results = results[:max_results]
    
    output = []
    
    # Summary
    output.append("=" * 80)
    output.append(f"SMART SEARCH RESULTS")
    output.append("=" * 80)
    output.append(f"Found {analysis['total_references']} references")
    
    if show_analysis and analysis['total_references'] > 0:
        output.append(f"\nBreakdown by type:")
        for pattern_type, count in sorted(analysis['by_pattern_type'].items()):
            output.append(f"  {pattern_type}: {count}")
        
        output.append(f"\nBreakdown by language:")
        for lang, count in sorted(analysis['by_language'].items()):
            output.append(f"  {lang}: {count}")
        
        if analysis['definition_files']:
            output.append(f"\nDefinitions found in:")
            for def_file in sorted(analysis['definition_files']):
                output.append(f"  {def_file}")
        
        if analysis['call_patterns']:
            output.append(f"\nCall patterns:")
            for pattern, count in analysis['call_patterns'].most_common(5):
                output.append(f"  {pattern}: {count}")
    
    # Group results
    if group_by_file:
        file_groups = defaultdict(list)
        for result in results:
            file_groups[result['file']].append(result)
        
        for file_path, file_results in sorted(file_groups.items()):
            output.append(f"\n{'='*20} {file_path} ({'='*20}")
            output.append(f"{len(file_results)} references")
            
            for result in file_results:
                output.append(f"\n  Line {result['line']} ({result['pattern_type']}):")
                if show_context and result['context_before']:
                    for ctx in result['context_before'][-2:]:  # Show last 2 context lines
                        output.append(f"    - {ctx}")
                
                output.append(f"    >>> {result['content']}")
                
                if show_context and result['context_after']:
                    for ctx in result['context_after'][:2]:  # Show first 2 context lines
                        output.append(f"    + {ctx}")
    else:
        # Show results grouped by type
        type_groups = defaultdict(list)
        for result in results:
            type_groups[result['pattern_type']].append(result)
        
        for pattern_type, type_results in sorted(type_groups.items()):
            output.append(f"\n{'='*15} {pattern_type.upper()} ({'='*15}")
            
            for result in type_results:
                output.append(f"\n{result['file']}:{result['line']}")
                
                if show_context and result['context_before']:
                    for ctx in result['context_before'][-1:]:
                        output.append(f"  - {ctx}")
                
                output.append(f"  >>> {result['content']}")
                
                if show_context and result['context_after']:
                    for ctx in result['context_after'][:1]:
                        output.append(f"  + {ctx}")
    
    return '\n'.join(output)

def smart_find_references(target_name, scope=".", ref_type="auto", language=None,
                         context_lines=3, ignore_case=False, show_calls=True,
                         show_definitions=True, show_analysis=True, group_by_file=False,
                         max_results=None):
    """Main function for smart reference finding."""
    check_ripgrep()
    
    def detect_primary_language(scan_scope):
        """Safely detect the dominant language using pathlib, avoiding shell=True."""
        try:
            p = Path(scan_scope)
            if not p.is_dir():
                return detect_language(str(p))
            
            # Limit scan to 1000 files for performance
            files = list(p.rglob("*"))[:1000]
            ext_counts = Counter(f.suffix for f in files if f.is_file())
            
            if ext_counts.get('.java', 0) > ext_counts.get('.py', 0):
                return 'java'
            if ext_counts.get('.py', 0) > 0:
                return 'python'
        except Exception as e:
            print(f"Language auto-detection failed: {e}", file=sys.stderr)
        return None

    all_results = []
    
    # Determine primary language if not specified
    if not language and scope != ".":
        # Sample files to detect predominant language
        language = detect_primary_language(scope)

    # Build patterns based on detected/specified language
    if language == 'java':
        patterns = build_java_patterns(target_name, ref_type)
        lang_filter = 'java'
    elif language == 'python':
        patterns = build_python_patterns(target_name, ref_type)
        lang_filter = 'py'
    else:
        # Generic patterns
        patterns = {
            'general_usage': [rf'\b{re.escape(target_name)}\b']
        }
        lang_filter = None
    
    # Execute searches
    for pattern_type, pattern_list in patterns.items():
        # Skip if user doesn't want certain types
        if not show_calls and ('call' in pattern_type or 'access' in pattern_type or 'usage' in pattern_type):
            continue
        if not show_definitions and 'definition' in pattern_type:
            continue
        
        for pattern in [p for p in pattern_list if p]: # Filter out empty patterns
            output = execute_search(pattern, scope, lang_filter, context_lines, ignore_case)
            if output:
                results = parse_search_results(output, pattern_type)
                all_results.extend(results)
    
    # Remove duplicates (same file:line)
    seen = set()
    unique_results = []
    for result in all_results:
        key = (result['file'], result['line'])
        if key not in seen:
            seen.add(key)
            unique_results.append(result)
    
    # Analyze and format results
    analysis = analyze_results(unique_results, target_name)
    formatted = format_results(unique_results, analysis, show_analysis, 
                              context_lines > 0, group_by_file, max_results)
    
    return formatted, analysis

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Smart code-aware search for finding references with enhanced context')
    else:
        parser = argparse.ArgumentParser(
            description='Smart code-aware search for finding references with enhanced context',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('target', help='Method, field, class, or pattern to search for')
    # Language and filtering
    parser.add_argument('--java-only', action='store_true', help='Search only Java files')
    parser.add_argument('--python-only', action='store_true', help='Search only Python files')
    parser.add_argument('--language', help='Specify language (java, python, etc.)')
    
    # What to show
    parser.add_argument('--show-calls', action='store_true', default=True,
                       help='Show method calls and usage (default: true)')
    parser.add_argument('--show-definitions', action='store_true', default=True,
                       help='Show definitions and declarations (default: true)')
    parser.add_argument('--no-calls', dest='show_calls', action='store_false',
                       help='Hide method calls and usage')
    parser.add_argument('--no-definitions', dest='show_definitions', action='store_false',
                       help='Hide definitions and declarations')
    
    # Display options
    parser.add_argument('--show-analysis', action='store_true', default=True,
                       help='Show analysis and patterns (default: true)')
    parser.add_argument('--no-analysis', dest='show_analysis', action='store_false',
                       help='Hide analysis and patterns')
    parser.add_argument('--group-by-file', action='store_true',
                       help='Group results by file instead of by type')
    parser.add_argument('--max-results', type=int,
                       help='Maximum number of results to show')
    
    # Search options
    # Output options
    args = parser.parse_args()
    
    # Handle language flags
    if args.java_only:
        args.language = 'java'
    elif args.python_only:
        args.language = 'python'
    
    try:
        formatted_results, analysis = smart_find_references(
            args.target, args.scope, args.type, args.language,
            args.context, args.ignore_case, args.show_calls,
            args.show_definitions, args.show_analysis, args.group_by_file,
            args.max_results
        )
        
        if args.json:
            # Convert set to list for JSON serialization
            analysis['definition_files'] = list(analysis.get('definition_files', []))
            print(json.dumps(analysis, indent=2, default=str))
        else:
            print(formatted_results)
    
    except KeyboardInterrupt:
        print("\nSearch interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()