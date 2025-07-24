#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Comprehensive method analyzer for usage analysis, parameter tracking, and flow tracing.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict, Counter
import json

# Import common utilities

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
    # Prefer shared library if available
    from common_utils import check_ripgrep, detect_language, add_common_args
except ImportError:
    # ── minimal in-file fall-backs ────────────────────────────────────
    import shutil
    def check_ripgrep():
        if not shutil.which("rg"):
            print("Error: ripgrep (rg) is not installed.", file=sys.stderr)
            sys.exit(1)
    def detect_language(path):
        return Path(path).suffix.lstrip(".")
    def add_common_args(parser, *flags):  # no-op shim
        return parser

def find_method_calls(method_name, scope=".", language="java"):
    """Find all calls to a specific method using ripgrep's JSON output."""
    check_ripgrep()
    
    # Pattern to find method calls like .method(...) or method(...)
    # Note: For ripgrep, we need proper escaping for special regex chars in method names
    escaped_name = re.escape(method_name)
    pattern = rf'\b{escaped_name}\s*\('
    cmd = ['rg', '--json', '-C', '1', '-t', language, pattern, scope]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        # ripgrep returns exit code 0 for matches, 1 for no matches, 2+ for errors
        if result.returncode >= 2:
            print(f"ripgrep error: {result.stderr}", file=sys.stderr)
            return []
        # Debug: print if we got output
        if result.stdout and result.stdout.strip():
            return parse_method_calls(result.stdout, method_name)
        return []
    except subprocess.TimeoutExpired:
        print(f"Search timed out for method: {method_name}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"An error occurred running ripgrep: {e}", file=sys.stderr)
        return []

def parse_method_calls(output, method_name):
    """Parse ripgrep's JSON output for method calls."""
    calls = []
    for line in output.split('\n'):
        if not line:
            continue
        try:
            data = json.loads(line)
            if data['type'] == 'match':
                match_data = data['data']
                content = match_data['lines']['text'].strip()
                # Ensure this is a call, not a definition
                # Check for method definitions (void/int/String/etc before method name)
                definition_pattern = rf'(public|private|protected|static|final|void|int|boolean|String|double|float|def)\s+{re.escape(method_name)}\s*\('
                if not re.search(definition_pattern, content):
                    calls.append({
                        'file': match_data['path']['text'],
                        'line': match_data['line_number'],
                        'content': content,
                        'parameters': extract_call_parameters(content, method_name),
                    })
        except (json.JSONDecodeError, KeyError):
            continue
    return calls

def extract_call_parameters(line, method_name):
    """
    Extract parameters from a method call string.
    Note: This is a best-effort regex and may fail on complex nested calls.
    """
    # Find content within the parentheses of the method call
    match = re.search(rf'{re.escape(method_name)}\s*\((.*?)\)', line)
    
    if match:
        params_str = match.group(1).strip()
        if not params_str:
            return []
        
        # Simple split by comma; will not handle commas within arguments correctly.
        return [p.strip() for p in params_str.split(',') if p.strip()]
    
    return []

def analyze_method_usage(calls):
    """Analyze method usage patterns."""
    analysis = {
        'total_calls': len(calls),
        'by_file': Counter(),
        'by_parameter_count': Counter(),
        'parameter_patterns': Counter(),
        'common_parameters': Counter(),
        'calling_contexts': Counter()
    }
    
    for call in calls:
        analysis['by_file'][call['file']] += 1
        analysis['by_parameter_count'][len(call['parameters'])] += 1
        
        # Analyze parameters
        for param in call['parameters']:
            analysis['common_parameters'][param.strip()] += 1
            
            # Parameter pattern analysis
            if param.strip().startswith('"'):
                analysis['parameter_patterns']['string_literal'] += 1
            elif param.strip().isdigit():
                analysis['parameter_patterns']['numeric_literal'] += 1
            elif '.' in param:
                analysis['parameter_patterns']['object_reference'] += 1
            elif param.strip() in ['true', 'false']:
                analysis['parameter_patterns']['boolean'] += 1
            else:
                analysis['parameter_patterns']['variable'] += 1
        
        # Analyze calling context
        content = call['content'].lower()
        if 'if' in content:
            analysis['calling_contexts']['conditional'] += 1
        if 'for' in content or 'while' in content:
            analysis['calling_contexts']['loop'] += 1
        if 'try' in content:
            analysis['calling_contexts']['exception_handling'] += 1
        if 'return' in content:
            analysis['calling_contexts']['return_statement'] += 1
    
    return analysis

def trace_method_flow(method_name, scope=".", language="java", max_depth=3):
    """
    Recursively trace method call flow to understand dependencies.
    """
    check_ripgrep()
    
    # Memoization to avoid re-tracing and handle recursion
    traced_methods = {}

    def trace(target_method, current_depth):
        if current_depth > max_depth or target_method in traced_methods:
            return []

        # Mark as traced to prevent cycles
        traced_methods[target_method] = []

        # Find the definition of the current method to analyze its body
        def_pattern = rf'(?:def|void|int|String|boolean|double|static|final|public|private|protected).*\s+{re.escape(target_method)}\s*\('
        def_files = find_definition_files(target_method, scope, language, def_pattern)

        if not def_files:
            return []
        
        # Analyze the first definition file found
        callees = extract_method_calls_from_file(def_files[0], target_method)

        # Recurse
        flow = []
        # Limit recursion to avoid explosion
        for callee in sorted(list(callees))[:10]: 
            flow.append({
                'method': callee,
                'depth': current_depth,
                'children': trace(callee, current_depth + 1)
            })
        
        traced_methods[target_method] = flow
        return flow

    # Start the trace from the root method
    return {'root_method': method_name, 'flow': trace(method_name, 1)}

def find_definition_files(method_name, scope, language, pattern):
    """Find file(s) where a method is defined."""
    check_ripgrep()
    cmd = ['rg', '-l', '-t', language, pattern, scope]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=15, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    except subprocess.CalledProcessError as e:
        print(f"ripgrep failed: {e}", file=sys.stderr)
        return []

def extract_method_calls_from_file(file_path, current_method_name):
    """Extract method calls from a specific file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find method calls in the file
        method_calls = re.findall(r'(\w+)\s*\(', content)
        
        # Filter out common keywords, constructors, and the method itself
        keywords = {
            'if', 'for', 'while', 'new', 'this', 'super', 'return',
            'System', 'String', 'Integer', 'Double', 'Boolean', 'assert',
            'catch', 'switch', current_method_name
        }
        filtered_calls = [
            call for call in method_calls 
            if len(call) > 2 and call not in keywords and not call[0].isupper()
        ]
        
        return list(set(filtered_calls))
    except Exception:
        return []

def format_flow(flow_tree, indent=0):
    """Format the method flow tree for display."""
    lines = []
    prefix = "  " * indent
    if indent > 0:
        prefix += "└─ "
    
    for call in flow_tree:
        lines.append(f"{prefix}{call['method']}")
        if call.get('children'):
            lines.extend(format_flow(call['children'], indent + 1))
    return lines

def format_method_analysis(method_name, calls, analysis, flow=None):
    """Format method analysis results."""
    output = []
    
    # Header
    output.append("=" * 80)
    output.append(f"METHOD ANALYSIS: '{method_name}'")
    output.append("=" * 80)
    output.append(f"Total calls found: {analysis['total_calls']}")
    
    if analysis['total_calls'] == 0:
        output.append("\nNo calls found for this method.")
        return '\n'.join(output)
    
    # Usage frequency
    output.append(f"\n📊 USAGE FREQUENCY")
    output.append("-" * 40)
    output.append(f"Files using this method: {len(analysis['by_file'])}")
    
    output.append(f"\nTop calling files:")
    for file_path, count in analysis['by_file'].most_common(10):
        output.append(f"  {count:3d}x {file_path}")
    
    # Parameter analysis
    output.append(f"\n📋 PARAMETER ANALYSIS")
    output.append("-" * 40)
    
    if analysis['by_parameter_count']:
        output.append(f"Parameter count distribution:")
        for param_count, frequency in sorted(analysis['by_parameter_count'].items()):
            percentage = (frequency / analysis['total_calls']) * 100
            output.append(f"  {param_count} params: {frequency:3d} calls ({percentage:5.1f}%)")
    
    if analysis['parameter_patterns']:
        output.append(f"\nParameter patterns:")
        for pattern, count in analysis['parameter_patterns'].most_common():
            percentage = (count / sum(analysis['parameter_patterns'].values())) * 100
            output.append(f"  {pattern:20} {count:3d} ({percentage:5.1f}%)")
    
    if analysis['common_parameters']:
        output.append(f"\nMost common parameter values:")
        for param, count in analysis['common_parameters'].most_common(10):
            if len(param) < 50:  # Skip very long parameters
                output.append(f"  {param:30} {count:3d}")
    
    # Calling context
    if analysis['calling_contexts']:
        output.append(f"\n🔍 CALLING CONTEXTS")
        output.append("-" * 40)
        for context, count in analysis['calling_contexts'].most_common():
            percentage = (count / analysis['total_calls']) * 100
            output.append(f"  {context:20} {count:3d} ({percentage:5.1f}%)")
    
    # Flow analysis
    if flow:
        output.append(f"\n🔄 METHOD FLOW ANALYSIS")
        output.append("-" * 40)
        
        if flow and flow.get('flow'):
            output.append(f"\nMethods called by '{method_name}':")
            output.extend(format_flow(flow['flow']))
    
    # Sample calls
    output.append(f"\n📄 SAMPLE CALLS")
    output.append("-" * 40)
    
    for i, call in enumerate(calls[:5]):  # Show first 5 calls
        output.append(f"\n{i+1}. {call['file']}:{call['line']}")
        output.append(f"   {call['content']}")
        if call['parameters']:
            output.append(f"   Parameters: {', '.join(call['parameters'])}")
    
    if len(calls) > 5:
        output.append(f"\n... and {len(calls) - 5} more calls")
    
    return '\n'.join(output)

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Comprehensive method analysis for usage patterns and flow tracing')
    else:
        parser = argparse.ArgumentParser(
            description='''Comprehensive method analysis for usage patterns and flow tracing

Examples:
  # Basic method analysis
  ./run_any_python_tool.sh method_analyzer.py "executeComplexTransformation" --show-all-calls --show-parameters
  
  # Flow tracing with dependencies  
  # Parameter pattern analysis  
  # Cross-file usage analysis        ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
    
    # Note: 'target' positional argument is already added by standard analyze parser
    # Add common arguments - note: 'scope', 'json' and 'max-depth' are already added by standard parser
    add_common_args(parser, 'language', 'max_results', 'timeout')
    
    # Analysis options
    parser.add_argument('--show-all-calls', action='store_true', default=True,
                       help='Show all method calls (default: true)')
    parser.add_argument('--show-parameters', action='store_true', default=True,
                       help='Analyze method parameters (default: true)')
    parser.add_argument('--trace-flow', action='store_true',
                       help='Trace method call flow and dependencies')
    parser.add_argument('--parameter-patterns', action='store_true',
                       help='Analyze parameter usage patterns')
    parser.add_argument('--frequency-analysis', action='store_true',
                       help='Show detailed frequency analysis')
    
    # Language shortcuts (for backward compatibility)
    parser.add_argument('--java-only', action='store_true', help='Search only Java files')
    parser.add_argument('--python-only', action='store_true', help='Search only Python files')
    
    # Set default language if not using standard parser
    if not HAS_STANDARD_PARSER:
        parser.set_defaults(language='java')
    
    # Control options
    # Output options
    # Note: --max-results and --json-output are added via add_common_args above
    
    args = parser.parse_args()
    
    # Handle language defaults and shortcuts
    if not hasattr(args, 'language'):
        args.language = 'java'  # Default to Java if language not specified
    
    # Handle language flags
    if args.java_only:
        args.language = 'java'
    elif args.python_only:
        args.language = 'python'
    
    try:
        # Find method calls
        method_name = args.target  # Standard parser uses 'target' for the symbol name
        calls = find_method_calls(method_name, args.scope, args.language)
        
        # Limit results if requested
        if hasattr(args, 'max_results') and args.max_results:
            calls = calls[:args.max_results]
        
        # Analyze usage
        analysis = analyze_method_usage(calls)
        
        # Trace flow if requested
        flow = None
        if args.trace_flow:
            flow = trace_method_flow(method_name, args.scope, args.language, args.max_depth)
        
        # Output results
        if hasattr(args, 'json') and args.json:
            json_output = {
                'method_name': method_name,
                'analysis': {
                    'total_calls': analysis['total_calls'],
                    'by_file': dict(analysis['by_file']),
                    'parameter_patterns': dict(analysis['parameter_patterns']),
                    'calling_contexts': dict(analysis['calling_contexts'])
                },
                'flow': flow,
                'calls': [
                    {
                        'file': call['file'],
                        'line': call['line'],
                        'content': call['content'],
                        'parameters': call['parameters']
                    } for call in calls
                ]
            }
            print(json.dumps(json_output, indent=2, default=str))
        else:
            formatted_results = format_method_analysis(
                method_name, calls, analysis, flow
            )
            print(formatted_results)
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()