#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Error Dashboard - Visual summary of tool errors with actionable insights.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
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

def load_error_log(log_path: Path) -> list:
    """Load errors from JSONL log."""
    errors = []
    if log_path.exists():
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    errors.append(json.loads(line))
                except:
                    pass
    return errors

def categorize_errors(errors: list) -> dict:
    """Categorize errors by type."""
    categories = {
        'usage_errors': [],
        'file_not_found': [],
        'test_errors': [],
        'real_failures': [],
        'permission_errors': []
    }
    
    for error in errors:
        tool = error.get('tool_name', '')
        msg = error.get('error_message', '')
        stderr = error.get('additional_context', {}).get('stderr', '')
        args = error.get('command_args', [])
        
        # Categorize
        if 'test' in tool or 'nonexistent' in ' '.join(args):
            categories['test_errors'].append(error)
        elif stderr and ('unrecognized arguments' in stderr or 'usage:' in stderr):
            categories['usage_errors'].append(error)
        elif stderr and ('No such file' in stderr or 'not found' in msg):
            categories['file_not_found'].append(error)
        elif stderr and ('Permission' in stderr or 'Access denied' in stderr):
            categories['permission_errors'].append(error)
        else:
            categories['real_failures'].append(error)
    
    return categories

def print_dashboard(errors: list, days: int = 7, focus_type: str = None, output_json: bool = False):
    """Print error dashboard."""
    # Filter by time if requested
    if days:
        cutoff = datetime.now() - timedelta(days=days)
        errors = [e for e in errors if datetime.fromisoformat(e['timestamp']) > cutoff]
    
    if not errors:
        if output_json:
            print(json.dumps({"message": "No errors found", "total_errors": 0, "period_days": days}))
        else:
            print("🎉 No errors found in the specified time period!")
        return
    
    categories = categorize_errors(errors)
    
    if output_json:
        # JSON output
        tool_counts = Counter()
        real_errors = [e for e in errors if e not in categories['test_errors']]
        if real_errors:
            tool_counts = Counter(e['tool_name'] for e in real_errors)
        
        output = {
            "period_days": days,
            "total_errors": len(errors),
            "focus_type": focus_type,
            "categories": {k: len(v) for k, v in categories.items() if v},
            "most_problematic_tools": dict(tool_counts.most_common(5)),
            "usage_error_examples": []
        }
        
        # Add usage error examples
        for error in categories['usage_errors'][:5]:
            stderr = error.get('additional_context', {}).get('stderr', '')
            if 'unrecognized arguments:' in stderr:
                bad_arg = stderr.split('unrecognized arguments:')[1].strip().split('\n')[0]
                output["usage_error_examples"].append({
                    "tool": error['tool_name'],
                    "command": ' '.join(error['command_args']),
                    "issue": f"Unrecognized argument: {bad_arg}"
                })
        
        print(json.dumps(output, indent=2))
        return
    
    print("=" * 80)
    if focus_type:
        print(f"                   ERROR DASHBOARD - {focus_type.upper()}")
    else:
        print("                        ERROR DASHBOARD")
    print("=" * 80)
    print(f"Period: Last {days} days | Total Errors: {len(errors)}")
    print()
    
    # Summary by category
    print("ERROR CATEGORIES:")
    print("-" * 40)
    for category, cat_errors in categories.items():
        if cat_errors:
            percentage = (len(cat_errors) / len(errors)) * 100
            print(f"  {category.replace('_', ' ').title()}: {len(cat_errors)} ({percentage:.1f}%)")
    print()
    
    # Most problematic tools (excluding test errors)
    real_errors = [e for e in errors if e not in categories['test_errors']]
    tool_counts = Counter()
    if real_errors:
        tool_counts = Counter(e['tool_name'] for e in real_errors)
        print("MOST PROBLEMATIC TOOLS:")
        print("-" * 40)
        for tool, count in tool_counts.most_common(5):
            print(f"  {tool}: {count} errors")
        print()
    
    # Usage errors detail
    if categories['usage_errors']:
        print("USAGE ERRORS (Action Required):")
        print("-" * 40)
        seen = set()
        for error in categories['usage_errors'][:5]:
            tool = error['tool_name']
            args = ' '.join(error['command_args'])
            key = f"{tool}:{args}"
            if key not in seen:
                seen.add(key)
                print(f"  Tool: {tool}")
                print(f"  Command: {args}")
                stderr = error.get('additional_context', {}).get('stderr', '')
                if 'unrecognized arguments:' in stderr:
                    bad_arg = stderr.split('unrecognized arguments:')[1].strip().split('\n')[0]
                    print(f"  Issue: Unrecognized argument: {bad_arg}")
                print()
    
    # Recommendations
    print("RECOMMENDATIONS:")
    print("-" * 40)
    
    if categories['usage_errors']:
        print("1. Update documentation/examples for tools with usage errors")
        print("2. Add better error messages with usage examples")
    
    if categories['file_not_found']:
        print("3. Add file existence checks before processing")
        print("4. Provide clearer error messages for missing files")
    
    if tool_counts.most_common(1):
        top_tool = tool_counts.most_common(1)[0][0]
        print(f"5. Review {top_tool} - it has the most errors")
    
    print()
    print("Run 'analyze_errors.py --recent 10' for detailed error information")

def main():
    # Create a basic parser and add standard common args manually
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Error dashboard for Python tools')
    else:
        parser = argparse.ArgumentParser(description='Error dashboard for Python tools')
    
    # Add the focus type as optional positional argument (analyze pattern)
    parser.add_argument('focus_type', nargs='?',
                       help='Error type to focus on (optional: usage_errors, file_not_found, test_errors, etc.)')
    
    # Add specific options for error dashboard
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--log-dir', help='Custom log directory')
    
    # Add relevant standard args
    args = parser.parse_args()
    
    # Find log file
    if args.log_dir:
        log_dir = Path(args.log_dir)
    else:
        log_dir = Path.home() / ".pytoolserrors"
    
    error_log = log_dir / "errors.jsonl"
    
    # Load and display
    errors = load_error_log(error_log)
    
    # Filter by focus type if provided
    if hasattr(args, 'focus_type') and args.focus_type:
        categories = categorize_errors(errors)
        if args.focus_type in categories:
            errors = categories[args.focus_type]
            print(f"Focusing on error type: {args.focus_type}")
            print(f"Found {len(errors)} errors of this type")
            print()
    
    focus_type = getattr(args, 'focus_type', None)
    print_dashboard(errors, args.days, focus_type, args.json)

if __name__ == "__main__":
    main()