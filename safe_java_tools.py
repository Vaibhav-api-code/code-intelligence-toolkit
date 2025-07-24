#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Safe Java Tools - A wrapper that validates structural integrity before running analysis tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
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
            'diff': './smart_diff.py'
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
                print("TOOL EXECUTION BLOCKED")
                print("=" * 80)
                print(f"Cannot run '{tool_name}' due to structural issues.")
                print("\nOptions:")
                print("  1. Fix the structural issues in the file(s)")
                print("  2. Use --force to run anyway (may cause tool errors)")
                print("  3. Use 'check-structure' tool for detailed analysis")
                return 1
        
        # Run the actual tool
        cmd = [tool_path] + args
        
        try:
            result = subprocess.run(cmd)
            return result.returncode
        except Exception as e:
            print(f"Error running tool: {e}")
            return 1
    
    def run_pipeline(self, pipeline_name, file_path, options=None):
        """Run predefined tool pipelines."""
        pipelines = {
            'analyze-all': [
                ('check-structure', []),
                ('extract-class', []),
                ('analyze-deps', []),
                ('unused-methods', []),
                ('refactor', ['--min-method-size', '30'])
            ],
            'refactor-assist': [
                ('check-structure', []),
                ('extract-class', []),
                ('internal-usage', []),
                ('unused-methods', []),
                ('refactor', [])
            ],
            'navigation': [
                ('check-structure', []),
                ('extract-class', []),
                ('navigate', ['--list'])
            ],
            'deep-analysis': [
                ('check-structure', []),
                ('extract-class', []),
                ('analyze-deps', ['--reverse']),
                ('trace', ['--max-depth', '5']),
                ('extract-block', ['--analyze'])
            ]
        }
        
        if pipeline_name not in pipelines:
            print(f"Unknown pipeline: {pipeline_name}")
            print(f"Available pipelines: {', '.join(pipelines.keys())}")
            return 1
        
        print(f"Running pipeline '{pipeline_name}' on {file_path}")
        print("=" * 80)
        
        # First, always check structure
        result = self.check_structure(file_path)
        print(self.format_structure_report(result, file_path))
        
        if not result['valid'] and not (options and options.get('force')):
            print("\nPipeline aborted due to structural issues")
            return 1
        
        # Run each tool in the pipeline
        for tool_name, tool_args in pipelines[pipeline_name]:
            if tool_name == 'check-structure':
                continue  # Already done
            
            print(f"\n>>> Running: {tool_name}")
            print("-" * 60)
            
            full_args = [file_path] + tool_args
            ret = self.run_tool(tool_name, full_args, force=True)  # Force since we already checked
            
            if ret != 0:
                print(f"\nWarning: {tool_name} returned error code {ret}")
                if not (options and options.get('continue_on_error')):
                    print("Pipeline aborted")
                    return ret
        
        print("\n" + "=" * 80)
        print("Pipeline completed successfully")
        return 0

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Safe Java Tools - Structure-validated tool execution')
    else:
        parser = argparse.ArgumentParser(description='Safe Java Tools - Structure-validated tool execution')
    
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
    
    # Run single tool
    return safe_tools.run_tool(args.tool, args.args, args.force)

if __name__ == "__main__":
    sys.exit(main())