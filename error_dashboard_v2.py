#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Error Dashboard V2 - Visual summary of tool errors with actionable insights.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional
import textwrap

class ErrorDashboard:
    """Dashboard for visualizing and analyzing tool errors."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize dashboard with log directory."""
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".pytoolserrors"
            
        self.error_log = self.log_dir / "errors.jsonl"
        self.summary_log = self.log_dir / "error_summary.json"
    
    def load_errors(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load errors from log file."""
        errors = []
        
        if not self.error_log.exists():
            return errors
            
        cutoff = None
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            
        with open(self.error_log, 'r') as f:
            for line in f:
                try:
                    error = json.loads(line.strip())
                    if cutoff:
                        error_time = datetime.fromisoformat(
                            error['timestamp'].replace('Z', '+00:00').replace('+00:00', '')
                        )
                        if error_time < cutoff:
                            continue
                    errors.append(error)
                except:
                    pass
                    
        return errors
    
    def create_dashboard(self, errors: List[Dict[str, Any]], recent: Optional[int] = None) -> str:
        """Create visual dashboard from errors."""
        if recent:
            errors = errors[-recent:] if len(errors) > recent else errors
            
        if not errors:
            return "No errors found to display."
            
        lines = []
        
        # Header
        lines.append("╔" + "═" * 78 + "╗")
        lines.append("║" + "ERROR DASHBOARD".center(78) + "║")
        lines.append("╠" + "═" * 78 + "╣")
        
        # Summary
        total = len(errors)
        tools = len(set(e.get('tool_name', 'unknown') for e in errors))
        types = len(set(e.get('error_type', 'unknown') for e in errors))
        
        if errors:
            first_time = datetime.fromisoformat(
                errors[0]['timestamp'].replace('Z', '+00:00').replace('+00:00', '')
            )
            last_time = datetime.fromisoformat(
                errors[-1]['timestamp'].replace('Z', '+00:00').replace('+00:00', '')
            )
            duration = last_time - first_time
            
            lines.append(f"║ Total Errors: {total:<20} Time Span: {duration}".ljust(79) + "║")
            lines.append(f"║ Unique Tools: {tools:<20} Error Types: {types}".ljust(79) + "║")
        
        lines.append("╠" + "═" * 78 + "╣")
        
        # Top Tools
        tool_counts = Counter(e.get('tool_name', 'unknown') for e in errors)
        lines.append("║ TOP TOOLS WITH ERRORS".ljust(79) + "║")
        lines.append("║" + "-" * 78 + "║")
        
        for tool, count in tool_counts.most_common(5):
            bar_length = int(count / total * 40)
            bar = "█" * bar_length
            lines.append(f"║ {tool:<30} {bar:<40} {count:>3}".ljust(79) + "║")
        
        lines.append("╠" + "═" * 78 + "╣")
        
        # Error Types
        type_counts = Counter(e.get('error_type', 'unknown') for e in errors)
        lines.append("║ ERROR TYPES".ljust(79) + "║")
        lines.append("║" + "-" * 78 + "║")
        
        for error_type, count in type_counts.most_common():
            percentage = count / total * 100
            lines.append(f"║ {error_type:<40} {count:>5} ({percentage:>5.1f}%)".ljust(79) + "║")
        
        lines.append("╠" + "═" * 78 + "╣")
        
        # Recent Errors
        lines.append("║ RECENT ERRORS".ljust(79) + "║")
        lines.append("║" + "-" * 78 + "║")
        
        for error in errors[-5:]:
            time_str = error.get('timestamp', 'N/A')[:19]
            tool = error.get('tool_name', 'unknown')
            msg = error.get('error_message', 'No message')[:40]
            lines.append(f"║ {time_str} {tool:<20} {msg}".ljust(79) + "║")
        
        lines.append("╠" + "═" * 78 + "╣")
        
        # Recommendations
        lines.append("║ RECOMMENDATIONS".ljust(79) + "║")
        lines.append("║" + "-" * 78 + "║")
        
        recommendations = self._generate_recommendations(errors)
        for i, rec in enumerate(recommendations[:3], 1):
            wrapped = textwrap.wrap(rec, width=75)
            for j, line in enumerate(wrapped):
                if j == 0:
                    lines.append(f"║ {i}. {line}".ljust(79) + "║")
                else:
                    lines.append(f"║    {line}".ljust(79) + "║")
        
        # Footer
        lines.append("╚" + "═" * 78 + "╝")
        
        return '\n'.join(lines)
    
    def _generate_recommendations(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Check for high frequency tools
        tool_counts = Counter(e.get('tool_name', 'unknown') for e in errors)
        for tool, count in tool_counts.most_common(2):
            if count > 5:
                recommendations.append(
                    f"Tool '{tool}' has {count} errors. Run '{tool} --help' to review usage."
                )
        
        # Check for argument errors
        arg_errors = sum(1 for e in errors 
                        if e.get('additional_context', {}).get('exit_code') == 2)
        if arg_errors > len(errors) * 0.3:
            recommendations.append(
                "Many argument errors detected. Check tool documentation for correct syntax."
            )
        
        # Check for recent spike
        if len(errors) > 10:
            recent = errors[-10:]
            recent_time = datetime.fromisoformat(
                recent[0]['timestamp'].replace('Z', '+00:00').replace('+00:00', '')
            )
            last_time = datetime.fromisoformat(
                recent[-1]['timestamp'].replace('Z', '+00:00').replace('+00:00', '')
            )
            if (last_time - recent_time).total_seconds() < 300:  # 5 minutes
                recommendations.append(
                    "Error spike detected. Consider reviewing recent changes or tool updates."
                )
        
        return recommendations
    
    def export_summary(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export error summary as structured data."""
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_errors": len(errors),
            "time_range": {
                "start": errors[0]['timestamp'] if errors else None,
                "end": errors[-1]['timestamp'] if errors else None
            },
            "by_tool": dict(Counter(e.get('tool_name', 'unknown') for e in errors)),
            "by_type": dict(Counter(e.get('error_type', 'unknown') for e in errors)),
            "by_exit_code": dict(Counter(
                e.get('additional_context', {}).get('exit_code', 'N/A') for e in errors
            )),
            "recommendations": self._generate_recommendations(errors)
        }
        
        return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Error Dashboard V2 - Visual error analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
EXAMPLES:
  # Show dashboard for all errors
  error_dashboard_v2.py
  
  # Show dashboard for last 7 days
  error_dashboard_v2.py --days 7
  
  # Show only recent 20 errors
  error_dashboard_v2.py --recent 20
  
  # Export summary as JSON
  error_dashboard_v2.py --export summary.json
  
  # Use custom log directory
  error_dashboard_v2.py --log-dir /path/to/logs
'''
    )
    
    parser.add_argument('--days', type=int, help='Analyze errors from last N days')
    parser.add_argument('--recent', type=int, help='Show only N most recent errors')
    parser.add_argument('--log-dir', help='Custom log directory')
    parser.add_argument('--clear', action='store_true', help='Clear all error logs and reset dashboard')
    parser.add_argument('--export', help='Export summary to JSON file')
    parser.add_argument('--json', action='store_true', help='Output dashboard data as JSON')
    
    args = parser.parse_args()
    
    # Initialize dashboard
    dashboard = ErrorDashboard(args.log_dir)
    
    # Clear error logs if requested
    if args.clear:
        try:
            # Remove main error log file
            if dashboard.error_log.exists():
                dashboard.error_log.unlink()
                print(f"Removed error log: {dashboard.error_log}")
            
            # Reset error summary
            from datetime import datetime
            import json
            clear_summary = {
                "cleared_at": datetime.now().isoformat() + "Z",
                "reason": "Manual clear via error dashboard --clear flag",
                "total_errors": 0,
                "by_tool": {},
                "by_type": {},
                "first_error": None,
                "last_error": None
            }
            
            with open(dashboard.summary_log, 'w') as f:
                json.dump(clear_summary, f, indent=2)
            
            print(f"Reset error summary: {dashboard.summary_log}")
            print("✅ Error dashboard cleared successfully")
            return
            
        except Exception as e:
            print(f"❌ Error clearing dashboard: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Load errors
    errors = dashboard.load_errors(args.days)
    
    if not errors:
        print("No errors found in the log.")
        return
    
    # Export summary if requested
    if args.export:
        summary = dashboard.export_summary(errors)
        with open(args.export, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary exported to {args.export}")
        return
    
    # Output as JSON if requested
    if args.json:
        summary = dashboard.export_summary(errors)
        print(json.dumps(summary, indent=2))
        return
    
    # Create and display dashboard
    output = dashboard.create_dashboard(errors, recent=args.recent)
    print(output)


if __name__ == '__main__':
    main()