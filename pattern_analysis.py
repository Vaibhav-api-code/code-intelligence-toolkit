#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Pattern analysis tool with aggregation for finding patterns across files,

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
from datetime import datetime, timezone
import os

# Import standard argument parser
try:
    from enhanced_standard_arg_parser import create_standard_parser as create_parser
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

def search_pattern_with_ripgrep(pattern, scope=".", file_pattern="*", 
                               regex=True, ignore_case=False, context_lines=0):
    """Search for patterns using ripgrep and get JSON output."""
    check_ripgrep()
    
    cmd = ['rg', '--json']  # Enable JSON output
    
    if not regex:
        cmd.append('-F')  # Fixed string
    
    if ignore_case:
        cmd.append('-i')
    
    if context_lines > 0:
        cmd.extend(['-C', str(context_lines)])
    
    if file_pattern != "*":
        cmd.extend(['-g', file_pattern])
    
    # The pattern should be the second to last argument
    cmd.extend([pattern, scope])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Search timed out for pattern: {pattern}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"An error occurred while running ripgrep: {e}", file=sys.stderr)
        return ""

def parse_search_results(output, pattern):
    """Parse ripgrep's JSON output into structured results."""
    results = []
    
    for line in output.strip().split('\n'):
        if not line.strip():
            continue
        
        try:
            data = json.loads(line)
            if data['type'] == 'match':
                match_data = data['data']
                file_path = match_data['path']['text']
                line_num = match_data['line_number']
                content = match_data['lines']['text'].strip()
                
                result = {
                    'file': file_path,
                    'line': line_num,
                    'content': content,
                    'pattern': pattern,
                    'language': detect_language(file_path),
                    'file_type': classify_file_type(file_path),
                    'timestamp': extract_timestamp(content),
                    'context_before': [],
                    'context_after': []
                }
                
                # Extract context from submatches if available
                if 'submatches' in match_data:
                    for submatch in match_data['submatches']:
                        if submatch.get('match'):
                            # This is the actual match within the line
                            pass
                
                results.append(result)
                
        except (json.JSONDecodeError, KeyError) as e:
            # Ignore begin/end messages or malformed lines
            if 'begin' not in line and 'end' not in line and 'summary' not in line:
                print(f"Warning: Could not parse JSON line: {line.strip()}", file=sys.stderr)
    
    return results

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
    elif any(ext in path_str for ext in ['.log', '.txt', 'log']):
        return 'log'
    elif any(ext in path_str for ext in ['.xml', '.properties', '.json', '.yml', '.yaml']):
        return 'config'
    elif 'src/main' in path_str:
        return 'source'
    else:
        return 'other'

def extract_timestamp(content):
    """Extract timestamp from log content if present."""
    # Common timestamp patterns
    patterns = [
        r'(\d{4}-\d{2}-\d{2}[\s_T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)',  # ISO format with optional timezone
        r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',     # US format
        r'(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})',     # EU format
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',     # Standard format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            timestamp_str = match.group(1)
            try:
                # Try to parse and normalize the timestamp
                if 'T' in timestamp_str or 'Z' in timestamp_str or '+' in timestamp_str or timestamp_str.count('-') > 2:
                    # ISO format - try to parse with timezone awareness
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    return dt.isoformat()
                else:
                    # Other formats - return as-is
                    return timestamp_str
            except ValueError:
                # If parsing fails, return the raw timestamp
                return timestamp_str
    
    return None

def analyze_pattern_frequency(results, group_by='file'):
    """Analyze pattern frequency by various dimensions."""
    analysis = {
        'total_matches': len(results),
        'by_file': Counter(),
        'by_language': Counter(),
        'by_file_type': Counter(),
        'by_date': Counter(),
        'by_hour': Counter(),
        'content_patterns': Counter(),
        'co_occurrence': defaultdict(Counter)
    }
    
    for result in results:
        analysis['by_file'][result['file']] += 1
        analysis['by_language'][result['language']] += 1
        analysis['by_file_type'][result['file_type']] += 1
        
        # Temporal analysis for logs
        if result['timestamp']:
            # Extract date and hour with timezone awareness
            try:
                timestamp_str = result['timestamp']
                if 'T' in timestamp_str or ' ' in timestamp_str:
                    # Handle timezone-aware parsing
                    if '+' in timestamp_str or 'Z' in timestamp_str:
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        # Assume local timezone if no timezone info
                        clean_timestamp = timestamp_str.replace('T', ' ').split('.')[0]
                        dt = datetime.fromisoformat(clean_timestamp)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    
                    analysis['by_date'][dt.date().isoformat()] += 1
                    analysis['by_hour'][dt.hour] += 1
            except Exception as e:
                # If parsing fails, try simpler extraction
                try:
                    # Extract just the date and hour from the string
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', timestamp_str)
                    hour_match = re.search(r'\d{2}:(\d{2}):', timestamp_str)
                    if date_match:
                        analysis['by_date'][date_match.group(1)] += 1
                    if hour_match:
                        hour = int(hour_match.group(1))
                        analysis['by_hour'][hour] += 1
                except:
                    pass
        
        # Content pattern analysis
        content = result['content'].lower()
        
        # Find common patterns in the matched lines
        if 'error' in content:
            analysis['content_patterns']['error'] += 1
        if 'warn' in content:
            analysis['content_patterns']['warning'] += 1
        if 'info' in content:
            analysis['content_patterns']['info'] += 1
        if 'debug' in content:
            analysis['content_patterns']['debug'] += 1
        if 'exception' in content:
            analysis['content_patterns']['exception'] += 1
        
        # Co-occurrence analysis (what else appears in the same line)
        words = re.findall(r'\b\w+\b', content)
        for word in words:
            if len(word) > 3 and word != result['pattern'].lower():
                analysis['co_occurrence'][result['pattern']][word] += 1
    
    return analysis

def calculate_trends(results, time_window='hour'):
    """Calculate trends over time for log data."""
    if not any(r['timestamp'] for r in results):
        return {}
    
    time_buckets = defaultdict(int)
    
    for result in results:
        if result['timestamp']:
            try:
                timestamp_str = result['timestamp']
                
                # Handle timezone-aware parsing
                if '+' in timestamp_str or 'Z' in timestamp_str:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    # Clean up timestamp and assume UTC if no timezone
                    clean_timestamp = timestamp_str.replace('T', ' ').split('.')[0]
                    dt = datetime.fromisoformat(clean_timestamp)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                
                if time_window == 'hour':
                    bucket = dt.strftime('%Y-%m-%d %H:00')
                elif time_window == 'day':
                    bucket = dt.strftime('%Y-%m-%d')
                elif time_window == 'minute':
                    bucket = dt.strftime('%Y-%m-%d %H:%M')
                else:
                    bucket = dt.strftime('%Y-%m-%d %H:00')
                
                time_buckets[bucket] += 1
            except Exception as e:
                # Try simpler string-based extraction as fallback
                try:
                    if time_window == 'day':
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', timestamp_str)
                        if date_match:
                            time_buckets[date_match.group(1)] += 1
                    elif time_window == 'hour':
                        datetime_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}):', timestamp_str)
                        if datetime_match:
                            time_buckets[datetime_match.group(1) + ':00'] += 1
                except:
                    continue
    
    # Calculate trend direction
    sorted_times = sorted(time_buckets.items())
    if len(sorted_times) >= 2:
        first_half = sum(count for _, count in sorted_times[:len(sorted_times)//2])
        second_half = sum(count for _, count in sorted_times[len(sorted_times)//2:])
        trend = "increasing" if second_half > first_half else "decreasing" if second_half < first_half else "stable"
    else:
        trend = "insufficient_data"
    
    return {
        'time_buckets': dict(time_buckets),
        'trend': trend,
        'peak_time': max(time_buckets.items(), key=lambda x: x[1])[0] if time_buckets else None,
        'total_periods': len(time_buckets)
    }

def format_analysis_results(pattern, results, analysis, trends=None, 
                           show_frequency=True, show_files=True, max_entries=None):
    """Format analysis results for display."""
    output = []
    
    # Header
    output.append("=" * 80)
    output.append(f"PATTERN ANALYSIS: '{pattern}'")
    output.append("=" * 80)
    output.append(f"Total matches found: {analysis['total_matches']}")
    
    if analysis['total_matches'] == 0:
        output.append("\nNo matches found for this pattern.")
        return '\n'.join(output)
    
    # Frequency analysis
    if show_frequency:
        output.append(f"\n📊 FREQUENCY ANALYSIS")
        output.append("-" * 40)
        
        # By file type
        if analysis['by_file_type']:
            output.append(f"\nBy file type:")
            for file_type, count in analysis['by_file_type'].most_common():
                percentage = (count / analysis['total_matches']) * 100
                output.append(f"  {file_type:12} {count:4d} ({percentage:5.1f}%)")
        
        # By language
        if analysis['by_language']:
            output.append(f"\nBy language:")
            for lang, count in analysis['by_language'].most_common():
                percentage = (count / analysis['total_matches']) * 100
                output.append(f"  {lang:12} {count:4d} ({percentage:5.1f}%)")
        
        # Top files
        output.append(f"\nTop files with matches:")
        for file_path, count in analysis['by_file'].most_common(10):
            output.append(f"  {count:3d}x {file_path}")
    
    # Content patterns
    if analysis['content_patterns']:
        output.append(f"\n🔍 CONTENT PATTERNS")
        output.append("-" * 40)
        for pattern_type, count in analysis['content_patterns'].most_common():
            percentage = (count / analysis['total_matches']) * 100
            output.append(f"  {pattern_type:15} {count:4d} ({percentage:5.1f}%)")
    
    # Co-occurrence analysis
    if analysis['co_occurrence']:
        output.append(f"\n🔗 CO-OCCURRENCE ANALYSIS")
        output.append("-" * 40)
        for main_pattern, co_words in analysis['co_occurrence'].items():
            output.append(f"\nWords appearing with '{main_pattern}':")
            for word, count in co_words.most_common(10):
                output.append(f"  {word:20} {count:3d}")
    
    # Trends analysis
    if trends:
        output.append(f"\n📈 TREND ANALYSIS")
        output.append("-" * 40)
        output.append(f"Trend direction: {trends['trend']}")
        if trends['peak_time']:
            output.append(f"Peak activity: {trends['peak_time']}")
        output.append(f"Time periods analyzed: {trends['total_periods']}")
        
        if trends['time_buckets']:
            output.append(f"\nActivity over time:")
            sorted_times = sorted(trends['time_buckets'].items())
            for time_period, count in sorted_times[-10:]:  # Show last 10 periods
                output.append(f"  {time_period:20} {count:3d} matches")
    
    # Temporal patterns (hourly distribution)
    if analysis['by_hour']:
        output.append(f"\n🕐 HOURLY DISTRIBUTION")
        output.append("-" * 40)
        max_hourly_count = max(analysis['by_hour'].values()) if analysis['by_hour'].values() else 1
        for hour in range(24):
            count = analysis['by_hour'].get(hour, 0)
            if count > 0:
                bar = '█' * min(20, count // max(1, max_hourly_count // 20))
                output.append(f"  {hour:2d}:00 {count:4d} {bar}")
    
    # Sample matches
    if show_files and results:
        output.append(f"\n📄 SAMPLE MATCHES")
        output.append("-" * 40)
        
        # Group by file type for organized display
        by_type = defaultdict(list)
        for result in results:
            by_type[result['file_type']].append(result)
        
        for file_type, type_results in sorted(by_type.items()):
            sample_size = min(5, len(type_results))
            if max_entries:
                sample_size = min(sample_size, max_entries)
            
            output.append(f"\n{file_type.upper()} files ({len(type_results)} total):")
            for result in type_results[:sample_size]:
                output.append(f"  {result['file']}:{result['line']}")
                output.append(f"    {result['content']}")
                if result['timestamp']:
                    output.append(f"    📅 {result['timestamp']}")
    
    return '\n'.join(output)

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('search', 'Pattern analysis with aggregation and frequency analysis')
    else:
        parser = argparse.ArgumentParser(description='Pattern analysis with aggregation and frequency analysis')
    
    parser.add_argument('pattern', help='Pattern to search for and analyze')
    
    # Search options
    if not HAS_STANDARD_PARSER:
        # Add search arguments manually only when standard parser is not available
        parser.add_argument('--scope', default='.', help='Directory scope for search (default: current dir)')
        parser.add_argument('-i', '--ignore-case', action='store_true', help='Case-insensitive search')
        parser.add_argument('--regex', action='store_true', help='Use regex pattern matching')
        parser.add_argument('-C', '--context', type=int, default=0, metavar='N',
                           help='Show N lines around match')
        parser.add_argument('--file-pattern', '-g', default='*', help='File pattern (e.g., "*.java")')
    # Note: search arguments are automatically added by the enhanced parser for 'search' tool type
    # Analysis options
    parser.add_argument('--count-by-file', action='store_true', default=True,
                       help='Count occurrences by file (default: true)')
    parser.add_argument('--show-frequency', action='store_true', default=True,
                       help='Show frequency analysis (default: true)')
    parser.add_argument('--show-timeline', action='store_true',
                       help='Show timeline analysis for log data')
    parser.add_argument('--show-trends', action='store_true',
                       help='Calculate and show trend analysis')
    parser.add_argument('--content-patterns', action='store_true',
                       help='Analyze content patterns (error, warning, etc.)')
    parser.add_argument('--co-occurrence', action='store_true',
                       help='Show word co-occurrence analysis')
    
    # Display options
    parser.add_argument('--top-files', type=int, default=10,
                       help='Number of top files to show (default: 10)')
    parser.add_argument('--max-samples', type=int, default=5,
                       help='Maximum sample matches to show per file type (default: 5)')
    parser.add_argument('--time-window', choices=['minute', 'hour', 'day'], default='hour',
                       help='Time window for trend analysis (default: hour)')
    
    # Output options
    parser.add_argument('--summary-only', action='store_true', help='Show only summary statistics')
    
    args = parser.parse_args()
    
    try:
        # Search for pattern
        # Handle different attribute names between enhanced parser and manual parser
        file_pattern = getattr(args, 'glob', getattr(args, 'file_pattern', '*'))
        
        # Convert enhanced parser's --type to regex flag
        if hasattr(args, 'type'):
            use_regex = (args.type == 'regex')
        else:
            use_regex = getattr(args, 'regex', False)
        
        # Handle context argument which might be None from enhanced parser
        context_lines = getattr(args, 'context', 0) or 0
        
        output = search_pattern_with_ripgrep(
            args.pattern, args.scope, file_pattern,
            use_regex, args.ignore_case, context_lines
        )
        
        # Parse results
        results = parse_search_results(output, args.pattern)
        
        # Analyze frequency
        analysis = analyze_pattern_frequency(results)
        
        # Calculate trends if requested
        trends = None
        if args.show_trends or args.show_timeline:
            trends = calculate_trends(results, args.time_window)
        
        # Output results
        if args.json:
            json_output = {
                'pattern': args.pattern,
                'analysis': {
                    'total_matches': analysis['total_matches'],
                    'by_file': dict(analysis['by_file']),
                    'by_language': dict(analysis['by_language']),
                    'by_file_type': dict(analysis['by_file_type']),
                    'content_patterns': dict(analysis['content_patterns']),
                    'by_hour': dict(analysis['by_hour'])
                },
                'trends': trends,
                'results': [
                    {
                        'file': r['file'],
                        'line': r['line'],
                        'content': r['content'],
                        'language': r['language'],
                        'file_type': r['file_type'],
                        'timestamp': r['timestamp']
                    } for r in results
                ] if not args.summary_only else []
            }
            print(json.dumps(json_output, indent=2, default=str))
        else:
            formatted_results = format_analysis_results(
                args.pattern, results, analysis, trends,
                args.show_frequency, not args.summary_only, args.max_samples
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