#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Multi-file correlation analysis tool for finding cross-file dependencies,

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
import shutil
from pathlib import Path
from collections import defaultdict, Counter
import json
from datetime import datetime
import os

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
        def check_ripgrep_installed():
            return True, ""
        @staticmethod
        def check_directory_accessible(path):
            return True, ""

def check_ripgrep():
    """Check if ripgrep is installed and suggest installation."""
    if not shutil.which('rg'):
        print("Error: ripgrep (rg) is not installed or not in your PATH.", file=sys.stderr)
        print("ripgrep is a prerequisite for this script.", file=sys.stderr)
        print("Please install it from: https://github.com/BurntSushi/ripgrep#installation", file=sys.stderr)
        sys.exit(1)

def find_all_callers(target, scope=".", language=None, include_logs=False):
    """Find all files and locations that call/reference the target using ripgrep's JSON output."""
    check_ripgrep()
    
    cmd = ['rg', '--json', '-C', '2']
    
    if language:
        cmd.extend(['-t', language])
    
    # Include common log file extensions if requested
    if include_logs:
        cmd.extend(['-g', '*.log', '-g', '*.txt'])
    
    # Search for the target as a whole word
    cmd.extend(['-w', target, scope])
    
    try:
        # Use a longer timeout for potentially large scopes
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        # rg with --json does not have a non-zero exit code for "no matches found"
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Search timed out for target: {target}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"An error occurred while running ripgrep: {e}", file=sys.stderr)
        return ""

def parse_caller_results(output, target):
    """Parse ripgrep's JSON output to extract caller information."""
    callers = []
    
    for line in output.strip().split('\n'):
        try:
            data = json.loads(line)
            if data['type'] == 'match':
                match_data = data['data']
                file_path = match_data['path']['text']
                
                callers.append({
                    'file': file_path,
                    'line': match_data['line_number'],
                    'content': match_data['lines']['text'].strip(),
                    'context': [ctx['text'].strip() for ctx in match_data.get('context', [])],
                    'language': detect_language(file_path),
                    'file_type': classify_file_type(file_path)
                })
        except (json.JSONDecodeError, KeyError) as e:
            # Ignore begin/end messages or malformed lines
            if data.get('type') not in ['begin', 'end', 'summary']:
                print(f"Warning: Could not parse JSON line: {line.strip()}", file=sys.stderr)
    
    return callers

def detect_language(file_path):
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.java': 'java',
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.log': 'log',
        '.txt': 'text',
        '.md': 'markdown',
        '.xml': 'xml',
        '.json': 'json',
        '.properties': 'properties'
    }
    return lang_map.get(ext, 'unknown')

def classify_file_type(file_path):
    """Classify file as source, test, config, or log."""
    path_str = str(file_path).lower()
    
    if 'test' in path_str or path_str.endswith('test.java') or path_str.endswith('test.py'):
        return 'test'
    elif any(ext in path_str for ext in ['.log', '.txt']):
        return 'log'
    elif any(ext in path_str for ext in ['.xml', '.properties', '.json', '.yml', '.yaml']):
        return 'config'
    elif 'src/main' in path_str:
        return 'source'
    else:
        return 'other'

def analyze_call_patterns(callers, target):
    """Analyze patterns in how the target is called."""
    analysis = {
        'total_calls': len(callers),
        'by_file_type': defaultdict(int),
        'by_language': defaultdict(int),
        'by_file': defaultdict(int),
        'call_contexts': Counter(),
        'frequent_files': Counter(),
        'method_patterns': Counter(),
        'temporal_patterns': defaultdict(list)
    }
    
    for caller in callers:
        analysis['by_file_type'][caller['file_type']] += 1
        analysis['by_language'][caller['language']] += 1
        analysis['by_file'][caller['file']] += 1
        analysis['frequent_files'][caller['file']] += 1
        
        # Analyze calling context
        content = caller['content'].lower()
        
        # Analyze calling context
        content = caller['content'].lower()
        target_lower = target.lower()
        
        # Method call patterns
        if f'{target_lower}(' in content:
            analysis['method_patterns']['method_call'] += 1
        if f'new {target_lower}' in content:
            analysis['method_patterns']['constructor'] += 1
        if f'.{target_lower}' in content:
            analysis['method_patterns']['object_method'] += 1
        
        # Context patterns
        if any(keyword in content for keyword in ['if ', 'when ', 'unless ']):
            analysis['call_contexts']['conditional'] += 1
        if any(keyword in content for keyword in ['for ', 'while ', 'loop ']):
            analysis['call_contexts']['loop'] += 1
        if any(keyword in content for keyword in ['try ', 'catch ', 'except ']):
            analysis['call_contexts']['exception_handling'] += 1
        if any(keyword in content for keyword in ['log.', 'print(', 'debug(']):
            analysis['call_contexts']['logging'] += 1
        if 'return ' in content:
            analysis['call_contexts']['return_value'] += 1
        
        # Try to extract timestamp for temporal analysis (for log files)
        if caller['file_type'] == 'log':
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[\s_T]\d{2}:\d{2}:\d{2})', caller['content'])
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                analysis['temporal_patterns'][timestamp[:10]].append(caller)  # Group by date
    
    return analysis

def find_dependencies(target, scope=".", max_depth=3):
    """Find what the target depends on (what it calls)."""
    check_ripgrep()
    
    # First find the definition file(s)
    definition_cmd = ['rg', '-n', '--color=never', '-t', 'java', '-t', 'py']
    definition_cmd.extend([rf'(class|def|function|interface)\s+{re.escape(target)}\b', scope])
    
    try:
        result = subprocess.run(definition_cmd, capture_output=True, text=True, timeout=30)
        definition_files = []
        
        for line in result.stdout.split('\n'):
            if line.strip():
                match = re.match(r'^([^:]+):', line)
                if match:
                    definition_files.append(match.group(1))
        
        # Now analyze what these files call
        dependencies = defaultdict(set)
        for def_file in definition_files[:5]:  # Limit to first 5 definition files
            deps = extract_dependencies_from_file(def_file, max_depth)
            for dep_type, dep_set in deps.items():
                dependencies[dep_type].update(dep_set)
        
        return dict(dependencies)
    
    except subprocess.TimeoutExpired:
        print(f"Dependency search timed out for: {target}", file=sys.stderr)
        return {}

def extract_dependencies_from_file(file_path, max_depth=3):
    """Extract dependencies from a specific file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        dependencies = {
            'methods': set(),
            'classes': set(),
            'imports': set(),
            'fields': set()
        }
        
        language = detect_language(file_path)
        
        if language == 'java':
            # Find method calls
            method_calls = re.findall(r'\.(\w+)\s*\(', content)
            dependencies['methods'].update(method_calls)
            
            # Find class usage
            class_usage = re.findall(r'new\s+(\w+)\s*\(', content)
            dependencies['classes'].update(class_usage)
            
            # Find imports
            imports = re.findall(r'import\s+[\w.]+\.(\w+);', content)
            dependencies['imports'].update(imports)
            
            # Find field access
            field_access = re.findall(r'this\.(\w+)', content)
            dependencies['fields'].update(field_access)
        
        elif language == 'python':
            # Find function calls
            function_calls = re.findall(r'(\w+)\s*\(', content)
            dependencies['methods'].update(function_calls)
            
            # Find class usage
            class_usage = re.findall(r'(\w+)\s*\(', content)  # Python constructors
            dependencies['classes'].update(class_usage)
            
            # Find imports
            imports = re.findall(r'from\s+[\w.]+\s+import\s+(\w+)', content)
            imports.extend(re.findall(r'import\s+(\w+)', content))
            dependencies['imports'].update(imports)
        
        # Filter out common/built-in items
        for dep_type in dependencies:
            dependencies[dep_type] = {
                dep for dep in dependencies[dep_type] 
                if len(dep) > 2 and not dep.lower() in {'get', 'set', 'new', 'this', 'if', 'for', 'int', 'str', 'list', 'dict'}
            }
        
        return dependencies
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return {'methods': set(), 'classes': set(), 'imports': set(), 'fields': set()}

def format_usage_analysis(callers, analysis, dependencies=None, show_frequency=True, 
                         show_files=True, show_patterns=True, max_entries=None):
    """Format the usage analysis results."""
    output = []
    
    # Header
    output.append("=" * 80)
    output.append(f"USAGE ANALYSIS RESULTS")
    output.append("=" * 80)
    output.append(f"Total references found: {analysis['total_calls']}")
    
    # Frequency analysis
    if show_frequency and analysis['total_calls'] > 0:
        output.append(f"\n📊 FREQUENCY ANALYSIS")
        output.append("-" * 40)
        
        output.append(f"\nBy file type:")
        for file_type, count in sorted(analysis['by_file_type'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / analysis['total_calls']) * 100
            output.append(f"  {file_type:12} {count:4d} ({percentage:5.1f}%)")
        
        output.append(f"\nBy language:")
        for lang, count in sorted(analysis['by_language'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / analysis['total_calls']) * 100
            output.append(f"  {lang:12} {count:4d} ({percentage:5.1f}%)")
        
        output.append(f"\nTop calling files:")
        for file_path, count in analysis['frequent_files'].most_common(10):
            output.append(f"  {count:3d}x {file_path}")
    
    # Pattern analysis
    if show_patterns and (analysis['call_contexts'] or analysis['method_patterns']):
        output.append(f"\n🔍 PATTERN ANALYSIS")
        output.append("-" * 40)
        
        if analysis['method_patterns']:
            output.append(f"\nCall patterns:")
            for pattern, count in analysis['method_patterns'].most_common():
                output.append(f"  {pattern:20} {count:4d}")
        
        if analysis['call_contexts']:
            output.append(f"\nContext patterns:")
            for context, count in analysis['call_contexts'].most_common():
                output.append(f"  {context:20} {count:4d}")
    
    # Dependencies
    if dependencies:
        output.append(f"\n🔗 DEPENDENCY ANALYSIS")
        output.append("-" * 40)
        
        for dep_type, deps in dependencies.items():
            if deps:
                output.append(f"\n{dep_type.title()}:")
                for dep in sorted(list(deps)[:10]):  # Show top 10
                    output.append(f"  {dep}")
    
    # Temporal patterns (for logs)
    if analysis['temporal_patterns']:
        output.append(f"\n📅 TEMPORAL PATTERNS")
        output.append("-" * 40)
        for date, entries in sorted(analysis['temporal_patterns'].items()):
            output.append(f"  {date}: {len(entries)} occurrences")
    
    # File listings
    if show_files:
        output.append(f"\n📁 DETAILED REFERENCES")
        output.append("-" * 40)
        
        # Group by file type
        by_type = defaultdict(list)
        for caller in callers:
            by_type[caller['file_type']].append(caller)
        
        for file_type, type_callers in sorted(by_type.items()):
            if max_entries and len(type_callers) > max_entries:
                type_callers = type_callers[:max_entries]
                truncated = len(by_type[file_type]) - max_entries
            else:
                truncated = 0
            
            output.append(f"\n{file_type.upper()} FILES:")
            for caller in type_callers:
                output.append(f"  {caller['file']}:{caller['line']}")
                output.append(f"    >>> {caller['content']}")
                if caller['context']:
                    for ctx in caller['context'][-1:]:  # Show last context line
                        output.append(f"        {ctx}")
            
            if truncated > 0:
                output.append(f"    ... and {truncated} more references")
    
    return '\n'.join(output)

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Multi-file correlation analysis for finding cross-file dependencies and usage patterns')
    else:
        parser = argparse.ArgumentParser(
            description='Multi-file correlation analysis for finding cross-file dependencies and usage patterns',
            epilog='''
EXAMPLES:
  # Find all callers with frequency analysis  
  # Analyze method usage patterns  
  # Cross-dependency analysis  
  # Log file analysis with temporal patterns  
  # Complete analysis with all features            ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
    
    # Add tool-specific arguments
    if not HAS_STANDARD_PARSER:
        parser.add_argument('target', help='Method, class, or pattern to analyze')
    
    # Analysis types
    parser.add_argument('--find-all-callers', action='store_true', default=True,
                       help='Find all files that reference the target (default: true)')
    parser.add_argument('--find-dependencies', action='store_true',
                       help='Find what the target depends on')
    parser.add_argument('--include-logs', action='store_true',
                       help='Include log files in analysis')
    
    # Language filtering
    parser.add_argument('--java-only', action='store_true', help='Search only Java files')
    parser.add_argument('--python-only', action='store_true', help='Search only Python files')
    parser.add_argument('--language', help='Specify language filter')
    
    # Display options
    parser.add_argument('--show-frequency', action='store_true', default=True,
                       help='Show frequency analysis (default: true)')
    parser.add_argument('--show-patterns', action='store_true', default=True,
                       help='Show usage patterns (default: true)')
    parser.add_argument('--show-files', action='store_true', default=True,
                       help='Show detailed file references (default: true)')
    parser.add_argument('--show-all', action='store_true',
                       help='Enable all display options')
    
    # Control options
    parser.add_argument('--max-entries', type=int,
                       help='Maximum entries to show per section')
    
    # Output options
    parser.add_argument('--summary-only', action='store_true',
                       help='Show only summary statistics')
    
    args = parser.parse_args()
    
    # Handle target mapping for standard parser compatibility
    target = getattr(args, 'target', getattr(args, 'pattern', None))
    if not target:
        print('Error: Target pattern required', file=sys.stderr)
        sys.exit(1)
    
    # Run preflight checks
    checks = [
        (PreflightChecker.check_ripgrep_installed, ()),
        (PreflightChecker.check_directory_accessible, (args.scope,))
    ]
    run_preflight_checks(checks)
    
    # Handle language flags
    if args.java_only:
        args.language = 'java'
    elif args.python_only:
        args.language = 'python'
    
    # Handle show-all flag
    if args.show_all:
        args.show_frequency = True
        args.show_patterns = True
        args.show_files = True
        args.find_dependencies = True
    
    # Summary-only overrides other display options
    if args.summary_only:
        args.show_files = False
    
    try:
        # Find all callers
        if args.find_all_callers:
            caller_output = find_all_callers(target, args.scope, args.language, args.include_logs)
            callers = parse_caller_results(caller_output, target)
            analysis = analyze_call_patterns(callers, target)
        else:
            callers = []
            analysis = {'total_calls': 0}
        
        # Find dependencies
        dependencies = None
        if args.find_dependencies:
            dependencies = find_dependencies(target, args.scope, args.max_depth)
        
        # Output results
        if args.json:
            json_output = {
                'target': target,
                'analysis': analysis,
                'dependencies': dependencies,
                'callers': [
                    {
                        'file': c['file'],
                        'line': c['line'], 
                        'content': c['content'],
                        'language': c['language'],
                        'file_type': c['file_type']
                    } for c in callers
                ] if not args.summary_only else []
            }
            print(json.dumps(json_output, indent=2, default=str))
        else:
            formatted_results = format_usage_analysis(
                callers, analysis, dependencies,
                args.show_frequency, args.show_files, args.show_patterns,
                args.max_entries
            )
            print(formatted_results)
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()