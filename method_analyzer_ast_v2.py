#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
method_analyzer_ast v2 - AST-enhanced method analyzer with standardized interface.

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
from pathlib import Path
from collections import defaultdict, Counter
import json
import ast
import shutil
from typing import List, Dict, Set, Tuple, Optional

# Try to import javalang for Java AST support

# Import standard argument parser
try:
    from enhanced_standard_arg_parser import create_analyze_parser as create_parser
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

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

# Import standard parser
try:
    from standard_arg_parser import create_standard_parser, parse_standard_args
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False

# Import common utilities
try:
    from common_utils import check_ripgrep, detect_language, add_common_args
except ImportError:
    def check_ripgrep():
        if not shutil.which('rg'):
            print("Error: ripgrep (rg) is not installed.", file=sys.stderr)
            sys.exit(1)

# Import existing AST analyzers from original file
from earlierversions.method_analyzer_ast import (
    PythonCallAnalyzer, JavaCallAnalyzer, 
    analyze_method_body_ast, trace_method_flow_ast,
    format_ast_analysis_report, find_method_definition
)

def find_method_definition_standard(method_name: str, args) -> List[Dict]:
    """Find method definitions using standardized interface."""
    # Determine scope and language
    if args.file:
        scope = str(args.file)
    else:
        scope = args.scope or "."
    
    # Auto-detect language if needed
    language = getattr(args, 'type', 'auto')
    if language == 'auto':
        if args.file:
            file_str = str(args.file)
            if file_str.endswith('.py'):
                language = 'python'
            elif file_str.endswith('.java'):
                language = 'java'
            else:
                language = 'java'
        else:
            language = 'java'
    
    # Use the original find_method_definition function which works correctly
    return find_method_definition(method_name, scope, language)

def main():
    # Create parser based on availability
    if HAS_STANDARD_PARSER:
        parser = create_standard_parser(
            'analyze',
            'method_analyzer_ast v2 - AST-enhanced method analyzer',
            epilog='''
EXAMPLES:
  # Basic method analysis  
  # Analyze in specific file  
  # Analyze with call flow tracing  
  # JSON output for integration  
  # Language-specific analysis
AST SUPPORT:
  - Python: Built-in ast module (always available)
  - Java: javalang library (install: pip install javalang)
  - Others: Regex fallback with limited accuracy
            '''
        )
        
        # Add analyze-specific options not in standard parser
        parser.add_argument('--show-args', action='store_true', default=True,
                           help='Show method arguments (default: true)')
        parser.add_argument('--trace-flow', action='store_true',
                           help='Trace method call flow using AST')
        parser.add_argument('--ast-context', action='store_true',
                           help='Show AST context (class/method) for each result')
        
    else:
        # Fallback parser
        parser = argparse.ArgumentParser(description='method_analyzer_ast v2 - AST-enhanced method analyzer')
        parser.add_argument('target', help='Method name to analyze')
        parser.add_argument('--show-args', action='store_true', default=True)
        parser.add_argument('--trace-flow', action='store_true')
        parser.add_argument('--ast-context', action='store_true',
                           help='Show AST context (class/method) for each result')
    
    # Parse and validate
    if HAS_STANDARD_PARSER:
        args = parse_standard_args(parser, 'analyze')
    else:
        args = parser.parse_args()
    
    method_name = args.target
    
    try:
        # Find method definitions
        if not args.quiet:
            print(f"Searching for method '{method_name}'...", file=sys.stderr)
        
        definitions = find_method_definition_standard(method_name, args)
        
        if not definitions:
            print(f"No definitions found for method '{method_name}'")
            sys.exit(0)
        
        # Auto-detect language if needed
        language = getattr(args, 'type', 'auto')
        if language == 'auto' and definitions:
            first_file = definitions[0]['file']
            if first_file.endswith('.py'):
                language = 'python'
            elif first_file.endswith('.java'):
                language = 'java'
        
        # Trace flow if requested
        flow_analysis = None
        if args.trace_flow or args.show_callees:
            if not args.quiet:
                ast_status = "✨ AST available" if (language == 'python' or JAVALANG_AVAILABLE) else "⚠️ Using regex"
                print(f"Tracing call flow... {ast_status}", file=sys.stderr)
            
            scope = args.file or args.scope
            flow_analysis = trace_method_flow_ast(method_name, scope, language, args.max_depth)
        
        # Output results
        if args.json:
            # Analyze first definition for JSON output
            first_def = definitions[0]
            body_analysis = analyze_method_body_ast(first_def['file'], method_name, language)
            
            output = {
                'method': method_name,
                'definitions': definitions,
                'analysis': {
                    'total_calls': body_analysis.get('total_calls', 0),
                    'unique_methods': list(body_analysis.get('unique_methods', set())),
                    'call_frequency': dict(body_analysis.get('call_frequency', Counter())),
                    'ast_used': body_analysis.get('ast_used', False)
                },
                'flow': flow_analysis
            }
            
            if args.show_args:
                output['calls_with_args'] = body_analysis.get('calls_with_args', [])
            
            print(json.dumps(output, indent=2))
        else:
            # Format report
            show_ast_context = getattr(args, 'ast_context', False)
            report = format_ast_analysis_report(
                method_name, definitions, flow_analysis, args.show_args,
                show_ast_context
            )
            print(report)
    
    except KeyboardInterrupt:
        print("\\nAnalysis interrupted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()