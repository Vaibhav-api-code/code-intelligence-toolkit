#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Safe Java Tools - A wrapper that validates structural integrity before running analysis tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import subprocess
import argparse
from pathlib import Path
import json

# Import our structure checker
from check_java_structure import StructureChecker

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

class SafeJavaTools:
    def __init__(self):
        # Check if ripgrep is available
        import shutil
        has_ripgrep = shutil.which('rg') is not None
        
        self.tools = {
            'extract-methods': './extract_methods.py',
            'extract-class': './extract_class_structure.py',
            'find-refs': './find_references_rg.py' if has_ripgrep else './find_references.py',
            'analyze-deps': './analyze_dependencies_rg.py' if has_ripgrep else './analyze_dependencies.py',
            'unused-methods': './analyze_unused_methods_rg.py' if has_ripgrep else './analyze_unused_methods.py',
            'internal-usage': './analyze_internal_usage.py',
            'refactor': './suggest_refactoring.py',
            'navigate': './navigate.py',
            'trace': './trace_calls_rg.py' if has_ripgrep else './trace_calls.py',
            'extract-block': './extract_block.py',
            'diff': './smart_diff.py',
            'check-structure': None  # Special case, handled internally
        }
        
        # Tools that require valid structure
        self.structure_sensitive_tools = {
            'extract-methods', 'extract-class', 'extract-block', 
            'navigate', 'trace', 'refactor', 'internal-usage'
        }
    
    def check_structure(self, file_path):
        """Check if file has structural issues."""
        checker = StructureChecker()
        issues, warnings = checker.check_file(file_path)
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'error_count': len(issues),
            'warning_count': len(warnings)
        }
    
    def format_structure_report(self, result, file_path):
        """Format structure check results."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"STRUCTURE VALIDATION: {file_path}")
        lines.append("=" * 80)
        
        if result['valid']:
            lines.append("✓ Structure is valid - safe to proceed")
            if result['warning_count'] > 0:
                lines.append(f"  Note: {result['warning_count']} warnings found (non-blocking)")
        else:
            lines.append(f"✗ Structure validation FAILED - {result['error_count']} errors found")
            lines.append("\nERRORS:")
            for issue in result['issues']:
                lines.append(f"  Line {issue['line']}: {issue['type']}")
                lines.append(f"    {issue['message']}")
        
        return "\n".join(lines)
    
    def run_tool(self, tool_name, args, force=False):
        """Run a tool with optional structure checking."""
        if tool_name not in self.tools:
            print(f"Error: Unknown tool '{tool_name}'")
            print(f"Available tools: {', '.join(self.tools.keys())}")
            return 1
        
        tool_path = self.tools[tool_name]
        
        # Check if this tool needs structure validation
        needs_validation = tool_name in self.structure_sensitive_tools
        java_files = []
        
        if needs_validation and not force:
            # Find Java files in arguments
            for arg in args:
                if arg.endswith('.java') and Path(arg).exists():
                    java_files.append(arg)
            
            # Validate each Java file
            all_valid = True
            for java_file in java_files:
                result = self.check_structure(java_file)
                
                if not result['valid']:
                    print(self.format_structure_report(result, java_file))
                    all_valid = False
                elif result['warning_count'] > 0 and not force:
                    print(self.format_structure_report(result, java_file))
            
            if not all_valid:
                print("\n" + "=" * 80)
                print("Tool execution blocked due to structural issues.")
                print("Use --force to bypass this check (may cause incorrect results).")
                return 1
        
        # Run the tool
        try:
            cmd = [sys.executable, tool_path] + args
            result = subprocess.run(cmd)
            return result.returncode
        except Exception as e:
            print(f"Error running tool: {e}")
            return 1
    
    def run_pipeline(self, pipeline_name, file_path, options):
        """Run a predefined pipeline of tools."""
        pipelines = {
            'analyze-all': [
                ('check-structure', [file_path]),
                ('extract-class', [file_path]),
                ('unused-methods', [file_path]),
                ('internal-usage', [file_path]),
                ('analyze-deps', [file_path]),
                ('refactor', [file_path])
            ],
            'refactor-assist': [
                ('check-structure', [file_path]),
                ('unused-methods', [file_path]),
                ('internal-usage', [file_path]),
                ('refactor', [file_path])
            ],
            'navigation': [
                ('check-structure', [file_path]),
                ('navigate', [file_path, '--list']),
                ('extract-class', [file_path])
            ],
            'deep-analysis': [
                ('check-structure', [file_path]),
                ('extract-class', [file_path]),
                ('analyze-deps', [file_path]),
                ('trace', ['main', '--file', file_path]),
                ('refactor', [file_path])
            ]
        }
        
        if pipeline_name not in pipelines:
            print(f"Error: Unknown pipeline '{pipeline_name}'")
            print(f"Available pipelines: {', '.join(pipelines.keys())}")
            return 1
        
        print(f"Running pipeline: {pipeline_name}")
        print("=" * 80)
        
        pipeline = pipelines[pipeline_name]
        for i, (tool_name, tool_args) in enumerate(pipeline, 1):
            print(f"\n[{i}/{len(pipeline)}] Running: {tool_name}")
            print("-" * 80)
            
            if tool_name == 'check-structure':
                # Handle check-structure specially
                result = self.check_structure(tool_args[0])
                print(self.format_structure_report(result, tool_args[0]))
                if not result['valid'] and not options.get('force'):
                    if not options.get('continue_on_error'):
                        print("\nPipeline aborted due to structure errors.")
                        return 1
            else:
                ret = self.run_tool(tool_name, tool_args, options.get('force', False))
                if ret != 0 and not options.get('continue_on_error'):
                    print(f"\nPipeline aborted due to error in {tool_name}.")
                    return ret
        
        print("\n" + "=" * 80)
        print(f"Pipeline '{pipeline_name}' completed successfully.")
        return 0

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Safe Java Tools - Run Java analysis tools with structure validation')
    else:
        parser = argparse.ArgumentParser(description='Safe Java Tools - Run Java analysis tools with structure validation')
    
    parser.add_argument('tool', nargs='?', help='Tool to run or "check-structure"')
    parser.add_argument('args', nargs='*', help='Arguments for the tool')
    parser.add_argument('--force', action='store_true',
                       help='Force execution even with structure errors')
    parser.add_argument('--pipeline', 
                       help='Run a predefined pipeline instead of a single tool')
    parser.add_argument('--continue-on-error', action='store_true',
                       help='Continue pipeline even if a tool fails')
    
    args = parser.parse_args()
    
    safe_tools = SafeJavaTools()
    
    # Check if running a pipeline
    if args.pipeline:
        # When using --pipeline, the file is in 'tool' argument
        file_path = args.tool if args.tool else (args.args[0] if args.args else None)
        if not file_path:
            print("Error: No file specified for pipeline")
            return 1
        
        options = {
            'force': args.force,
            'continue_on_error': args.continue_on_error
        }
        
        return safe_tools.run_pipeline(args.pipeline, file_path, options)
    
    # Must have a tool specified if not running a pipeline
    if not args.tool:
        parser.print_help()
        return 1
    
    # Special handling for check-structure
    if args.tool == 'check-structure':
        if not args.args:
            print("Error: No file specified for structure check")
            return 1
        
        for file_path in args.args:
            if not Path(file_path).exists():
                print(f"Error: File '{file_path}' not found")
                continue
            
            result = safe_tools.check_structure(file_path)
            print(safe_tools.format_structure_report(result, file_path))
            
            if not result['valid']:
                return 1
        return 0
    
    # Run single tool
    return safe_tools.run_tool(args.tool, args.args, args.force)

if __name__ == "__main__":
    sys.exit(main())