#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Log analyzer for pattern frequency and timeline analysis.

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
from datetime import datetime, timedelta, timezone
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

def search_log_pattern(pattern, log_files, regex=True, ignore_case=False, context_lines=0):
    """Search for patterns in log files using ripgrep's JSON output."""
    check_ripgrep()
    
    cmd = ['rg']
    
    if not regex:
        cmd.append('-F')  # Fixed string
    # Note: ripgrep uses regex by default, so -E is not needed
    
    if ignore_case:
        cmd.append('-i')
    
    if context_lines > 0:
        cmd.extend(['-C', str(context_lines)])
    
    # Add log file extensions
    cmd.extend(['-g', '*.log', '-g', '*.txt'])
    
    cmd.append(pattern)
    
    # Add files or directories
    if isinstance(log_files, list):
        cmd.extend(log_files)
    else:
        cmd.append(log_files)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Search timed out for pattern: {pattern}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"An error occurred running ripgrep: {e}", file=sys.stderr)
        return ""

def parse_log_entries(output, pattern):
    """Parse ripgrep's JSON output into structured log entries."""
    entries = []
    
    for line in output.split('\n'):
        if not line.strip():
            continue
        
        # Match file:line:content format
        try:
            data = json.loads(line)
            if data['type'] == 'match':
                match_data = data['data']
                file_path = match_data['path']['text']
                content = match_data['lines']['text'].strip()
                timestamp = extract_timestamp(content)
                
                context_before = [ctx['text'].strip() for ctx in match_data.get('context', []) if ctx['line_number'] < match_data['line_number']]
                
                # Convert datetime object to string for consistency, but keep datetime object for processing
                timestamp_str = None
                date_only = None
                hour = None
                if timestamp:
                    if isinstance(timestamp, datetime):
                        timestamp_str = timestamp.isoformat()
                        date_only = timestamp.date().isoformat()
                        hour = timestamp.hour
                    else:
                        # If it's a string (fallback case), keep it as is
                        timestamp_str = timestamp
                        # Try to parse for date/hour extraction
                        try:
                            dt = datetime.fromisoformat(str(timestamp).replace('T', ' ').split('.')[0])
                            date_only = dt.date().isoformat()
                            hour = dt.hour
                        except:
                            pass
                
                entries.append({
                    'file': file_path,
                    'line': match_data['line_number'],
                    'content': content,
                    'pattern': pattern,
                    'timestamp': timestamp_str,
                    'log_level': extract_log_level(content),
                    'context': extract_context_info(content, pattern),
                    'date_only': date_only,
                    'hour': hour,
                    'context_before': context_before,
                    'context_after': [] # JSON output context is not split this way
                })
        except (json.JSONDecodeError, KeyError):
            # Ignore non-match lines like 'begin', 'end', 'summary'
            continue
    
    return entries

def extract_timestamp(content):
    """Extract timestamp from log content using a comprehensive pattern with timezone support."""
    # Comprehensive timestamp pattern that handles most common formats
    # This pattern captures timestamps with optional milliseconds and timezone info
    timestamp_pattern = r'''(?x)
        # ISO 8601 formats with optional timezone
        (\d{4}-\d{2}-\d{2}[\s_T]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:[+-]\d{2}:?\d{2}|Z)?)
        |
        # US format (MM/DD/YYYY HH:MM:SS)
        (\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d{1,3})?)
        |
        # EU format (DD-MM-YYYY HH:MM:SS)
        (\d{1,2}-\d{1,2}-\d{4}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d{1,3})?)
        |
        # Syslog format (e.g., "Jan 15 14:30:22")
        (\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d{1,3})?)
        |
        # Unix timestamp (10-13 digits)
        \b(\d{10,13})\b
        |
        # Log4j format with brackets [2024-07-07 10:30:15.123]
        \[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?)\]
    '''
    
    match = re.search(timestamp_pattern, content)
    if not match:
        return None
    
    # Get the captured group that matched
    timestamp_str = next(g for g in match.groups() if g is not None)
    
    try:
        # Handle Unix timestamps
        if timestamp_str.isdigit():
            timestamp_int = int(timestamp_str)
            if len(timestamp_str) == 13:  # milliseconds
                dt = datetime.fromtimestamp(timestamp_int / 1000, tz=timezone.utc)
            else:  # seconds
                dt = datetime.fromtimestamp(timestamp_int, tz=timezone.utc)
            return dt
        
        # Try parsing with datetime.fromisoformat (Python 3.7+) for ISO formats
        # Handle the common case where 'T' is replaced with space
        cleaned_timestamp = timestamp_str.replace('_', ' ')
        
        # Try fromisoformat first (handles timezones well)
        try:
            # Handle 'Z' timezone indicator
            if cleaned_timestamp.endswith('Z'):
                cleaned_timestamp = cleaned_timestamp[:-1] + '+00:00'
            dt = datetime.fromisoformat(cleaned_timestamp)
            return dt
        except (ValueError, AttributeError):
            pass
        
        # Fall back to strptime for other formats
        # Define format patterns for non-ISO timestamps
        format_patterns = [
            ('%Y-%m-%d %H:%M:%S.%f', None),
            ('%Y-%m-%d %H:%M:%S', None),
            ('%Y-%m-%dT%H:%M:%S.%f', None),
            ('%Y-%m-%dT%H:%M:%S', None),
            ('%m/%d/%Y %H:%M:%S.%f', None),
            ('%m/%d/%Y %H:%M:%S', None),
            ('%d-%m-%Y %H:%M:%S.%f', None),
            ('%d-%m-%Y %H:%M:%S', None),
            ('%b %d %H:%M:%S.%f', lambda dt: dt.replace(year=datetime.now().year)),
            ('%b %d %H:%M:%S', lambda dt: dt.replace(year=datetime.now().year)),
        ]
        
        for fmt, post_process in format_patterns:
            try:
                dt = datetime.strptime(cleaned_timestamp, fmt)
                if post_process:
                    dt = post_process(dt)
                # If no timezone info, assume local timezone
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        # If all parsing fails, return the original string
        return timestamp_str
        
    except Exception:
        # Return the original string if parsing fails
        return timestamp_str

def extract_log_level(content):
    """Extract log level from content using efficient regex."""
    # Single regex pattern for all common log levels
    # Using word boundaries to avoid false matches
    log_level_pattern = r'\b(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|SEVERE|CRITICAL)\b'
    
    match = re.search(log_level_pattern, content, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    # Additional patterns for bracketed log levels like [INFO] or <ERROR>
    bracketed_pattern = r'[\[<](TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|SEVERE|CRITICAL)[\]>]'
    match = re.search(bracketed_pattern, content, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    return 'UNKNOWN'

def extract_context_info(content, pattern):
    """Extract contextual information from log entry."""
    context = {
        'thread': None,
        'class': None,
        'method': None,
        'exception': None,
        'numeric_values': [],
        'has_stacktrace': False
    }
    
    # Extract thread information
    thread_match = re.search(r'\[([^\]]+)\]', content)
    if thread_match:
        context['thread'] = thread_match.group(1)
    
    # Extract class/method information
    class_match = re.search(r'([A-Z][a-zA-Z]+)\.([a-zA-Z]+)', content)
    if class_match:
        context['class'] = class_match.group(1)
        context['method'] = class_match.group(2)
    
    # Extract exception information
    if any(exc in content.upper() for exc in ['EXCEPTION', 'ERROR', 'THROWABLE']):
        exc_match = re.search(r'([A-Z][a-zA-Z]*Exception|[A-Z][a-zA-Z]*Error)', content)
        if exc_match:
            context['exception'] = exc_match.group(1)
    
    # Extract numeric values
    numeric_matches = re.findall(r'-?\d+\.?\d*', content)
    context['numeric_values'] = [float(n) if '.' in n else int(n) for n in numeric_matches[:5]]  # Limit to 5 numbers
    
    # Check for stack trace
    context['has_stacktrace'] = 'at ' in content and ('(' in content and ')' in content)
    
    return context

def analyze_frequency_patterns(entries, time_window='hour'):
    """Analyze frequency patterns over time."""
    analysis = {
        'total_entries': len(entries),
        'by_hour': defaultdict(int),
        'by_date': defaultdict(int),
        'by_log_level': defaultdict(int),
        'by_file': defaultdict(int),
        'by_thread': defaultdict(int),
        'by_class': defaultdict(int),
        'by_exception': defaultdict(int),
        'time_series': defaultdict(int),
        'peak_times': [],
        'quiet_periods': []
    }
    
    timestamps = []
    
    for entry in entries:
        analysis['by_file'][entry['file']] += 1
        analysis['by_log_level'][entry['log_level']] += 1
        
        if entry['context']:
            if entry['context']['thread']:
                analysis['by_thread'][entry['context']['thread']] += 1
            if entry['context']['class']:
                analysis['by_class'][entry['context']['class']] += 1
            if entry['context']['exception']:
                analysis['by_exception'][entry['context']['exception']] += 1
        
        if entry['timestamp']:
            try:
                # Parse timestamp for temporal analysis
                dt = None
                if isinstance(entry['timestamp'], str):
                    # Handle ISO format timestamps
                    dt = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                elif isinstance(entry['timestamp'], datetime):
                    dt = entry['timestamp']
                
                if dt:
                    timestamps.append(dt)
                    
                    analysis['by_date'][dt.date().isoformat()] += 1
                    analysis['by_hour'][dt.hour] += 1
                    
                    # Time series buckets
                    if time_window == 'minute':
                        bucket = dt.strftime('%Y-%m-%d %H:%M')
                    elif time_window == 'hour':
                        bucket = dt.strftime('%Y-%m-%d %H:00')
                    elif time_window == 'day':
                        bucket = dt.strftime('%Y-%m-%d')
                    else:
                        bucket = dt.strftime('%Y-%m-%d %H:00')
                    
                    analysis['time_series'][bucket] += 1
            except:
                continue
    
    # Find peak times and quiet periods
    if timestamps:
        timestamps.sort()
        
        # Find periods with high activity (peaks)
        time_counts = Counter()
        for ts in timestamps:
            hour_bucket = ts.strftime('%H:00')
            time_counts[hour_bucket] += 1
        
        if time_counts:
            avg_count = sum(time_counts.values()) / len(time_counts)
            analysis['peak_times'] = [
                hour for hour, count in time_counts.items() 
                if count > avg_count * 1.5
            ]
            analysis['quiet_periods'] = [
                hour for hour, count in time_counts.items() 
                if count < avg_count * 0.5
            ]
    
    return analysis

def calculate_timeline_trends(entries, time_window='hour'):
    """Calculate trends over time."""
    if not any(e['timestamp'] for e in entries):
        return {}
    
    time_buckets = defaultdict(int)
    level_trends = defaultdict(lambda: defaultdict(int))
    
    for entry in entries:
        if entry['timestamp']:
            try:
                dt = None
                if isinstance(entry['timestamp'], str):
                    dt = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                elif isinstance(entry['timestamp'], datetime):
                    dt = entry['timestamp']
                
                if dt:
                    if time_window == 'hour':
                        bucket = dt.strftime('%Y-%m-%d %H:00')
                    elif time_window == 'day':
                        bucket = dt.strftime('%Y-%m-%d')
                    elif time_window == 'minute':
                        bucket = dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        bucket = dt.strftime('%Y-%m-%d %H:00')
                    
                    time_buckets[bucket] += 1
                    level_trends[entry['log_level']][bucket] += 1
            except:
                continue
    
    # Calculate trend direction
    sorted_times = sorted(time_buckets.items())
    if len(sorted_times) >= 4:
        # Compare first quarter with last quarter
        quarter_size = len(sorted_times) // 4
        first_quarter = sum(count for _, count in sorted_times[:quarter_size])
        last_quarter = sum(count for _, count in sorted_times[-quarter_size:])
        
        if last_quarter > first_quarter * 1.2:
            trend = "increasing"
        elif last_quarter < first_quarter * 0.8:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    # Find busiest and quietest periods
    if time_buckets:
        busiest_period = max(time_buckets.items(), key=lambda x: x[1])
        quietest_period = min(time_buckets.items(), key=lambda x: x[1])
    else:
        busiest_period = None
        quietest_period = None
    
    return {
        'time_buckets': dict(time_buckets),
        'level_trends': {level: dict(buckets) for level, buckets in level_trends.items()},
        'trend': trend,
        'busiest_period': busiest_period,
        'quietest_period': quietest_period,
        'total_periods': len(time_buckets),
        'time_span': f"{min(time_buckets.keys())} to {max(time_buckets.keys())}" if time_buckets else None
    }

def detect_anomalies(entries, threshold_multiplier=2.0):
    """Detect anomalous patterns in log entries."""
    anomalies = {
        'frequency_spikes': [],
        'unusual_patterns': [],
        'error_bursts': [],
        'long_quiet_periods': []
    }
    
    if not entries:
        return anomalies
    
    # Frequency analysis for spikes
    hourly_counts = defaultdict(int)
    error_counts = defaultdict(int)
    
    for entry in entries:
        if entry['hour']:
            hourly_counts[entry['hour']] += 1
            if entry['log_level'] in ['ERROR', 'FATAL', 'SEVERE']:
                error_counts[entry['hour']] += 1
    
    if hourly_counts:
        avg_hourly = sum(hourly_counts.values()) / len(hourly_counts)
        threshold = avg_hourly * threshold_multiplier
        
        for hour, count in hourly_counts.items():
            if count > threshold:
                anomalies['frequency_spikes'].append({
                    'hour': hour,
                    'count': count,
                    'threshold': threshold,
                    'factor': count / avg_hourly
                })
    
    # Error burst detection
    if error_counts:
        avg_errors = sum(error_counts.values()) / len(error_counts) if error_counts else 0
        error_threshold = max(avg_errors * threshold_multiplier, 5)  # At least 5 errors
        
        for hour, count in error_counts.items():
            if count > error_threshold:
                anomalies['error_bursts'].append({
                    'hour': hour,
                    'error_count': count,
                    'threshold': error_threshold
                })
    
    # Pattern analysis for unusual occurrences
    class_patterns = Counter(
        entry['context']['class'] for entry in entries 
        if entry['context'] and entry['context']['class']
    )
    
    if class_patterns:
        # Find classes mentioned unusually often
        avg_class_mentions = sum(class_patterns.values()) / len(class_patterns)
        for class_name, count in class_patterns.items():
            if count > avg_class_mentions * threshold_multiplier:
                anomalies['unusual_patterns'].append({
                    'type': 'class_frequency',
                    'pattern': class_name,
                    'count': count,
                    'threshold': avg_class_mentions * threshold_multiplier
                })
    
    return anomalies

def format_log_analysis(pattern, entries, frequency_analysis, timeline_trends=None, 
                       anomalies=None, show_samples=True, max_samples=10):
    """Format log analysis results for display."""
    output = []
    
    # Header
    output.append("=" * 80)
    output.append(f"LOG ANALYSIS: '{pattern}'")
    output.append("=" * 80)
    output.append(f"Total log entries found: {frequency_analysis['total_entries']}")
    
    if frequency_analysis['total_entries'] == 0:
        output.append("\nNo log entries found for this pattern.")
        return '\n'.join(output)
    
    # Frequency analysis
    output.append(f"\n📊 FREQUENCY ANALYSIS")
    output.append("-" * 40)
    
    # By log level
    if frequency_analysis['by_log_level']:
        output.append(f"\nBy log level:")
        for level, count in sorted(frequency_analysis['by_log_level'].items(), 
                                 key=lambda x: x[1], reverse=True):
            percentage = (count / frequency_analysis['total_entries']) * 100
            output.append(f"  {level:8} {count:4d} ({percentage:5.1f}%)")
    
    # By file
    if frequency_analysis['by_file']:
        output.append(f"\nTop log files:")
        for file_path, count in Counter(frequency_analysis['by_file']).most_common(5):
            output.append(f"  {count:3d}x {file_path}")
    
    # By thread (if available)
    if frequency_analysis['by_thread']:
        output.append(f"\nTop threads:")
        for thread, count in Counter(frequency_analysis['by_thread']).most_common(5):
            output.append(f"  {count:3d}x {thread}")
    
    # By class (if available)
    if frequency_analysis['by_class']:
        output.append(f"\nTop classes:")
        for class_name, count in Counter(frequency_analysis['by_class']).most_common(5):
            output.append(f"  {count:3d}x {class_name}")
    
    # Exception analysis
    if frequency_analysis['by_exception']:
        output.append(f"\nExceptions found:")
        for exception, count in Counter(frequency_analysis['by_exception']).most_common():
            output.append(f"  {count:3d}x {exception}")
    
    # Hourly distribution
    if frequency_analysis['by_hour']:
        output.append(f"\n🕐 HOURLY DISTRIBUTION")
        output.append("-" * 40)
        max_count = max(frequency_analysis['by_hour'].values())
        for hour in range(24):
            count = frequency_analysis['by_hour'].get(hour, 0)
            if count > 0:
                bar_length = min(30, (count * 30) // max_count) if max_count > 0 else 0
                bar = '█' * bar_length
                output.append(f"  {hour:2d}:00 {count:4d} {bar}")
    
    # Peak times and quiet periods
    if frequency_analysis['peak_times']:
        output.append(f"\n🔥 Peak activity hours: {', '.join(frequency_analysis['peak_times'])}")
    if frequency_analysis['quiet_periods']:
        output.append(f"😴 Quiet hours: {', '.join(frequency_analysis['quiet_periods'])}")
    
    # Timeline trends
    if timeline_trends:
        output.append(f"\n📈 TIMELINE ANALYSIS")
        output.append("-" * 40)
        output.append(f"Overall trend: {timeline_trends['trend']}")
        if timeline_trends['time_span']:
            output.append(f"Time span: {timeline_trends['time_span']}")
        if timeline_trends['busiest_period']:
            period, count = timeline_trends['busiest_period']
            output.append(f"Busiest period: {period} ({count} entries)")
        if timeline_trends['quietest_period']:
            period, count = timeline_trends['quietest_period']
            output.append(f"Quietest period: {period} ({count} entries)")
        
        # Show recent activity
        if timeline_trends['time_buckets']:
            recent_periods = sorted(timeline_trends['time_buckets'].items())[-10:]
            output.append(f"\nRecent activity:")
            for period, count in recent_periods:
                output.append(f"  {period:20} {count:3d} entries")
    
    # Anomaly detection
    if anomalies:
        has_anomalies = any(anomalies.values())
        if has_anomalies:
            output.append(f"\n🚨 ANOMALY DETECTION")
            output.append("-" * 40)
            
            if anomalies['frequency_spikes']:
                output.append(f"\nFrequency spikes detected:")
                for spike in anomalies['frequency_spikes']:
                    output.append(f"  Hour {spike['hour']}: {spike['count']} entries "
                                f"({spike['factor']:.1f}x normal)")
            
            if anomalies['error_bursts']:
                output.append(f"\nError bursts detected:")
                for burst in anomalies['error_bursts']:
                    output.append(f"  Hour {burst['hour']}: {burst['error_count']} errors")
            
            if anomalies['unusual_patterns']:
                output.append(f"\nUnusual patterns:")
                for pattern in anomalies['unusual_patterns']:
                    output.append(f"  {pattern['pattern']}: {pattern['count']} occurrences")
    
    # Sample entries
    if show_samples and entries:
        output.append(f"\n📄 SAMPLE LOG ENTRIES")
        output.append("-" * 40)
        
        # Group by log level for organized display
        by_level = defaultdict(list)
        for entry in entries:
            by_level[entry['log_level']].append(entry)
        
        shown_samples = 0
        for level in ['ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'TRACE']:
            if level in by_level and shown_samples < max_samples:
                level_entries = by_level[level][:3]  # Show up to 3 per level
                output.append(f"\n{level} entries:")
                for entry in level_entries:
                    if shown_samples >= max_samples:
                        break
                    output.append(f"  {entry['file']}:{entry['line']}")
                    if entry['timestamp']:
                        output.append(f"    🕐 {entry['timestamp']}")
                    output.append(f"    📝 {entry['content']}")
                    if entry['context'] and entry['context']['exception']:
                        output.append(f"    ⚠️  Exception: {entry['context']['exception']}")
                    shown_samples += 1
                    if shown_samples < len(entries):
                        output.append("")
        
        if len(entries) > max_samples:
            output.append(f"\n... and {len(entries) - max_samples} more entries")
    
    return '\n'.join(output)

def main():
    # Don't use standard analyze parser - log analyzer has its own argument structure
    if False:  # Disabled standard parser for this tool
        parser = create_parser('analyze', 'Log analyzer for pattern frequency and timeline analysis')
    else:
        parser = argparse.ArgumentParser(
            description='''Log analyzer for pattern frequency and timeline analysis

Examples:
  # Basic pattern analysis
  ./run_any_python_tool.sh log_analyzer.py --pattern "REVERSAL" --files ./logs/*.txt --frequency
  
  # Timeline analysis with trends  
  # Anomaly detection for error patterns  
  # Complete analysis with all features  
  # Focus on specific time window        ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
    
    parser.add_argument('--pattern', required=True, help='Pattern to search for in logs')
    parser.add_argument('--files', required=True, 
                       help='Log files or directory to analyze (e.g., "./logs/*.txt")')
    
    # Search options
    parser.add_argument('--regex', action='store_true', help='Use regex pattern matching')
    parser.add_argument('-i', '--ignore-case', action='store_true', help='Case-insensitive search')
    parser.add_argument('-C', '--context', type=int, default=0, help='Number of context lines to show')
    # Analysis options
    parser.add_argument('--frequency', action='store_true', default=True,
                       help='Analyze frequency patterns (default: true)')
    parser.add_argument('--timeline', action='store_true',
                       help='Analyze timeline trends and patterns')
    parser.add_argument('--anomaly-detection', action='store_true',
                       help='Detect anomalous patterns and spikes')
    parser.add_argument('--all-analysis', action='store_true',
                       help='Enable all analysis features')
    
    # Time analysis options
    parser.add_argument('--time-window', choices=['minute', 'hour', 'day'], default='hour',
                       help='Time window for trend analysis (default: hour)')
    parser.add_argument('--threshold', type=float, default=2.0,
                       help='Anomaly detection threshold multiplier (default: 2.0)')
    
    # Display options
    parser.add_argument('--samples', type=int, default=10,
                       help='Number of sample log entries to show (default: 10)')
    parser.add_argument('--no-samples', action='store_true',
                       help='Don\'t show sample log entries')
    
    # Output options
    parser.add_argument('--summary-only', action='store_true', help='Show only summary statistics')
    
    # Add --json since we're not using standard parser anymore
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Handle all-analysis flag
    if args.all_analysis:
        args.frequency = True
        args.timeline = True
        args.anomaly_detection = True
    
    try:
        # Search for pattern in log files
        search_output = search_log_pattern(
            args.pattern, args.files, args.regex, args.ignore_case, args.context
        )
        
        # Parse log entries
        entries = parse_log_entries(search_output, args.pattern)
        
        # Frequency analysis
        frequency_analysis = None
        if args.frequency:
            frequency_analysis = analyze_frequency_patterns(entries, args.time_window)
        
        # Timeline trends
        timeline_trends = None
        if args.timeline:
            timeline_trends = calculate_timeline_trends(entries, args.time_window)
        
        # Anomaly detection
        anomalies = None
        if args.anomaly_detection:
            anomalies = detect_anomalies(entries, args.threshold)
        
        # Output results
        if args.json:
            json_output = {
                'pattern': args.pattern,
                'analysis': frequency_analysis,
                'timeline': timeline_trends,
                'anomalies': anomalies,
                'entries': [
                    {
                        'file': e['file'],
                        'line': e['line'],
                        'content': e['content'],
                        'timestamp': e['timestamp'],
                        'log_level': e['log_level'],
                        'context': e['context']
                    } for e in entries
                ] if not args.summary_only else []
            }
            print(json.dumps(json_output, indent=2, default=str))
        else:
            formatted_results = format_log_analysis(
                args.pattern, entries, frequency_analysis, timeline_trends,
                anomalies, not args.no_samples, args.samples
            )
            print(formatted_results)
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()