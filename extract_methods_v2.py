#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Extract specific methods from Java files, even when the files are too large to read directly.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
from pathlib import Path
import re
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

try:
    import javalang
    HAS_JAVALANG = True
except ImportError:
    HAS_JAVALANG = False

try:
    from java_parsing_utils import find_closing_brace
except ImportError:
    def find_closing_brace(content, start_pos):
        """Simple brace matcher fallback."""
        brace_count = 1
        pos = start_pos + 1
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        return pos if brace_count == 0 else -1

def extract_method_regex(file_path, method_name, include_javadoc=True):
    """Extract method using regex (fallback when javalang not available)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to find methods with the specific name
        method_pattern = rf'(?:(?:\/\*\*[\s\S]*?\*\/)\s*)?(?:@\w+(?:\([^)]*\))?\s*)*((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.]+\s+)?)?{re.escape(method_name)}\s*\([^)]*\)(?:\s+throws\s+[^{{]+)?\s*\{{'
        
        results = []
        
        for match in re.finditer(method_pattern, content, re.MULTILINE | re.DOTALL):
            start_pos = match.start()
            brace_pos = match.end() - 1
            
            # Find the complete method body
            end_pos = find_closing_brace(content, brace_pos)
            if end_pos == -1:
                continue
                
            # Extract the method
            method_content = content[start_pos:end_pos]
            
            # Get line numbers
            start_line = content[:start_pos].count('\n') + 1
            end_line = content[:end_pos].count('\n') + 1
            
            # Get method signature
            signature_match = re.search(rf'{re.escape(method_name)}\s*\([^)]*\)', method_content)
            signature = signature_match.group(0) if signature_match else method_name
            
            results.append({
                'content': method_content,
                'start_line': start_line,
                'end_line': end_line,
                'line_count': end_line - start_line + 1,
                'signature': signature
            })
        
        return results
        
    except Exception as e:
        return {'error': str(e)}

def extract_method_javalang(file_path, method_name, include_javadoc=True):
    """Extract method using javalang AST parser."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = javalang.parse.parse(content)
        results = []
        
        # Find all methods with the given name
        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            if node.name == method_name:
                # Get position info
                if hasattr(node, 'position') and node.position:
                    start_line = node.position.line
                    
                    # Find method in content
                    lines = content.split('\n')
                    
                    # Find method signature line
                    method_line_idx = start_line - 1
                    
                    # Look backward for javadoc if requested
                    if include_javadoc:
                        javadoc_start = method_line_idx
                        while javadoc_start > 0:
                            line = lines[javadoc_start - 1].strip()
                            if line.endswith('*/'):
                                # Found end of javadoc, find start
                                while javadoc_start > 0 and not lines[javadoc_start - 1].strip().startswith('/**'):
                                    javadoc_start -= 1
                                break
                            elif line and not line.startswith('@'):
                                # Not javadoc or annotation
                                break
                            javadoc_start -= 1
                    else:
                        javadoc_start = method_line_idx
                    
                    # Find method end by tracking braces
                    method_start = '\n'.join(lines[javadoc_start:])
                    brace_pos = method_start.find('{')
                    if brace_pos != -1:
                        end_offset = find_closing_brace(method_start, brace_pos)
                        if end_offset != -1:
                            method_content = method_start[:end_offset]
                            end_line = javadoc_start + method_content.count('\n') + 1
                            
                            # Build signature
                            params = ', '.join(f"{p.type.name} {p.name}" for p in node.parameters)
                            signature = f"{node.name}({params})"
                            
                            results.append({
                                'content': method_content,
                                'start_line': javadoc_start + 1,
                                'end_line': end_line,
                                'line_count': end_line - javadoc_start,
                                'signature': signature
                            })
        
        return results
        
    except Exception as e:
        return {'error': str(e)}

def extract_method(file_path, method_name, include_javadoc=True):
    """Extract method using best available parser."""
    if HAS_JAVALANG:
        result = extract_method_javalang(file_path, method_name, include_javadoc)
        if not isinstance(result, dict) or 'error' not in result:
            return result
    
    # Fallback to regex
    return extract_method_regex(file_path, method_name, include_javadoc)

def list_all_methods(file_path):
    """List all methods in the file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        methods = []
        
        # Simple regex to find method declarations
        method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:[\w<>\[\],.]+\s+)?(\w+)\s*\([^)]*\)'
        
        for match in re.finditer(method_pattern, content, re.MULTILINE):
            method_name = match.group(1)
            if method_name not in ['if', 'while', 'for', 'switch', 'catch']:  # Skip keywords
                start_line = content[:match.start()].count('\n') + 1
                
                # Try to find the end of the method
                brace_start = content.find('{', match.end())
                if brace_start != -1:
                    end_pos = find_closing_brace(content, brace_start)
                    if end_pos != -1:
                        end_line = content[:end_pos].count('\n') + 1
                        methods.append({
                            'name': method_name,
                            'start_line': start_line,
                            'end_line': end_line,
                            'line_count': end_line - start_line + 1
                        })
        
        return methods
        
    except Exception as e:
        return {'error': str(e)}

def main():
    # Create parser using analyze pattern
    parser = create_standard_parser(
        'analyze',
        'Extract methods from Java files',
        epilog='''
EXAMPLES:
  # Extract a specific method  
  # Extract method without javadoc  
  # List all methods in a file  
  # Extract from a specific path
COMMON ERRORS:
  - Make sure the file path is correct
  - Method names are case-sensitive
  - For overloaded methods, all versions will be extracted
        '''
    )
    
    # Add tool-specific arguments
    parser.add_argument('--list', action='store_true', help='List all methods in the file')
    parser.add_argument('--no-javadoc', action='store_true', help='Exclude javadoc comments')
    
    # Override the target argument to be optional when --list is used
    parser._actions[1].nargs = '?'  # Make target optional
    parser._actions[1].help = 'Name of the method to extract (not needed with --list)'
    
    # Parse arguments manually to handle special case
    args = parser.parse_args()
    
    # Custom validation since we need to handle --list mode specially
    
    # Validate arguments
    if not args.list and not args.target:
        parser.error("Either provide a method name or use --list to see all methods")
    
    if not args.file:
        parser.error("File must be specified with --file")

    # Check file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    if not file_path.suffix == '.java':
        print(f"Warning: File '{file_path}' does not have .java extension", file=sys.stderr)
    
    # List methods if requested
    if args.list:
        methods = list_all_methods(file_path)
        if isinstance(methods, dict) and 'error' in methods:
            print(f"Error: {methods['error']}", file=sys.stderr)
            sys.exit(1)
        
        if not methods:
            print(f"No methods found in {file_path}")
            sys.exit(0)
        
        print(f"Found {len(methods)} methods in {file_path}:\n")
        print(f"{'Method Name':<40} {'Lines':<12} {'Size':<10}")
        print("-" * 65)
        
        # Sort by line count (largest first)
        for method in sorted(methods, key=lambda x: x['line_count'], reverse=True):
            print(f"{method['name']:<40} {method['start_line']:>5}-{method['end_line']:<5} {method['line_count']:>5} lines")
    
    else:
        # Extract specific method
        results = extract_method(file_path, args.target, not args.no_javadoc)
        
        if isinstance(results, dict) and 'error' in results:
            print(f"Error: {results['error']}", file=sys.stderr)
            sys.exit(1)
        
        if not results:
            print(f"Method '{args.target}' not found in {file_path}", file=sys.stderr)
            print(f"\nTip: Use --list to see all available methods", file=sys.stderr)
            sys.exit(1)
        
        if len(results) > 1:
            print(f"Found {len(results)} methods named '{args.target}':\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['signature']} at lines {result['start_line']}-{result['end_line']}")
            print()
        
        for i, result in enumerate(results):
            if len(results) > 1:
                print(f"=== Method {i+1}: {result['signature']} ===")
            print(f"Location: lines {result['start_line']}-{result['end_line']} ({result['line_count']} lines)")
            print("-" * 80)
            print(result['content'])
            if i < len(results) - 1:
                print("\n")

if __name__ == "__main__":
    main()