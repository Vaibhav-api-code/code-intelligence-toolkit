#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced error analyzer for Python tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
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
from typing import List, Dict, Any, Optional, Tuple
import re
import subprocess

# Import common utilities
try:
    from common_utils import normalize_path, setup_logging, format_size
    HAS_COMMON_UTILS = True
except ImportError:
    HAS_COMMON_UTILS = False
    def normalize_path(path):
        return os.path.abspath(os.path.expanduser(path))
    def setup_logging(name):
        import logging
        return logging.getLogger(name)
    def format_size(size):
        return f"{size:,}"

class ErrorAnalyzer:
    """Enhanced error analyzer with comprehensive features."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize analyzer with log directory."""
        if log_dir:
            self.log_dir = Path(normalize_path(log_dir))
        else:
            home = Path.home()
            self.log_dir = home / ".pytoolserrors"
            
        self.error_log = self.log_dir / "errors.jsonl"
        self.summary_log = self.log_dir / "error_summary.json"
        self.logger = setup_logging(__name__)
        
    def load_errors(self, 
                   days: Optional[int] = None,
                   hours: Optional[int] = None,
                   tool: Optional[str] = None,
                   error_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load errors with flexible filtering."""
        errors = []
        
        if not self.error_log.exists():
            self.logger.warning(f"Error log not found: {self.error_log}")
            return errors
            
        cutoff = None
        if days:
            cutoff = datetime.now() - timedelta(days=days)
        elif hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            
        with open(self.error_log, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    error = json.loads(line)
                    
                    # Apply time filter
                    if cutoff:
                        error_time = datetime.fromisoformat(
                            error['timestamp'].replace('Z', '+00:00').replace('+00:00', '')
                        )
                        if error_time < cutoff:
                            continue
                    
                    # Apply tool filter
                    if tool and error.get('tool_name', '') != tool:
                        continue
                        
                    # Apply error type filter
                    if error_type and error.get('error_type', '') != error_type:
                        continue
                        
                    errors.append(error)
                except Exception as e:
                    self.logger.debug(f"Skipping invalid error at line {line_num}: {e}")
                    
        return errors
    
    def get_recent_errors(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the N most recent errors."""
        errors = self.load_errors()
        return errors[-count:] if errors else []
    
    def analyze_error_patterns(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error patterns and generate insights."""
        if not errors:
            return {"error": "No errors to analyze"}
            
        analysis = {
            "summary": {
                "total_errors": len(errors),
                "unique_tools": len(set(e.get('tool_name', 'unknown') for e in errors)),
                "unique_error_types": len(set(e.get('error_type', 'unknown') for e in errors)),
            },
            "time_analysis": self._analyze_time_patterns(errors),
            "tool_analysis": self._analyze_by_tool(errors),
            "error_type_analysis": self._analyze_by_type(errors),
            "common_failures": self._analyze_common_failures(errors),
            "recommendations": self._generate_recommendations(errors)
        }
        
        return analysis
    
    def _analyze_time_patterns(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in errors."""
        timestamps = []
        for e in errors:
            try:
                ts = datetime.fromisoformat(
                    e['timestamp'].replace('Z', '+00:00').replace('+00:00', '')
                )
                timestamps.append(ts)
            except:
                pass
                
        if not timestamps:
            return {}
            
        return {
            "first_error": min(timestamps).isoformat(),
            "last_error": max(timestamps).isoformat(),
            "duration": str(max(timestamps) - min(timestamps)),
            "errors_per_hour": self._calculate_error_rate(timestamps, 'hour'),
            "errors_per_day": self._calculate_error_rate(timestamps, 'day'),
            "peak_hour": self._find_peak_time(timestamps, 'hour'),
            "peak_day": self._find_peak_time(timestamps, 'day')
        }
    
    def _calculate_error_rate(self, timestamps: List[datetime], unit: str) -> float:
        """Calculate error rate per time unit."""
        if not timestamps:
            return 0.0
            
        duration = max(timestamps) - min(timestamps)
        if unit == 'hour':
            hours = duration.total_seconds() / 3600
            return len(timestamps) / max(hours, 1)
        elif unit == 'day':
            days = duration.days or 1
            return len(timestamps) / days
        return 0.0
    
    def _find_peak_time(self, timestamps: List[datetime], unit: str) -> str:
        """Find peak error time."""
        if not timestamps:
            return "N/A"
            
        if unit == 'hour':
            hours = Counter(ts.hour for ts in timestamps)
            peak_hour = hours.most_common(1)[0][0]
            return f"{peak_hour:02d}:00"
        elif unit == 'day':
            days = Counter(ts.strftime('%A') for ts in timestamps)
            return days.most_common(1)[0][0] if days else "N/A"
        return "N/A"
    
    def _analyze_by_tool(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze errors by tool."""
        tool_stats = defaultdict(lambda: {
            "count": 0,
            "error_types": Counter(),
            "exit_codes": Counter(),
            "common_args": Counter()
        })
        
        for error in errors:
            tool = error.get('tool_name', 'unknown')
            stats = tool_stats[tool]
            stats["count"] += 1
            stats["error_types"][error.get('error_type', 'unknown')] += 1
            
            # Exit codes
            exit_code = error.get('additional_context', {}).get('exit_code')
            if exit_code is not None:
                stats["exit_codes"][exit_code] += 1
                
            # Common arguments
            args = error.get('command_args', [])
            if args:
                arg_str = ' '.join(args[:3])  # First 3 args
                stats["common_args"][arg_str] += 1
        
        # Convert to regular dict and limit common args
        result = {}
        for tool, stats in tool_stats.items():
            result[tool] = {
                "count": stats["count"],
                "error_types": dict(stats["error_types"]),
                "exit_codes": dict(stats["exit_codes"]),
                "top_args": dict(stats["common_args"].most_common(3))
            }
            
        return result
    
    def _analyze_by_type(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze errors by type."""
        type_stats = defaultdict(lambda: {
            "count": 0,
            "tools": Counter(),
            "messages": Counter()
        })
        
        for error in errors:
            error_type = error.get('error_type', 'unknown')
            stats = type_stats[error_type]
            stats["count"] += 1
            stats["tools"][error.get('tool_name', 'unknown')] += 1
            
            # Common messages
            msg = error.get('error_message', '')
            if msg:
                # Normalize message
                msg = re.sub(r'line \d+', 'line N', msg)
                msg = re.sub(r'code \d+', 'code N', msg)
                stats["messages"][msg[:50]] += 1
        
        # Convert to regular dict
        result = {}
        for error_type, stats in type_stats.items():
            result[error_type] = {
                "count": stats["count"],
                "affected_tools": dict(stats["tools"]),
                "top_messages": dict(stats["messages"].most_common(3))
            }
            
        return result
    
    def _analyze_common_failures(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify common failure patterns."""
        patterns = []
        
        # Pattern 1: Missing required arguments
        arg_errors = [e for e in errors if 'required' in e.get('stack_trace', '')]
        if arg_errors:
            patterns.append({
                "pattern": "Missing required arguments",
                "frequency": len(arg_errors),
                "affected_tools": list(set(e.get('tool_name', 'unknown') for e in arg_errors)),
                "example": arg_errors[0].get('stack_trace', '')[:200]
            })
        
        # Pattern 2: File not found
        file_errors = [e for e in errors if 'not found' in e.get('error_message', '').lower()]
        if file_errors:
            patterns.append({
                "pattern": "File not found errors",
                "frequency": len(file_errors),
                "affected_tools": list(set(e.get('tool_name', 'unknown') for e in file_errors)),
                "example": file_errors[0].get('error_message', '')
            })
        
        # Pattern 3: JSON parsing errors
        json_errors = [e for e in errors if 'json' in e.get('error_message', '').lower()]
        if json_errors:
            patterns.append({
                "pattern": "JSON parsing errors",
                "frequency": len(json_errors),
                "affected_tools": list(set(e.get('tool_name', 'unknown') for e in json_errors)),
                "example": json_errors[0].get('error_message', '')
            })
        
        # Pattern 4: Exit code 2 (usually argument errors)
        exit2_errors = [e for e in errors if e.get('additional_context', {}).get('exit_code') == 2]
        if exit2_errors:
            patterns.append({
                "pattern": "Argument parsing errors (exit code 2)",
                "frequency": len(exit2_errors),
                "affected_tools": list(set(e.get('tool_name', 'unknown') for e in exit2_errors)),
                "common_cause": "Invalid or missing command line arguments"
            })
        
        return sorted(patterns, key=lambda x: x['frequency'], reverse=True)
    
    def _generate_recommendations(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on error analysis."""
        recommendations = []
        
        # Check for high error rate
        if len(errors) > 100:
            recommendations.append(
                "High error volume detected. Consider reviewing tool documentation and common usage patterns."
            )
        
        # Check for repeated errors
        tool_counts = Counter(e.get('tool_name', 'unknown') for e in errors)
        for tool, count in tool_counts.most_common(3):
            if count > 10:
                recommendations.append(
                    f"Tool '{tool}' has {count} errors. Review its argument syntax and usage examples."
                )
        
        # Check for argument errors
        arg_errors = sum(1 for e in errors if e.get('additional_context', {}).get('exit_code') == 2)
        if arg_errors > len(errors) * 0.3:
            recommendations.append(
                "Many argument parsing errors detected. Use --help flag to check correct syntax."
            )
        
        # Check for file errors
        file_errors = sum(1 for e in errors if 'not found' in e.get('error_message', '').lower())
        if file_errors > 5:
            recommendations.append(
                "Multiple file not found errors. Verify file paths and use auto-discovery features."
            )
        
        return recommendations
    
    def format_analysis_report(self, analysis: Dict[str, Any], format_type: str = 'text') -> str:
        """Format analysis report for output."""
        if format_type == 'json':
            return json.dumps(analysis, indent=2, default=str)
            
        # Text format
        lines = []
        
        # Summary
        summary = analysis.get('summary', {})
        lines.append("ERROR ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"Total Errors: {summary.get('total_errors', 0)}")
        lines.append(f"Unique Tools: {summary.get('unique_tools', 0)}")
        lines.append(f"Error Types: {summary.get('unique_error_types', 0)}")
        lines.append("")
        
        # Time Analysis
        time_analysis = analysis.get('time_analysis', {})
        if time_analysis:
            lines.append("Time Analysis:")
            lines.append("-" * 40)
            lines.append(f"Period: {time_analysis.get('first_error', 'N/A')} to {time_analysis.get('last_error', 'N/A')}")
            lines.append(f"Duration: {time_analysis.get('duration', 'N/A')}")
            lines.append(f"Error Rate: {time_analysis.get('errors_per_hour', 0):.1f} per hour")
            lines.append(f"Peak Hour: {time_analysis.get('peak_hour', 'N/A')}")
            lines.append("")
        
        # Top Tools with Errors
        tool_analysis = analysis.get('tool_analysis', {})
        if tool_analysis:
            lines.append("Top Tools with Errors:")
            lines.append("-" * 40)
            sorted_tools = sorted(tool_analysis.items(), key=lambda x: x[1]['count'], reverse=True)
            for tool, stats in sorted_tools[:5]:
                lines.append(f"{tool}: {stats['count']} errors")
                if stats.get('exit_codes'):
                    codes = ', '.join(f"code {k}: {v}" for k, v in stats['exit_codes'].items())
                    lines.append(f"  Exit codes: {codes}")
            lines.append("")
        
        # Common Failure Patterns
        patterns = analysis.get('common_failures', [])
        if patterns:
            lines.append("Common Failure Patterns:")
            lines.append("-" * 40)
            for i, pattern in enumerate(patterns[:5], 1):
                lines.append(f"{i}. {pattern['pattern']} ({pattern['frequency']} occurrences)")
                if 'affected_tools' in pattern:
                    tools = ', '.join(pattern['affected_tools'][:3])
                    lines.append(f"   Affected tools: {tools}")
            lines.append("")
        
        # Recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            lines.append("Recommendations:")
            lines.append("-" * 40)
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def format_recent_errors(self, errors: List[Dict[str, Any]]) -> str:
        """Format recent errors for display."""
        if not errors:
            return "No recent errors found."
            
        lines = []
        lines.append(f"LAST {len(errors)} ERRORS")
        lines.append("=" * 80)
        lines.append("")
        
        for error in errors:
            lines.append(f"Error ID: {error.get('error_id', 'N/A')}")
            lines.append(f"Time: {error.get('timestamp', 'N/A')}")
            lines.append(f"Tool: {error.get('tool_name', 'unknown')}")
            lines.append(f"Type: {error.get('error_type', 'unknown')}")
            lines.append(f"Message: {error.get('error_message', 'No message')}")
            
            args = error.get('command_args', [])
            if args:
                lines.append(f"Args: {' '.join(args)}")
                
            exit_code = error.get('additional_context', {}).get('exit_code')
            if exit_code is not None:
                lines.append(f"Exit Code: {exit_code}")
                
            # Show first line of error if available
            stderr = error.get('additional_context', {}).get('stderr', '')
            if stderr:
                first_line = stderr.split('\n')[0]
                if first_line:
                    lines.append(f"Error: {first_line}")
                    
            lines.append("")
        
        return '\n'.join(lines)
    
    def clear_old_errors(self, days: int = 30) -> Tuple[int, int]:
        """Clear errors older than specified days."""
        if not self.error_log.exists():
            return 0, 0
            
        cutoff = datetime.now() - timedelta(days=days)
        kept_errors = []
        removed_count = 0
        
        with open(self.error_log, 'r') as f:
            for line in f:
                try:
                    error = json.loads(line)
                    error_time = datetime.fromisoformat(
                        error['timestamp'].replace('Z', '+00:00').replace('+00:00', '')
                    )
                    if error_time >= cutoff:
                        kept_errors.append(line.strip())
                    else:
                        removed_count += 1
                except:
                    # Keep malformed entries
                    kept_errors.append(line.strip())
        
        # Write back kept errors
        with open(self.error_log, 'w') as f:
            for line in kept_errors:
                f.write(line + '\n')
                
        return removed_count, len(kept_errors)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Enhanced error analyzer for Python tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
EXAMPLES:
  # Show most recent errors
  error_analyzer.py --recent 10
  
  # Analyze errors from last 24 hours
  error_analyzer.py --hours 24
  
  # Analyze errors for specific tool
  error_analyzer.py --tool find_text.py
  
  # Show comprehensive analysis
  error_analyzer.py --analyze
  
  # Clear old errors
  error_analyzer.py --clear-old 30
  
  # Export analysis as JSON
  error_analyzer.py --analyze --json
'''
    )
    
    # Time filters
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument('--days', type=int, help='Analyze errors from last N days')
    time_group.add_argument('--hours', type=int, help='Analyze errors from last N hours')
    time_group.add_argument('--recent', type=int, help='Show N most recent errors')
    
    # Other filters
    parser.add_argument('--tool', help='Filter by specific tool name')
    parser.add_argument('--type', help='Filter by error type')
    
    # Actions
    parser.add_argument('--analyze', action='store_true', 
                       help='Perform comprehensive analysis')
    parser.add_argument('--clear-old', type=int, metavar='DAYS',
                       help='Clear errors older than N days')
    
    # Output options
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--log-dir', help='Custom log directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = ErrorAnalyzer(args.log_dir)
    
    # Handle clear old errors
    if args.clear_old:
        removed, kept = analyzer.clear_old_errors(args.clear_old)
        print(f"Removed {removed} old errors, kept {kept} recent errors.")
        return
    
    # Handle recent errors display
    if args.recent:
        errors = analyzer.get_recent_errors(args.recent)
        print(analyzer.format_recent_errors(errors))
        return
    
    # Load errors with filters
    errors = analyzer.load_errors(
        days=args.days,
        hours=args.hours,
        tool=args.tool,
        error_type=args.type
    )
    
    if not errors:
        print("No errors found matching the criteria.")
        return
    
    # Perform analysis if requested or by default
    if args.analyze or not args.recent:
        analysis = analyzer.analyze_error_patterns(errors)
        output = analyzer.format_analysis_report(
            analysis, 
            format_type='json' if args.json else 'text'
        )
        print(output)
    else:
        # Just show count
        print(f"Found {len(errors)} errors matching the criteria.")


if __name__ == '__main__':
    main()