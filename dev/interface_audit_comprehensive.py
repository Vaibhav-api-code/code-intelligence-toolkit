#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Comprehensive Interface Audit - Check ALL tools in run_any_python_tool.sh

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

class ToolInterfaceAuditor:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.tools_found = []
        self.standard_patterns = {
            'search': '<tool> <pattern> --file <file> | --scope <dir> [options]',
            'analyze': '<tool> <target> --file <file> | --scope <dir> [options]',
            'navigate': '<tool> <file> --to <target> | --line <num> [options]',
            'refactor': '<tool> <operation> <args> --file <file> | --scope <dir> [options]',
            'directory': '<tool> <path> [options]',
            'utility': '<tool> [command] [options]',
            'compare': '<tool> <file1> <file2> [options]'
        }
        
    def extract_tools_from_runner(self) -> List[Dict]:
        """Extract all tools mentioned in run_any_python_tool.sh"""
        runner_path = self.script_dir / "run_any_python_tool.sh"
        
        if not runner_path.exists():
            print(f"Error: {runner_path} not found")
            return []
        
        tools = []
        with open(runner_path, 'r') as f:
            content = f.read()
            
        # Find all .py tools mentioned
        import re
        
        # Pattern to find tool names in examples and descriptions
        tool_patterns = [
            r'(\w+\.py)',                    # Basic .py files
            r'echo\s+"[^"]*(\w+\.py)',      # In echo statements
            r'\$0\s+(\w+\.py)',             # In usage examples
            r'# (.+\.py) -',                # In commented examples
        ]
        
        found_tools = set()
        for pattern in tool_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    for m in match:
                        if m.endswith('.py'):
                            found_tools.add(m)
                elif match.endswith('.py'):
                    found_tools.add(match)
        
        # Extract examples for each tool
        for tool in sorted(found_tools):
            tool_info = self._analyze_tool_interface(tool, content)
            if tool_info:
                tools.append(tool_info)
                
        return tools
    
    def _analyze_tool_interface(self, tool_name: str, runner_content: str) -> Optional[Dict]:
        """Analyze a specific tool's interface pattern"""
        tool_path = self.script_dir / tool_name
        
        # Check if tool exists
        exists = tool_path.exists()
        
        # Extract examples from runner script
        examples = self._extract_examples(tool_name, runner_content)
        
        # Try to get help text if tool exists
        help_text = ""
        if exists:
            help_text = self._get_tool_help(tool_path)
        
        # Categorize tool type
        tool_type = self._categorize_tool(tool_name, examples, help_text)
        
        # Check if follows standard pattern
        follows_standard = self._check_standard_pattern(tool_type, examples)
        
        return {
            'name': tool_name,
            'exists': exists,
            'type': tool_type,
            'examples': examples,
            'follows_standard': follows_standard,
            'help_text': help_text[:200] + "..." if len(help_text) > 200 else help_text,
            'issues': self._identify_issues(tool_name, tool_type, examples)
        }
    
    def _extract_examples(self, tool_name: str, content: str) -> List[str]:
        """Extract usage examples for a specific tool"""
        examples = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if tool_name in line and ('$0' in line or 'echo' in line):
                # Clean up the example
                example = line.strip()
                example = example.replace('echo "', '').replace('"', '')
                example = example.replace('$0 ', '')
                if example.startswith('  '):
                    example = example[2:]
                if tool_name in example:
                    examples.append(example)
        
        return examples
    
    def _get_tool_help(self, tool_path: Path) -> str:
        """Get help text from a tool"""
        try:
            # Try with python3 first
            result = subprocess.run(['python3', str(tool_path), '--help'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout
            
            # Try direct execution
            result = subprocess.run([str(tool_path), '--help'], 
                                  capture_output=True, text=True, timeout=10)
            return result.stdout if result.returncode == 0 else result.stderr
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError):
            return ""
    
    def _categorize_tool(self, tool_name: str, examples: List[str], help_text: str) -> str:
        """Categorize tool by its primary function"""
        name_lower = tool_name.lower()
        
        # Directory tools
        if any(keyword in name_lower for keyword in ['ls', 'find_files', 'tree', 'dir_stats', 'recent_files']):
            return 'directory'
        
        # Search tools
        if any(keyword in name_lower for keyword in ['find_text', 'find_references', 'smart_find']):
            return 'search'
        
        # Navigate tools
        if any(keyword in name_lower for keyword in ['navigate', 'nav']):
            return 'navigate'
        
        # Refactor tools
        if any(keyword in name_lower for keyword in ['refactor', 'replace', 'ast_refactor', 'smart_refactor']):
            return 'refactor'
        
        # Compare tools
        if any(keyword in name_lower for keyword in ['diff', 'semantic_diff']):
            return 'compare'
        
        # Analyze tools
        if any(keyword in name_lower for keyword in ['analyze', 'analyzer', 'method_analyzer', 'trace', 'usage']):
            return 'analyze'
        
        # Utility tools
        return 'utility'
    
    def _check_standard_pattern(self, tool_type: str, examples: List[str]) -> bool:
        """Check if examples follow standard pattern for the tool type"""
        if not examples:
            return False
        
        for example in examples:
            parts = example.split()
            if len(parts) < 2:
                continue
                
            tool_name = parts[0]
            args = parts[1:]
            
            if tool_type == 'search':
                # Should be: <pattern> --file <file> | --scope <dir>
                if len(args) >= 1 and ('--file' in args or '--scope' in args):
                    return True
                    
            elif tool_type == 'analyze':
                # Should be: <target> --file <file> | --scope <dir>
                if len(args) >= 1 and ('--file' in args or '--scope' in args):
                    return True
                    
            elif tool_type == 'navigate':
                # Should be: <file> --to <target> | --line <num>
                if len(args) >= 2 and ('--to' in args or '--line' in args):
                    return True
                    
            elif tool_type == 'directory':
                # Should be: <path> [options] (positional path)
                if len(args) >= 1 and not args[0].startswith('-'):
                    return True
                    
            elif tool_type == 'compare':
                # Should be: <file1> <file2> [options]
                if len(args) >= 2 and not args[0].startswith('-') and not args[1].startswith('-'):
                    return True
        
        return False
    
    def _identify_issues(self, tool_name: str, tool_type: str, examples: List[str]) -> List[str]:
        """Identify specific interface issues"""
        issues = []
        
        if not examples:
            issues.append("No usage examples found")
            return issues
        
        for example in examples:
            parts = example.split()
            if len(parts) < 2:
                issues.append("Too few arguments in example")
                continue
                
            args = parts[1:]
            
            # Check for common issues by tool type
            if tool_type == 'search':
                if '--in-files' in args:
                    issues.append("Uses deprecated --in-files instead of --file")
                if '--file' not in args and '--scope' not in args:
                    issues.append("Missing location specification (--file or --scope)")
                    
            elif tool_type == 'analyze':
                if '--file' not in args and '--scope' not in args and tool_name not in ['analyze_errors.py']:
                    issues.append("Missing location specification (--file or --scope)")
                    
            elif tool_type == 'refactor':
                if tool_name == 'replace_text.py' and len(args) >= 3:
                    # Check for old pattern: <file> <old> <new>
                    if not args[0].startswith('-') and not args[1].startswith('-') and not args[2].startswith('-'):
                        issues.append("Uses old pattern: <file> <old> <new> instead of standardized refactor pattern")
                        
            elif tool_type == 'directory':
                if all(arg.startswith('-') for arg in args):
                    issues.append("Missing positional path argument")
        
        return issues
    
    def generate_report(self, tools: List[Dict]) -> str:
        """Generate comprehensive audit report"""
        report = []
        report.append("# Comprehensive Python Tools Interface Audit")
        report.append("=" * 60)
        report.append("")
        
        # Summary statistics
        total_tools = len(tools)
        existing_tools = sum(1 for t in tools if t['exists'])
        standard_tools = sum(1 for t in tools if t['follows_standard'])
        tools_with_examples = sum(1 for t in tools if t['examples'])
        
        report.append(f"## Summary Statistics")
        report.append(f"- Total tools found: {total_tools}")
        report.append(f"- Tools that exist: {existing_tools}")
        report.append(f"- Tools with examples: {tools_with_examples}")
        report.append(f"- Tools following standard: {standard_tools}")
        report.append(f"- Standardization rate: {standard_tools/total_tools*100:.1f}%")
        report.append("")
        
        # Group by type
        by_type = {}
        for tool in tools:
            tool_type = tool['type']
            if tool_type not in by_type:
                by_type[tool_type] = []
            by_type[tool_type].append(tool)
        
        report.append("## Tools by Category")
        report.append("")
        
        for tool_type in sorted(by_type.keys()):
            tools_in_type = by_type[tool_type]
            standard_in_type = sum(1 for t in tools_in_type if t['follows_standard'])
            
            report.append(f"### {tool_type.title()} Tools ({len(tools_in_type)} tools)")
            report.append(f"Standard pattern: `{self.standard_patterns.get(tool_type, 'Not defined')}`")
            report.append(f"Standardization: {standard_in_type}/{len(tools_in_type)} ({standard_in_type/len(tools_in_type)*100:.1f}%)")
            report.append("")
            
            for tool in sorted(tools_in_type, key=lambda x: x['name']):
                status = "✅" if tool['follows_standard'] else "❌"
                exists = "📁" if tool['exists'] else "❓"
                
                report.append(f"**{status} {exists} {tool['name']}**")
                
                if tool['examples']:
                    report.append("Examples:")
                    for example in tool['examples'][:2]:  # Limit to 2 examples
                        report.append(f"  `{example}`")
                else:
                    report.append("  No examples found")
                
                if tool['issues']:
                    report.append("Issues:")
                    for issue in tool['issues']:
                        report.append(f"  - {issue}")
                
                report.append("")
        
        # Non-standard tools that need attention
        report.append("## Priority Tools for Standardization")
        report.append("")
        
        non_standard = [t for t in tools if not t['follows_standard'] and t['exists'] and t['examples']]
        non_standard.sort(key=lambda x: len(x['issues']), reverse=True)
        
        for tool in non_standard[:10]:  # Top 10 priority
            report.append(f"### {tool['name']} ({tool['type']})")
            report.append(f"Issues: {', '.join(tool['issues'])}")
            if tool['examples']:
                report.append(f"Current: `{tool['examples'][0]}`")
            report.append(f"Should be: `{self.standard_patterns.get(tool['type'], 'Pattern TBD')}`")
            report.append("")
        
        return '\n'.join(report)
    
    def export_json(self, tools: List[Dict], filename: str):
        """Export audit results as JSON"""
        with open(filename, 'w') as f:
            json.dump(tools, f, indent=2)
        print(f"JSON export saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Audit Python tool interfaces')
    parser.add_argument('--json', help='Export JSON to file')
    parser.add_argument('--report', help='Save report to file')
    parser.add_argument('--summary', action='store_true', help='Show summary only')
    
    args = parser.parse_args()
    
    auditor = ToolInterfaceAuditor()
    tools = auditor.extract_tools_from_runner()
    
    if args.summary:
        total = len(tools)
        standard = sum(1 for t in tools if t['follows_standard'])
        print(f"Tool Interface Audit Summary:")
        print(f"Total tools: {total}")
        print(f"Following standard: {standard}")
        print(f"Standardization rate: {standard/total*100:.1f}%")
        return
    
    report = auditor.generate_report(tools)
    
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.report}")
    else:
        print(report)
    
    if args.json:
        auditor.export_json(tools, args.json)

if __name__ == "__main__":
    main()