#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Error log analysis tool for Python tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional
import re

# Don't use standard parser for this tool - it doesn't need a target
def create_parser(description):
    return argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

# Import preflight checks
try:
    from preflight_checks import run_preflight_checks, PreflightChecker
except ImportError:
    def run_preflight_checks(checks, exit_on_fail=True):
        pass
    class PreflightChecker:
        @staticmethod
        def check_path_exists(path, path_type="path"):
            return True, ""

class ErrorAnalyzer:
    """Analyze error logs to find patterns and insights."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize analyzer with log directory."""
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            home = Path.home()
            self.log_dir = home / ".pytoolserrors"
            
        self.error_log = self.log_dir / "errors.jsonl"
        self.summary_log = self.log_dir / "error_summary.json"
        
    def load_errors(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load errors from log file, optionally filtered by age."""
        errors = []
        
        if not self.error_log.exists():
            return errors
            
        cutoff = None
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            
        with open(self.error_log, 'r') as f:
            for line in f:
                try:
                    error = json.loads(line)
                    if cutoff:
                        error_time = datetime.fromisoformat(error['timestamp'])
                        if error_time < cutoff:
                            continue
                    errors.append(error)
                except:
                    pass
                    
        return errors
    
    def analyze_patterns(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error patterns and frequencies."""
        analysis = {
            "total_errors": len(errors),
            "time_range": {},
            "by_tool": defaultdict(lambda: {"count": 0, "types": Counter()}),
            "by_type": Counter(),
            "by_hour": Counter(),
            "by_day": Counter(),
            "common_messages": Counter(),
            "common_args": Counter(),
            "failure_patterns": []
        }
        
        if not errors:
            return analysis
            
        # Time range
        timestamps = [datetime.fromisoformat(e['timestamp']) for e in errors]
        analysis["time_range"] = {
            "first": min(timestamps).isoformat(),
            "last": max(timestamps).isoformat(),
            "duration_days": (max(timestamps) - min(timestamps)).days
        }
        
        # Analyze each error
        for error in errors:
            tool = error.get('tool_name', 'unknown')
            error_type = error.get('error_type', 'unknown')
            
            # By tool
            analysis["by_tool"][tool]["count"] += 1
            analysis["by_tool"][tool]["types"][error_type] += 1
            
            # By type
            analysis["by_type"][error_type] += 1
            
            # By time
            timestamp = datetime.fromisoformat(error['timestamp'])
            analysis["by_hour"][timestamp.hour] += 1
            analysis["by_day"][timestamp.strftime('%A')] += 1
            
            # Common messages (first 50 chars)
            msg = error.get('error_message', '')[:50]
            analysis["common_messages"][msg] += 1
            
            # Common args patterns
            args = ' '.join(error.get('command_args', []))
            if args:
                analysis["common_args"][args] += 1
        
        # Find failure patterns
        analysis["failure_patterns"] = self._find_failure_patterns(errors)
        
        # Convert defaultdict and Counter to regular dict for JSON serialization
        analysis["by_tool"] = dict(analysis["by_tool"])
        for tool in analysis["by_tool"]:
            analysis["by_tool"][tool]["types"] = dict(analysis["by_tool"][tool]["types"])
        analysis["by_type"] = dict(analysis["by_type"])
        analysis["by_hour"] = dict(analysis["by_hour"])
        analysis["by_day"] = dict(analysis["by_day"])
        analysis["common_messages"] = dict(analysis["common_messages"].most_common(10))
        analysis["common_args"] = dict(analysis["common_args"].most_common(10))
        
        return analysis
    
    def _find_failure_patterns(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify common failure patterns."""
        patterns = []
        
        # Pattern 1: File not found errors
        file_not_found = [e for e in errors if 'No such file' in e.get('error_message', '') 
                         or 'not found' in e.get('error_message', '').lower()]
        if file_not_found:
            patterns.append({
                "pattern": "File not found",
                "count": len(file_not_found),
                "tools": list(set(e['tool_name'] for e in file_not_found)),
                "suggestion": "Check file paths and ensure files exist before processing"
            })
        
        # Pattern 2: Permission errors
        permission_errors = [e for e in errors if 'Permission' in e.get('error_message', '')
                           or 'Access denied' in e.get('error_message', '')]
        if permission_errors:
            patterns.append({
                "pattern": "Permission denied",
                "count": len(permission_errors),
                "tools": list(set(e['tool_name'] for e in permission_errors)),
                "suggestion": "Check file permissions and user access rights"
            })
        
        # Pattern 3: Syntax/parsing errors
        parse_errors = [e for e in errors if 'SyntaxError' in e.get('error_type', '')
                       or 'parse' in e.get('error_message', '').lower()]
        if parse_errors:
            patterns.append({
                "pattern": "Parsing/Syntax errors",
                "count": len(parse_errors),
                "tools": list(set(e['tool_name'] for e in parse_errors)),
                "suggestion": "Validate input file syntax before processing"
            })
        
        # Pattern 4: Import errors
        import_errors = [e for e in errors if 'ImportError' in e.get('error_type', '')
                        or 'ModuleNotFoundError' in e.get('error_type', '')]
        if import_errors:
            patterns.append({
                "pattern": "Import/Module errors",
                "count": len(import_errors),
                "tools": list(set(e['tool_name'] for e in import_errors)),
                "suggestion": "Check Python dependencies and PYTHONPATH"
            })
        
        # Pattern 5: Memory/resource errors
        resource_errors = [e for e in errors if 'MemoryError' in e.get('error_type', '')
                          or 'too large' in e.get('error_message', '').lower()]
        if resource_errors:
            patterns.append({
                "pattern": "Memory/Resource exhaustion",
                "count": len(resource_errors),
                "tools": list(set(e['tool_name'] for e in resource_errors)),
                "suggestion": "Process large files in chunks or increase memory limits"
            })
        
        return patterns
    
    def get_tool_reliability(self, errors: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate reliability score for each tool based on error frequency."""
        # This would need success counts to be accurate, 
        # for now just show error counts
        tool_errors = defaultdict(int)
        for error in errors:
            tool_errors[error.get('tool_name', 'unknown')] += 1
            
        return dict(tool_errors)
    
    def format_report(self, analysis: Dict[str, Any]) -> str:
        """Format analysis results as a readable report."""
        lines = []
        lines.append("=" * 60)
        lines.append("PYTHON TOOLS ERROR ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # Summary
        lines.append(f"Total Errors: {analysis['total_errors']}")
        if analysis['time_range']:
            lines.append(f"Time Range: {analysis['time_range']['first']} to {analysis['time_range']['last']}")
            lines.append(f"Duration: {analysis['time_range']['duration_days']} days")
        lines.append("")
        
        # By Tool
        lines.append("ERRORS BY TOOL:")
        lines.append("-" * 40)
        for tool, data in sorted(analysis['by_tool'].items(), 
                                key=lambda x: x[1]['count'], reverse=True):
            lines.append(f"  {tool}: {data['count']} errors")
            for error_type, count in sorted(data['types'].items(), 
                                          key=lambda x: x[1], reverse=True)[:3]:
                lines.append(f"    - {error_type}: {count}")
        lines.append("")
        
        # By Error Type
        lines.append("TOP ERROR TYPES:")
        lines.append("-" * 40)
        for error_type, count in sorted(analysis['by_type'].items(), 
                                       key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  {error_type}: {count}")
        lines.append("")
        
        # Time Distribution
        lines.append("ERRORS BY HOUR OF DAY:")
        lines.append("-" * 40)
        for hour in range(24):
            count = analysis['by_hour'].get(hour, 0)
            if count > 0:
                bar = "█" * min(count, 50)
                lines.append(f"  {hour:02d}:00 {bar} ({count})")
        lines.append("")
        
        # Common Messages
        lines.append("COMMON ERROR MESSAGES:")
        lines.append("-" * 40)
        for msg, count in list(analysis['common_messages'].items())[:5]:
            lines.append(f"  '{msg}...': {count} times")
        lines.append("")
        
        # Failure Patterns
        if analysis['failure_patterns']:
            lines.append("IDENTIFIED FAILURE PATTERNS:")
            lines.append("-" * 40)
            for pattern in analysis['failure_patterns']:
                lines.append(f"  Pattern: {pattern['pattern']}")
                lines.append(f"  Count: {pattern['count']}")
                lines.append(f"  Tools: {', '.join(pattern['tools'])}")
                lines.append(f"  Suggestion: {pattern['suggestion']}")
                lines.append("")
        
        return "\n".join(lines)

def main():
    """Main entry point for error analysis."""
    parser = create_parser('Analyze Python tools error logs')
    parser.epilog = '''
EXAMPLES:
  # Show error summary
  analyze_errors.py --summary
  
  # Show most recent errors
  analyze_errors.py --recent 10
  
  # Analyze errors from last 7 days
  analyze_errors.py --days 7
  
  # Show detailed analysis for a specific tool
  analyze_errors.py --tool find_text.py
  
  # Show error patterns
  analyze_errors.py --patterns
  
  # Clear all error logs and reset counters
  analyze_errors.py --clear
  
  # Export analysis as JSON
  analyze_errors.py --json
'''
    
    parser.add_argument('--log-dir', help='Custom log directory')
    parser.add_argument('--days', type=int, help='Analyze errors from last N days')
    parser.add_argument('--tool', help='Filter by specific tool name')
    parser.add_argument('--summary', action='store_true', help='Show summary from summary log')
    parser.add_argument('--recent', type=int, help='Show N most recent errors')
    parser.add_argument('--patterns', action='store_true', help='Focus on failure patterns')
    parser.add_argument('--clear', action='store_true', help='Clear all error logs and reset counters')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet output')
    
    args = parser.parse_args()
    
    # Run preflight checks
    checks = []
    if hasattr(args, 'log_dir') and args.log_dir:
        checks.append((PreflightChecker.check_path_exists, (args.log_dir, "log directory")))
    
    if checks:
        run_preflight_checks(checks)
    
    analyzer = ErrorAnalyzer(args.log_dir)
    
    # Clear error logs if requested
    if args.clear:
        try:
            # Remove main error log file
            if analyzer.error_log.exists():
                analyzer.error_log.unlink()
                if not args.quiet:
                    print(f"Removed error log: {analyzer.error_log}")
            
            # Reset error summary
            clear_summary = {
                "cleared_at": datetime.now().isoformat() + "Z",
                "reason": "Manual clear via --clear flag",
                "total_errors": 0,
                "by_tool": {},
                "by_type": {},
                "first_error": None,
                "last_error": None
            }
            
            with open(analyzer.summary_log, 'w') as f:
                json.dump(clear_summary, f, indent=2)
            
            if not args.quiet:
                print(f"Reset error summary: {analyzer.summary_log}")
                print("✅ Error logs cleared successfully")
            
            return
            
        except Exception as e:
            print(f"❌ Error clearing logs: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Show summary
    if args.summary:
        if analyzer.summary_log.exists():
            with open(analyzer.summary_log, 'r') as f:
                summary = json.load(f)
            if args.json:
                print(json.dumps(summary, indent=2))
            else:
                print("ERROR SUMMARY")
                print("=" * 40)
                print(f"Total Errors: {summary.get('total_errors', 0)}")
                print(f"First Error: {summary.get('first_error', 'N/A')}")
                print(f"Last Error: {summary.get('last_error', 'N/A')}")
                print("\nBy Tool:")
                for tool, data in summary.get('by_tool', {}).items():
                    print(f"  {tool}: {data['count']}")
        else:
            print("No error summary found")
        return
    
    # Show recent errors
    if args.recent:
        from error_logger import get_logger
        logger = get_logger(args.log_dir)
        recent = logger.get_recent_errors(args.recent)
        
        if args.json:
            print(json.dumps(recent, indent=2))
        else:
            print(f"LAST {len(recent)} ERRORS")
            print("=" * 60)
            for error in recent:
                print(f"\nError ID: {error['error_id']}")
                print(f"Time: {error['timestamp']}")
                print(f"Tool: {error['tool_name']}")
                print(f"Type: {error['error_type']}")
                print(f"Message: {error['error_message']}")
                print(f"Args: {' '.join(error['command_args'])}")
        return
    
    # Load and analyze errors
    errors = analyzer.load_errors(args.days)
    
    # Filter by tool if specified
    if args.tool:
        errors = [e for e in errors if e.get('tool_name') == args.tool]
    
    if not errors:
        print("No errors found matching criteria")
        return
    
    # Analyze
    analysis = analyzer.analyze_patterns(errors)
    
    # Output
    if args.json:
        print(json.dumps(analysis, indent=2))
    elif args.patterns:
        # Focus on patterns
        print("FAILURE PATTERNS ANALYSIS")
        print("=" * 60)
        for pattern in analysis['failure_patterns']:
            print(f"\nPattern: {pattern['pattern']}")
            print(f"Occurrences: {pattern['count']}")
            print(f"Affected tools: {', '.join(pattern['tools'])}")
            print(f"Recommendation: {pattern['suggestion']}")
    else:
        # Full report
        report = analyzer.format_report(analysis)
        print(report)

if __name__ == "__main__":
    main()