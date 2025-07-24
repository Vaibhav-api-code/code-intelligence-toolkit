#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Extract specific methods from Java files, even when the files are too large to read directly.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
from pathlib import Path
import re
import argparse

try:
    import javalang
    HAS_JAVALANG = True
except ImportError:
    HAS_JAVALANG = False

from java_parsing_utils import find_closing_brace

def extract_method_regex(file_path, method_name, include_javadoc=True):
    """Extract method using regex (fallback when javalang not available)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        
        # Pattern to find methods with the specific name
        # This pattern tries to match various method signatures
        method_pattern = rf'(?:(?:\/\*\*[\s\S]*?\*\/)\s*)?(?:@\w+(?:\([^)]*\))?\s*)*((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.]+\s+)?)?{re.escape(method_name)}\s*\([^)]*\)(?:\s+throws\s+[^{{]+)?\s*\{{'
        
        results = []
        
        for match in re.finditer(method_pattern, content, re.MULTILINE | re.DOTALL):
            # Check if this match is in a commented line
            match_line_start = content.rfind('\n', 0, match.start()) + 1
            match_line_end = content.find('\n', match.start())
            if match_line_end == -1:
                match_line_end = len(content)
            match_line = content[match_line_start:match_line_end].strip()
            
            # Skip if the line starts with a comment
            if match_line.startswith('//') or match_line.startswith('/*'):
                continue
            # Find the complete method body by tracking braces
            start_pos = match.start()
            brace_pos = match.end() - 1  # Position of opening brace
            
            # Improved brace counting that handles strings and comments
            brace_count = 1
            pos = brace_pos + 1
            in_string = False
            in_char = False
            in_line_comment = False
            in_block_comment = False
            escape_next = False
            
            while brace_count > 0 and pos < len(content):
                char = content[pos]
                prev_char = content[pos-1] if pos > 0 else ''
                next_char = content[pos+1] if pos < len(content)-1 else ''
                
                # Handle escape sequences
                if escape_next:
                    escape_next = False
                    pos += 1
                    continue
                    
                if char == '\\' and (in_string or in_char):
                    escape_next = True
                    pos += 1
                    continue
                
                # Handle comments
                if not in_string and not in_char:
                    if char == '/' and next_char == '/' and not in_block_comment:
                        in_line_comment = True
                    elif char == '/' and next_char == '*' and not in_line_comment:
                        in_block_comment = True
                        pos += 1  # Skip the *
                    elif char == '*' and next_char == '/' and in_block_comment:
                        in_block_comment = False
                        pos += 1  # Skip the /
                    elif char == '\n' and in_line_comment:
                        in_line_comment = False
                
                # Handle strings and chars
                if not in_line_comment and not in_block_comment:
                    if char == '"' and not in_char:
                        in_string = not in_string
                    elif char == "'" and not in_string:
                        in_char = not in_char
                
                # Count braces only when not in string/comment
                if not in_string and not in_char and not in_line_comment and not in_block_comment:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                
                pos += 1
            
            if brace_count == 0:
                method_content = content[start_pos:pos]
                
                # Calculate line numbers
                lines_before_start = content[:start_pos].count('\n')
                lines_before_end = content[:pos].count('\n')
                
                # Extract signature
                signature_match = re.search(rf'[^{{]*{re.escape(method_name)}\s*\([^)]*\)', method_content)
                signature = signature_match.group(0).strip() if signature_match else method_name
                
                # Handle javadoc
                if not include_javadoc:
                    # Remove javadoc from content
                    javadoc_pattern = r'^\/\*\*[\s\S]*?\*\/\s*'
                    method_content = re.sub(javadoc_pattern, '', method_content)
                
                results.append({
                    'method_name': method_name,
                    'signature': signature,
                    'start_line': lines_before_start + 1,
                    'end_line': lines_before_end + 1,
                    'line_count': lines_before_end - lines_before_start + 1,
                    'content': method_content
                })
        
        return results if results else None
        
    except Exception as e:
        return {'error': str(e)}

def extract_method(file_path, method_name, include_javadoc=True):
    """
    Extract a specific method from a Java file.
    
    Args:
        file_path: Path to the Java file
        method_name: Name of the method to extract
        include_javadoc: Whether to include JavaDoc comments above the method
                        (Note: In AST mode, javadoc is currently always included)
        
    Returns:
        Dictionary with method info or None if not found
    """
    if not HAS_JAVALANG:
        return extract_method_regex(file_path, method_name, include_javadoc)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = javalang.parse.parse(content)
        results = []
        lines = content.splitlines()

        for path, node in tree:
            if isinstance(node, javalang.tree.MethodDeclaration) and node.name == method_name:
                start_line = node.position.line

                start_index = sum(len(l) + 1 for l in lines[:start_line - 1])
                open_brace = content.find('{', start_index)
                if open_brace == -1:
                    continue

                # Use proper brace counting utility
                end_pos = find_closing_brace(content, open_brace)
                if end_pos == -1:
                    continue

                method_content = content[start_index:end_pos]
                end_line = content[:end_pos].count('\n') + 1

                signature_line = lines[start_line - 1].strip()
                signature = signature_line

                results.append({
                    'method_name': method_name,
                    'signature': signature,
                    'start_line': start_line,
                    'end_line': end_line,
                    'line_count': end_line - start_line + 1,
                    'content': method_content
                })

        return results if results else None
        
    except Exception as e:
        return {'error': str(e)}

def extract_all_methods_regex(file_path):
    """Extract all methods using regex (fallback when javalang not available)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Pattern to find all methods
        method_pattern = r'(?:public|private|protected|static|final|synchronized|native|abstract)\s+(?:(?:static|final|synchronized)\s+)*(?:[a-zA-Z0-9_<>\[\].,\s]+\s+)?([a-zA-Z0-9_]+)\s*\([^{]*\)\s*(?:throws\s+[^{]+)?\s*\{'
        
        methods = []
        
        for match in re.finditer(method_pattern, content, re.MULTILINE):
            # Check if this match is in a commented line
            match_line_start = content.rfind('\n', 0, match.start()) + 1
            match_line_end = content.find('\n', match.start())
            if match_line_end == -1:
                match_line_end = len(content)
            match_line = content[match_line_start:match_line_end].strip()
            
            # Skip if the line starts with a comment
            if match_line.startswith('//') or match_line.startswith('/*'):
                continue
                
            method_name = match.group(1)
            start_pos = match.start()
            
            # Find the complete method body with proper brace counting
            brace_count = 1
            pos = match.end()
            in_string = False
            in_char = False
            in_line_comment = False
            in_block_comment = False
            escape_next = False
            
            while brace_count > 0 and pos < len(content):
                char = content[pos]
                next_char = content[pos+1] if pos < len(content)-1 else ''
                
                # Handle escape sequences
                if escape_next:
                    escape_next = False
                    pos += 1
                    continue
                    
                if char == '\\' and (in_string or in_char):
                    escape_next = True
                    pos += 1
                    continue
                
                # Handle comments
                if not in_string and not in_char:
                    if char == '/' and next_char == '/' and not in_block_comment:
                        in_line_comment = True
                    elif char == '/' and next_char == '*' and not in_line_comment:
                        in_block_comment = True
                        pos += 1  # Skip the *
                    elif char == '*' and next_char == '/' and in_block_comment:
                        in_block_comment = False
                        pos += 1  # Skip the /
                    elif char == '\n' and in_line_comment:
                        in_line_comment = False
                
                # Handle strings and chars
                if not in_line_comment and not in_block_comment:
                    if char == '"' and not in_char:
                        in_string = not in_string
                    elif char == "'" and not in_string:
                        in_char = not in_char
                
                # Count braces only when not in string/comment
                if not in_string and not in_char and not in_line_comment and not in_block_comment:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                
                pos += 1
            
            if brace_count == 0:
                # Calculate line numbers
                start_line = content[:start_pos].count('\n') + 1
                end_line = content[:pos].count('\n') + 1
                
                methods.append({
                    'name': method_name,
                    'start_line': start_line,
                    'end_line': end_line,
                    'line_count': end_line - start_line + 1
                })
        
        return methods
        
    except Exception as e:
        return {'error': str(e)}

def extract_all_methods(file_path):
    """
    Extract all method names and their line numbers from a Java file.
    """
    if not HAS_JAVALANG:
        return extract_all_methods_regex(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = javalang.parse.parse(content)
        lines = content.splitlines()
        methods = []

        for path, node in tree:
            if isinstance(node, javalang.tree.MethodDeclaration):
                name = node.name
                start_line = node.position.line
                start_index = sum(len(l) + 1 for l in lines[:start_line - 1])
                open_brace = content.find('{', start_index)
                
                # Use proper brace counting utility
                end_pos = find_closing_brace(content, open_brace)
                if end_pos == -1:
                    continue

                end_line = content[:end_pos].count('\n') + 1

                methods.append({
                    'name': name,
                    'start_line': start_line,
                    'end_line': end_line,
                    'line_count': end_line - start_line + 1
                })

        return methods
        
    except Exception as e:
        return {'error': str(e)}

def main():
    parser = argparse.ArgumentParser(
        description="Extract specific methods from Java files, even when the files are too large to read directly.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s OrderSenderControllerV2.java --method showTestUI
  %(prog)s OrderSenderControllerV2.java --method sendOrder --no-javadoc
  %(prog)s OrderSenderControllerV2.java --list
"""
    )
    parser.add_argument("file_path", type=Path, help="Path to the Java file")
    
    # Group for mutually exclusive actions: either list or extract a specific method
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--list", action="store_true", help="List all methods in the file")
    action_group.add_argument("--method", dest="method_name", help="Name of the method to extract")

    parser.add_argument("--no-javadoc", action="store_false", dest="include_javadoc",
                        help="Exclude JavaDoc comments from the output")
    
    args = parser.parse_args()

    if not args.file_path.exists():
        print(f"Error: File '{args.file_path}' not found")
        sys.exit(1)

    if args.list:
        methods = extract_all_methods(args.file_path)
        if isinstance(methods, dict) and 'error' in methods:
            print(f"Error: {methods['error']}")
            sys.exit(1)
        
        if not methods:
            print(f"No methods found in {args.file_path}")
            return

        print(f"Found {len(methods)} methods in {args.file_path}:\n")
        print(f"{'Method Name':<40} {'Lines':<12} {'Size':<10}")
        print("-" * 65)
        
        for method in sorted(methods, key=lambda x: x['line_count'], reverse=True):
            print(f"{method['name']:<40} {method['start_line']:>5}-{method['end_line']:<5} {method['line_count']:>5} lines")

    elif args.method_name:
        results = extract_method(args.file_path, args.method_name, args.include_javadoc)
        
        if not results:
            print(f"Method '{args.method_name}' not found in {args.file_path}")
            sys.exit(1)
            
        if isinstance(results, dict) and 'error' in results:
            print(f"Error: {results['error']}")
            sys.exit(1)
            
        if len(results) > 1:
            print(f"Found {len(results)} methods named '{args.method_name}':\n")
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