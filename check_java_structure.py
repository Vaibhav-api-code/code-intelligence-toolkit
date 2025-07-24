#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Check for bracket/brace matching and structural issues in Java files.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from pathlib import Path
from collections import deque
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

class StructureChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []

    def remove_all_comments(self, text):
        """Remove both block comments (/* ... */) and single-line comments (//) while preserving line breaks."""
        
        # First, handle strings to avoid removing comment-like content inside strings
        strings = []
        
        def save_string(match):
            strings.append(match.group(0))
            return f"__STRING_{len(strings)-1}__"
        
        # Save string literals
        text = re.sub(r'"(?:[^"\\]|\\.)*"', save_string, text)
        
        # Remove block comments while preserving line breaks
        def block_replacer(match):
            comment = match.group(0)
            return re.sub(r'[^\n]', ' ', comment)
        
        text = re.sub(r'/\*.*?\*/', block_replacer, text, flags=re.DOTALL)
        
        # Remove single-line comments while preserving the line structure
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Find // but not inside a saved string placeholder
            comment_pos = line.find('//')
            if comment_pos != -1:
                # Replace comment with spaces to preserve column positions
                lines[i] = line[:comment_pos] + ' ' * (len(line) - comment_pos)
        
        text = '\n'.join(lines)
        
        # Restore strings
        for i, string in enumerate(strings):
            text = text.replace(f"__STRING_{i}__", string)
        
        return text
        
    def check_file(self, file_path):
        """Check a Java file for structural issues."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Attempt full AST parsing first if javalang is available
        if HAS_JAVALANG:
            try:
                javalang.parse.parse(content)
            except javalang.parser.JavaSyntaxError as e:
                line = e.at.position.line if e.at and e.at.position else 1
                col = e.at.position.column if e.at and e.at.position else 1
                self.issues.append({
                    'type': 'SYNTAX_ERROR',
                    'line': line,
                    'col': col,
                    'message': e.description
                })
            except Exception as e:
                self.issues.append({
                    'type': 'PARSE_ERROR',
                    'line': 1,
                    'col': 1,
                    'message': str(e)
                })

        # Note: AST parsing above catches syntax errors that make the file unparseable.
        # Heuristic checks below catch structural issues in parseable files
        # (e.g., unclosed strings in comments, irregular indentation).
        # Both are valuable - AST for syntax, heuristics for style/structure.
        
        # Remove all comments while preserving line numbers for heuristic checks
        content_clean = self.remove_all_comments(content)
        lines = content_clean.splitlines()
        
        # Check various structural elements
        self.check_brackets(lines)
        self.check_strings(lines)
        self.check_semicolons(lines)
        self.check_method_structure(content_clean)
        self.check_class_structure(content_clean)
        self.check_indentation(lines)
        
        return self.issues, self.warnings
    
    def check_brackets(self, lines):
        """Check for balanced brackets, braces, and parentheses."""
        stack = deque()
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        closing_brackets = set(bracket_pairs.values())
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments and strings for bracket checking
            cleaned_line = self.remove_strings_and_comments(line)
            
            for col, char in enumerate(cleaned_line):
                if char in bracket_pairs:
                    stack.append({
                        'char': char,
                        'line': line_num,
                        'col': col + 1,
                        'expecting': bracket_pairs[char]
                    })
                elif char in closing_brackets:
                    if not stack:
                        self.issues.append({
                            'type': 'UNMATCHED_CLOSING',
                            'line': line_num,
                            'col': col + 1,
                            'message': f"Unexpected closing '{char}' without matching opening"
                        })
                    else:
                        opening = stack.pop()
                        if opening['expecting'] != char:
                            self.issues.append({
                                'type': 'MISMATCHED_BRACKET',
                                'line': line_num,
                                'col': col + 1,
                                'message': f"Expected '{opening['expecting']}' but found '{char}' (opened at line {opening['line']})"
                            })
        
        # Check for unclosed brackets
        while stack:
            unclosed = stack.pop()
            self.issues.append({
                'type': 'UNCLOSED_BRACKET',
                'line': unclosed['line'],
                'col': unclosed['col'],
                'message': f"Unclosed '{unclosed['char']}' - expected '{unclosed['expecting']}'"
            })
    
    def check_strings(self, lines):
        """Check for unclosed strings and character literals."""
        for line_num, line in enumerate(lines, 1):
            # Check for unclosed strings (basic check)
            if not self.is_in_comment(line):
                # Count quotes, considering escaped quotes
                cleaned = re.sub(r'\\"', '', line)  # Remove escaped quotes
                cleaned = re.sub(r"\\'", '', cleaned)  # Remove escaped single quotes
                
                double_quotes = cleaned.count('"')
                if double_quotes % 2 != 0:
                    self.issues.append({
                        'type': 'UNCLOSED_STRING',
                        'line': line_num,
                        'col': line.rfind('"') + 1,
                        'message': 'Unclosed string literal'
                    })
                
                # Check character literals
                char_literals = re.findall(r"'([^'\\]|\\.)'", line)
                single_quotes = line.count("'") - (len(char_literals) * 2)
                if single_quotes % 2 != 0:
                    self.warnings.append({
                        'type': 'POSSIBLE_UNCLOSED_CHAR',
                        'line': line_num,
                        'col': line.rfind("'") + 1,
                        'message': 'Possibly unclosed character literal'
                    })
    
    def check_semicolons(self, lines):
        """Check for missing semicolons."""
        # Patterns that should end with semicolon
        needs_semicolon = [
            r'^\s*(?:public|private|protected|static|final)*\s*\w+(?:<[^>]+>)?\s+\w+\s*=',  # Variable assignment
            r'^\s*return\s+',  # Return statements
            r'^\s*throw\s+',   # Throw statements
            r'^\s*break\s*$',  # Break statements
            r'^\s*continue\s*$',  # Continue statements
            r'\)\s*$',  # Method calls at end of line (heuristic)
        ]
        
        for line_num, line in enumerate(lines, 1):
            if self.is_in_comment(line):
                continue
                
            trimmed = line.strip()
            if not trimmed:
                continue
            
            # Check if line needs semicolon
            needs_semi = False
            for pattern in needs_semicolon:
                if re.search(pattern, trimmed):
                    needs_semi = True
                    break
            
            if needs_semi and not trimmed.endswith(';') and not trimmed.endswith('{') and not trimmed.endswith('}'):
                # Check if the next line continues this statement
                if line_num < len(lines):
                    next_line = lines[line_num].strip()
                    if next_line and not next_line[0] in '.+-*/=':
                        self.warnings.append({
                            'type': 'MISSING_SEMICOLON',
                            'line': line_num,
                            'col': len(line),
                            'message': 'Possibly missing semicolon'
                        })
    
    def check_method_structure(self, content):
        """Check method structure for common issues."""
        # Find all methods
        method_pattern = r'((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.]+\s+)?)?(\w+)\s*\(([^)]*)\)(?:\s+throws\s+[^{]+)?\s*\{'
        
        for match in re.finditer(method_pattern, content, re.MULTILINE):
            method_name = match.group(4)
            params = match.group(5)
            
            # Check for very long parameter lists
            if params and len(params.split(',')) > 7:
                lines_before = content[:match.start()].count('\n')
                self.warnings.append({
                    'type': 'LONG_PARAM_LIST',
                    'line': lines_before + 1,
                    'col': match.start() - content.rfind('\n', 0, match.start()),
                    'message': f'Method {method_name} has {len(params.split(","))} parameters (consider using a parameter object)'
                })
            
            # Check method body
            start_pos = match.end() - 1  # Position of opening brace
            end_pos = self.find_matching_brace(content, start_pos)
            
            if end_pos == -1:
                lines_before = content[:match.start()].count('\n')
                self.issues.append({
                    'type': 'UNCLOSED_METHOD',
                    'line': lines_before + 1,
                    'col': match.start() - content.rfind('\n', 0, match.start()),
                    'message': f'Method {method_name} appears to be unclosed'
                })
    
    def check_class_structure(self, content):
        """Check class structure for issues."""
        # Find class declarations
        class_pattern = r'((?:public|private|protected)\s+)?((?:static|final|abstract)\s+)*(class|interface|enum)\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w\s,]+)?\s*\{'
        
        classes = []
        for match in re.finditer(class_pattern, content):
            class_type = match.group(3)
            class_name = match.group(4)
            start_pos = match.end() - 1
            
            end_pos = self.find_matching_brace(content, start_pos)
            if end_pos == -1:
                lines_before = content[:match.start()].count('\n')
                self.issues.append({
                    'type': 'UNCLOSED_CLASS',
                    'line': lines_before + 1,
                    'col': match.start() - content.rfind('\n', 0, match.start()),
                    'message': f'{class_type.capitalize()} {class_name} appears to be unclosed'
                })
            else:
                classes.append({
                    'name': class_name,
                    'type': class_type,
                    'start': match.start(),
                    'end': end_pos
                })
        
        # Check for multiple public classes in one file
        public_classes = [c for c in classes if 'public' in content[max(0, c['start']-50):c['start']]]
        if len(public_classes) > 1:
            for cls in public_classes[1:]:
                lines_before = content[:cls['start']].count('\n')
                self.warnings.append({
                    'type': 'MULTIPLE_PUBLIC_CLASSES',
                    'line': lines_before + 1,
                    'col': 1,
                    'message': f'Multiple public classes in one file ({cls["name"]})'
                })
    
    def check_indentation(self, lines):
        """Check for inconsistent indentation."""
        indent_sizes = []
        uses_tabs = False
        uses_spaces = False
        
        for line_num, line in enumerate(lines, 1):
            if line.strip():  # Non-empty line
                leading = len(line) - len(line.lstrip())
                if leading > 0:
                    if '\t' in line[:leading]:
                        uses_tabs = True
                    if ' ' in line[:leading]:
                        uses_spaces = True
                    
                    # Calculate indent level (assuming spaces)
                    spaces = line[:leading].replace('\t', '    ')
                    indent_level = len(spaces)
                    if indent_level % 4 != 0 and '\t' not in line[:leading]:
                        self.warnings.append({
                            'type': 'IRREGULAR_INDENT',
                            'line': line_num,
                            'col': 1,
                            'message': f'Irregular indentation ({indent_level} spaces)'
                        })
        
        if uses_tabs and uses_spaces:
            self.warnings.append({
                'type': 'MIXED_INDENTATION',
                'line': 1,
                'col': 1,
                'message': 'File uses both tabs and spaces for indentation'
            })
    
    def find_matching_brace(self, content, start_pos):
        """Find the matching closing brace for an opening brace."""
        if content[start_pos] != '{':
            return -1
        
        count = 1
        pos = start_pos + 1
        in_string = False
        in_char = False
        escape_next = False
        
        while count > 0 and pos < len(content):
            char = content[pos]
            
            if escape_next:
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == '"' and not in_char:
                in_string = not in_string
            elif char == "'" and not in_string:
                in_char = not in_char
            elif not in_string and not in_char:
                if char == '{':
                    count += 1
                elif char == '}':
                    count -= 1
            
            pos += 1
        
        return pos if count == 0 else -1
    
    def remove_strings_and_comments(self, line):
        """Remove strings and comments from a line for bracket checking."""
        # Remove single-line comments
        comment_pos = line.find('//')
        if comment_pos != -1:
            line = line[:comment_pos]
        
        # Remove strings (simple approach)
        line = re.sub(r'"[^"]*"', '""', line)
        line = re.sub(r"'[^']*'", "''", line)
        
        return line
    
    def is_in_comment(self, line):
        """Check if line is likely inside a comment."""
        trimmed = line.strip()
        return trimmed.startswith('//') or trimmed.startswith('/*') or trimmed.startswith('*')

def print_issues(issues, warnings, file_path):
    """Print found issues and warnings."""
    print(f"Structure Check Results for: {file_path}")
    print("=" * 80)
    
    if not issues and not warnings:
        print("✓ No structural issues found!")
        return
    
    if issues:
        print(f"\nERRORS ({len(issues)}):")
        print("-" * 60)
        for issue in sorted(issues, key=lambda x: (x['line'], x['col'])):
            print(f"Line {issue['line']}, Col {issue['col']}: {issue['type']}")
            print(f"  {issue['message']}")
    
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        print("-" * 60)
        for warning in sorted(warnings, key=lambda x: (x['line'], x.get('col', 0))):
            col_info = f", Col {warning['col']}" if 'col' in warning else ""
            print(f"Line {warning['line']}{col_info}: {warning['type']}")
            print(f"  {warning['message']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"  Errors: {len(issues)}")
    print(f"  Warnings: {len(warnings)}")
    
    if issues:
        print("\nPriority fixes:")
        issue_types = {}
        for issue in issues:
            issue_types[issue['type']] = issue_types.get(issue['type'], 0) + 1
        
        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {issue_type}: {count} occurrence(s)")

def check_multiple_files(file_paths):
    """Check multiple files and provide aggregate summary."""
    total_issues = 0
    total_warnings = 0
    file_results = []
    
    for file_path in file_paths:
        if not Path(file_path).exists():
            print(f"Skipping '{file_path}' - file not found")
            continue
        
        checker = StructureChecker()
        issues, warnings = checker.check_file(file_path)
        
        file_results.append({
            'file': file_path,
            'issues': issues,
            'warnings': warnings
        })
        
        total_issues += len(issues)
        total_warnings += len(warnings)
    
    # Print individual file results
    for result in file_results:
        print("\n" + "=" * 80)
        print_issues(result['issues'], result['warnings'], result['file'])
    
    # Print aggregate summary if multiple files
    if len(file_results) > 1:
        print("\n" + "=" * 80)
        print("AGGREGATE SUMMARY")
        print("=" * 80)
        print(f"Files checked: {len(file_results)}")
        print(f"Total errors: {total_issues}")
        print(f"Total warnings: {total_warnings}")
        
        # Files with most issues
        files_by_issues = sorted(file_results, 
                                key=lambda x: len(x['issues']) + len(x['warnings']), 
                                reverse=True)
        
        if files_by_issues[0]['issues'] or files_by_issues[0]['warnings']:
            print("\nFiles with most issues:")
            for result in files_by_issues[:5]:
                issue_count = len(result['issues'])
                warning_count = len(result['warnings'])
                if issue_count + warning_count > 0:
                    print(f"  {Path(result['file']).name}: {issue_count} errors, {warning_count} warnings")

def main():
    parser = create_standard_parser('analyze', 
                                   'Check Java file structure and bracket matching')
    
    # Add specific options for structure checking
    parser.add_argument('--errors-only', action='store_true',
                       help='Show only errors, not warnings')
    parser.add_argument('--check-multiple', action='store_true',
                       help='Enable checking multiple files')
    
    # Parse arguments using standard parser
    args = parse_standard_args(parser, 'analyze')
    
    # Handle file specification - prioritize --file flag, fallback to target
    if hasattr(args, 'file') and args.file:
        file_path = args.file
    else:
        file_path = args.target
    
    # Convert to list for compatibility with existing check_multiple_files function
    if args.check_multiple:
        # In analyze pattern, target is a single value, but we can accept multiple via scope
        if hasattr(args, 'scope') and args.scope != '.':
            # Find all Java files in scope
            scope_path = Path(args.scope)
            if scope_path.is_dir():
                file_paths = list(scope_path.glob('**/*.java'))
                file_paths = [str(f) for f in file_paths]
            else:
                file_paths = [file_path]
        else:
            file_paths = [file_path]
    else:
        file_paths = [file_path]
    
    if args.errors_only:
        # Monkey patch to skip warnings
        original_check = StructureChecker.check_file
        def check_no_warnings(self, file_path):
            issues, warnings = original_check(self, file_path)
            return issues, []
        StructureChecker.check_file = check_no_warnings
    
    if len(file_paths) == 1:
        file_path = file_paths[0]
        if not Path(file_path).exists():
            print(f"Error: File '{file_path}' not found")
            sys.exit(1)
        
        checker = StructureChecker()
        issues, warnings = checker.check_file(file_path)
        print_issues(issues, warnings, file_path)
        
        # Exit with error code if there are issues
        if issues:
            sys.exit(1)
    else:
        check_multiple_files(file_paths)

if __name__ == "__main__":
    main()
