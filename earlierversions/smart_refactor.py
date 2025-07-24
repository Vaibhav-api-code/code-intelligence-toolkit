#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Smart refactor tool with Java scope awareness.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from collections import defaultdict, Counter
import json
import ast
import tempfile
import os
from typing import List, Dict, Set, Tuple, Optional

def check_dependencies():
    """Check if required tools are installed."""
    if not shutil.which('rg'):
        print("Error: ripgrep (rg) is not installed.")
        print("Install it with: brew install ripgrep")
        sys.exit(1)

def find_java_files(scope="."):
    """Find all Java files in the scope."""
    java_files = []
    scope_path = Path(scope)
    
    if scope_path.is_file() and scope_path.suffix == '.java':
        return [str(scope_path)]
    
    try:
        result = subprocess.run(['find', scope, '-name', '*.java', '-type', 'f'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            java_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
    except:
        # Fallback to glob
        for java_file in Path(scope).rglob('*.java'):
            java_files.append(str(java_file))
    
    return java_files

def analyze_java_scope(file_path, target_name):
    """Analyze Java file to understand scope and usage of target."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return {}
    
    scope_info = {
        'package': extract_package(content),
        'imports': extract_imports(content),
        'class_name': extract_class_name(content),
        'methods': extract_methods(content),
        'fields': extract_fields(content),
        'inner_classes': extract_inner_classes(content),
        'target_usages': find_target_usages(content, target_name),
        'scope_conflicts': []
    }
    
    return scope_info

def extract_package(content):
    """Extract package declaration."""
    match = re.search(r'^\s*package\s+([^;]+);', content, re.MULTILINE)
    return match.group(1).strip() if match else None

def extract_imports(content):
    """Extract import statements."""
    imports = []
    for match in re.finditer(r'^\s*import\s+(static\s+)?([^;]+);', content, re.MULTILINE):
        imports.append({
            'is_static': bool(match.group(1)),
            'import_path': match.group(2).strip(),
            'line': content[:match.start()].count('\n') + 1
        })
    return imports

def extract_class_name(content):
    """Extract the main class name."""
    match = re.search(r'(?:public\s+)?(?:abstract\s+)?(?:final\s+)?class\s+(\w+)', content)
    return match.group(1) if match else None

def extract_methods(content):
    """Extract method definitions with their scope information."""
    methods = []
    
    # Pattern for method declarations
    method_pattern = r'^\s*((?:public|private|protected)?\s*)?((?:static|final|synchronized|abstract|native)\s+)*((?:[a-zA-Z_$][\w$]*(?:<[^>]*>)?(?:\[\])*\s+)?)(\w+)\s*\(([^)]*)\)(?:\s+throws\s+[^{]+)?\s*\{'
    
    for match in re.finditer(method_pattern, content, re.MULTILINE):
        visibility = (match.group(1) or '').strip() or 'package-private'
        modifiers = (match.group(2) or '').strip()
        return_type = (match.group(3) or '').strip()
        method_name = match.group(4)
        parameters = match.group(5).strip()
        
        # Find method body end
        start_pos = match.end() - 1  # Position of opening brace
        end_pos = find_closing_brace(content, start_pos)
        
        if end_pos != -1:
            method_body = content[match.start():end_pos]
            line_num = content[:match.start()].count('\n') + 1
            
            methods.append({
                'name': method_name,
                'visibility': visibility,
                'modifiers': modifiers,
                'return_type': return_type,
                'parameters': parameters,
                'line': line_num,
                'start_pos': match.start(),
                'end_pos': end_pos,
                'body': method_body,
                'signature': f"{method_name}({parameters})"
            })
    
    return methods

def extract_fields(content):
    """Extract field declarations with scope information."""
    fields = []
    
    # Pattern for field declarations
    field_pattern = r'^\s*((?:public|private|protected)?\s*)?((?:static|final|volatile|transient)\s+)*([a-zA-Z_$][\w$]*(?:<[^>]*>)?(?:\[\])*)\s+(\w+)(?:\s*=\s*[^;]+)?\s*;'
    
    for match in re.finditer(field_pattern, content, re.MULTILINE):
        visibility = (match.group(1) or '').strip() or 'package-private'
        modifiers = (match.group(2) or '').strip()
        field_type = match.group(3)
        field_name = match.group(4)
        line_num = content[:match.start()].count('\n') + 1
        
        fields.append({
            'name': field_name,
            'type': field_type,
            'visibility': visibility,
            'modifiers': modifiers,
            'line': line_num,
            'start_pos': match.start(),
            'end_pos': match.end()
        })
    
    return fields

def extract_inner_classes(content):
    """Extract inner class definitions."""
    inner_classes = []
    
    # Pattern for inner class declarations
    inner_class_pattern = r'^\s*((?:public|private|protected)?\s*)?((?:static|final|abstract)\s+)*(?:class|interface|enum)\s+(\w+)'
    
    for match in re.finditer(inner_class_pattern, content, re.MULTILINE):
        # Skip the main class by checking if this is inside another class
        line_before = content[:match.start()]
        open_braces = line_before.count('{')
        close_braces = line_before.count('}')
        
        if open_braces > close_braces:  # Inside another class
            visibility = (match.group(1) or '').strip() or 'package-private'
            modifiers = (match.group(2) or '').strip()
            class_name = match.group(3)
            line_num = content[:match.start()].count('\n') + 1
            
            inner_classes.append({
                'name': class_name,
                'visibility': visibility,
                'modifiers': modifiers,
                'line': line_num
            })
    
    return inner_classes

def find_target_usages(content, target_name):
    """Find all usages of the target in the content."""
    usages = []
    
    # Different usage patterns
    patterns = [
        (rf'\b{re.escape(target_name)}\b', 'reference'),
        (rf'\.{re.escape(target_name)}\s*\(', 'method_call'),
        (rf'\.{re.escape(target_name)}\b(?!\s*\()', 'field_access'),
        (rf'new\s+{re.escape(target_name)}\s*\(', 'constructor'),
        (rf'{re.escape(target_name)}\s+\w+', 'type_declaration'),
        (rf'@{re.escape(target_name)}\b', 'annotation')
    ]
    
    for pattern, usage_type in patterns:
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = content.split('\n')[line_num - 1] if line_num <= len(content.split('\n')) else ""
            
            usages.append({
                'type': usage_type,
                'line': line_num,
                'start_pos': match.start(),
                'end_pos': match.end(),
                'context': line_content.strip(),
                'match_text': match.group()
            })
    
    return usages

def find_closing_brace(content, start_pos):
    """Find the closing brace that matches the opening brace at start_pos."""
    if start_pos >= len(content) or content[start_pos] != '{':
        return -1
    
    brace_count = 1
    pos = start_pos + 1
    in_string = False
    in_char = False
    in_comment = False
    in_line_comment = False
    
    while pos < len(content) and brace_count > 0:
        char = content[pos]
        
        # Handle comments and strings
        if not in_string and not in_char:
            if pos < len(content) - 1 and content[pos:pos+2] == '//':
                in_line_comment = True
            elif pos < len(content) - 1 and content[pos:pos+2] == '/*':
                in_comment = True
            elif char == '"' and (pos == 0 or content[pos-1] != '\\'):
                in_string = True
            elif char == "'" and (pos == 0 or content[pos-1] != '\\'):
                in_char = True
            elif not in_comment and not in_line_comment:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
        else:
            if in_string and char == '"' and (pos == 0 or content[pos-1] != '\\'):
                in_string = False
            elif in_char and char == "'" and (pos == 0 or content[pos-1] != '\\'):
                in_char = False
        
        if in_line_comment and char == '\n':
            in_line_comment = False
        elif in_comment and pos < len(content) - 1 and content[pos:pos+2] == '*/':
            in_comment = False
            pos += 1  # Skip the second character of */
        
        pos += 1
    
    return pos - 1 if brace_count == 0 else -1

def check_scope_conflicts(old_name, new_name, scope_info):
    """Check for potential scope conflicts when renaming."""
    conflicts = []
    
    # Check if new name conflicts with existing methods
    for method in scope_info['methods']:
        if method['name'] == new_name:
            conflicts.append({
                'type': 'method_conflict',
                'message': f"Method '{new_name}' already exists at line {method['line']}",
                'line': method['line']
            })
    
    # Check if new name conflicts with existing fields
    for field in scope_info['fields']:
        if field['name'] == new_name:
            conflicts.append({
                'type': 'field_conflict',
                'message': f"Field '{new_name}' already exists at line {field['line']}",
                'line': field['line']
            })
    
    # Check if new name conflicts with class name
    if scope_info['class_name'] == new_name:
        conflicts.append({
            'type': 'class_conflict',
            'message': f"Name '{new_name}' conflicts with class name",
            'line': 1
        })
    
    # Check if new name conflicts with imports
    for import_info in scope_info['imports']:
        import_name = import_info['import_path'].split('.')[-1]
        if import_name == new_name:
            conflicts.append({
                'type': 'import_conflict',
                'message': f"Name '{new_name}' conflicts with import at line {import_info['line']}",
                'line': import_info['line']
            })
    
    return conflicts

def perform_safe_rename(file_path, old_name, new_name, refactor_type='auto', scope='local', dry_run=False):
    """Perform a safe rename operation with scope awareness."""
    check_dependencies()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        return {'success': False, 'error': f"Could not read file: {e}"}
    
    # Analyze scope
    scope_info = analyze_java_scope(file_path, old_name)
    
    # Check for conflicts
    conflicts = check_scope_conflicts(old_name, new_name, scope_info)
    if conflicts and not dry_run:
        return {
            'success': False,
            'error': 'Scope conflicts detected',
            'conflicts': conflicts
        }
    
    # Determine what to rename based on type and scope
    changes = []
    new_content = original_content
    
    if refactor_type in ['auto', 'method']:
        # Rename method declarations and calls
        for method in scope_info['methods']:
            if method['name'] == old_name:
                changes.append({
                    'type': 'method_declaration',
                    'line': method['line'],
                    'old_text': method['signature'],
                    'new_text': method['signature'].replace(old_name, new_name, 1)
                })
                
                # Replace the method name in its declaration
                method_pattern = rf'\b{re.escape(old_name)}\s*\('
                replacement = f'{new_name}('
                new_content = re.sub(method_pattern, replacement, new_content, count=1)
    
    if refactor_type in ['auto', 'field']:
        # Rename field declarations and accesses
        for field in scope_info['fields']:
            if field['name'] == old_name:
                changes.append({
                    'type': 'field_declaration',
                    'line': field['line'],
                    'old_text': f"{field['type']} {old_name}",
                    'new_text': f"{field['type']} {new_name}"
                })
    
    # Rename usages based on scope
    if scope in ['local', 'all']:
        for usage in scope_info['target_usages']:
            if old_name in usage['match_text']:
                changes.append({
                    'type': usage['type'],
                    'line': usage['line'],
                    'context': usage['context']
                })
    
    # Apply intelligent renaming
    if refactor_type == 'auto':
        # Use word boundaries for safer replacement
        pattern = rf'\b{re.escape(old_name)}\b'
        new_content = re.sub(pattern, new_name, new_content)
    
    # If this is a dry run, don't actually modify the file
    if dry_run:
        return {
            'success': True,
            'changes': changes,
            'conflicts': conflicts,
            'preview': get_diff_preview(original_content, new_content),
            'file': file_path
        }
    
    # Write the modified content back
    try:
        # Create backup
        backup_path = f"{file_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # Write new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            'success': True,
            'changes': changes,
            'conflicts': conflicts,
            'backup_created': backup_path,
            'file': file_path
        }
    
    except Exception as e:
        return {'success': False, 'error': f"Could not write file: {e}"}

def get_diff_preview(old_content, new_content):
    """Generate a diff preview of the changes."""
    import difflib
    
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(old_lines, new_lines, 
                                   fromfile='original', tofile='modified',
                                   lineterm=''))
    
    return '\n'.join(diff[:50])  # Show first 50 lines of diff

def multi_file_refactor(scope, old_name, new_name, refactor_type='auto', 
                       file_pattern='*.java', dry_run=False, max_files=50):
    """Perform refactoring across multiple files."""
    java_files = find_java_files(scope)
    
    if len(java_files) > max_files:
        print(f"Warning: Found {len(java_files)} files, limiting to {max_files}")
        java_files = java_files[:max_files]
    
    results = []
    
    for file_path in java_files:
        print(f"Processing: {file_path}")
        result = perform_safe_rename(file_path, old_name, new_name, 
                                   refactor_type, 'all', dry_run)
        result['file'] = file_path
        results.append(result)
    
    return results

def extract_method_to_new_method(file_path, start_line, end_line, new_method_name, dry_run=False):
    """Extract lines into a new method."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return {'success': False, 'error': f"Could not read file: {e}"}
    
    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        return {'success': False, 'error': 'Invalid line range'}
    
    # Extract the code to be moved
    extracted_lines = lines[start_line-1:end_line]
    extracted_code = ''.join(extracted_lines)
    
    # Analyze the extracted code for variables
    variables_used = extract_variables_from_code(extracted_code)
    
    # Generate method signature
    method_signature = f"private void {new_method_name}() {{"
    
    # Create the new method
    new_method = f"\n    {method_signature}\n"
    for line in extracted_lines:
        new_method += f"    {line}"
    new_method += "    }\n"
    
    # Replace extracted code with method call
    method_call = f"        {new_method_name}();"
    
    # Modify the content
    new_lines = lines[:start_line-1] + [method_call + '\n'] + lines[end_line:]
    
    # Find a good place to insert the new method (end of class)
    insert_pos = find_method_insertion_point(new_lines)
    new_lines.insert(insert_pos, new_method)
    
    new_content = ''.join(new_lines)
    
    if dry_run:
        return {
            'success': True,
            'preview': get_diff_preview(''.join(lines), new_content),
            'new_method': new_method,
            'variables_used': variables_used
        }
    
    # Write the file
    try:
        backup_path = f"{file_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(''.join(lines))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            'success': True,
            'backup_created': backup_path,
            'new_method': new_method,
            'variables_used': variables_used
        }
    
    except Exception as e:
        return {'success': False, 'error': f"Could not write file: {e}"}

def extract_variables_from_code(code):
    """Extract variable names used in the code."""
    # Simple variable extraction - could be enhanced
    variables = set()
    
    # Find variable assignments
    for match in re.finditer(r'(\w+)\s*=', code):
        variables.add(match.group(1))
    
    # Find variable usage
    for match in re.finditer(r'\b(\w+)\b', code):
        var_name = match.group(1)
        if not var_name[0].isupper() and var_name not in {'if', 'for', 'while', 'return', 'new', 'this', 'super'}:
            variables.add(var_name)
    
    return list(variables)

def find_method_insertion_point(lines):
    """Find the best place to insert a new method."""
    # Look for the last closing brace that's at the class level
    brace_level = 0
    last_method_end = len(lines) - 2  # Default to near end
    
    for i, line in enumerate(lines):
        brace_level += line.count('{') - line.count('}')
        
        # If we're at class level and see a method-like pattern
        if brace_level == 1 and re.match(r'\s*}\s*$', line):
            last_method_end = i + 1
    
    return last_method_end

def format_refactor_results(results, operation='rename'):
    """Format refactoring results for display."""
    output = []
    
    output.append("=" * 80)
    output.append(f"SMART REFACTOR RESULTS: {operation.upper()}")
    output.append("=" * 80)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    output.append(f"Files processed: {len(results)}")
    output.append(f"Successful: {len(successful)}")
    output.append(f"Failed: {len(failed)}")
    
    if failed:
        output.append(f"\n❌ FAILED FILES:")
        output.append("-" * 40)
        for result in failed:
            output.append(f"  {result.get('file', 'unknown')}: {result.get('error', 'unknown error')}")
            if result.get('conflicts'):
                for conflict in result['conflicts']:
                    output.append(f"    - {conflict['message']}")
    
    if successful:
        output.append(f"\n✅ SUCCESSFUL FILES:")
        output.append("-" * 40)
        for result in successful:
            file_path = result.get('file', 'unknown')
            changes = result.get('changes', [])
            output.append(f"  {file_path}: {len(changes)} changes")
            
            if changes:
                change_types = Counter(change['type'] for change in changes)
                for change_type, count in change_types.items():
                    output.append(f"    - {change_type}: {count}")
            
            if result.get('backup_created'):
                output.append(f"    - Backup: {result['backup_created']}")
    
    return '\n'.join(output)

def main():
    parser = argparse.ArgumentParser(
        description='Smart refactor tool with Java scope awareness',
        epilog='''
EXAMPLES:
  # Safe method rename with conflict detection
  %(prog)s rename --old-name "oldMethod" --new-name "newMethod" --file MyClass.java --dry-run
  
  # Multi-file variable rename
  %(prog)s rename --old-name "counter" --new-name "index" --scope src/ --type variable
  
  # Extract method from code block
  %(prog)s extract-method --file MyClass.java --start-line 50 --end-line 65 --method-name "validateInput"
  
  # Scope-aware class rename
  %(prog)s rename --old-name "OldClass" --new-name "NewClass" --scope . --type class --max-files 20
  
  # Preview changes without applying
  %(prog)s rename --old-name "data" --new-name "payload" --scope . --dry-run --show-conflicts
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Refactoring operations')
    
    # Rename command
    rename_parser = subparsers.add_parser('rename', help='Rename variables, methods, or classes')
    rename_parser.add_argument('--old-name', required=True, help='Current name to rename')
    rename_parser.add_argument('--new-name', required=True, help='New name to use')
    rename_parser.add_argument('--file', help='Single file to refactor')
    rename_parser.add_argument('--scope', default='.', help='Directory scope for multi-file refactor')
    rename_parser.add_argument('--type', choices=['auto', 'method', 'field', 'class', 'variable'], 
                              default='auto', help='Type of element to rename')
    rename_parser.add_argument('--scope-level', choices=['local', 'class', 'package', 'all'], 
                              default='all', help='Scope level for rename operation')
    
    # Extract method command
    extract_parser = subparsers.add_parser('extract-method', help='Extract code into a new method')
    extract_parser.add_argument('--file', required=True, help='File to refactor')
    extract_parser.add_argument('--start-line', type=int, required=True, help='Start line of code to extract')
    extract_parser.add_argument('--end-line', type=int, required=True, help='End line of code to extract')
    extract_parser.add_argument('--method-name', required=True, help='Name for the new method')
    
    # Common options
    for p in [rename_parser, extract_parser]:
        p.add_argument('--dry-run', action='store_true', help='Preview changes without applying them')
        p.add_argument('--show-conflicts', action='store_true', help='Show potential naming conflicts')
        p.add_argument('--max-files', type=int, default=50, help='Maximum files to process')
        p.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'rename':
            if args.file:
                # Single file rename
                results = [perform_safe_rename(args.file, args.old_name, args.new_name, 
                                             args.type, args.scope_level, args.dry_run)]
            else:
                # Multi-file rename
                results = multi_file_refactor(args.scope, args.old_name, args.new_name, 
                                            args.type, '*.java', args.dry_run, args.max_files)
            
            operation = 'rename'
        
        elif args.command == 'extract-method':
            result = extract_method_to_new_method(args.file, args.start_line, args.end_line, 
                                                 args.method_name, args.dry_run)
            results = [result]
            operation = 'extract-method'
        
        # Output results
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            formatted_output = format_refactor_results(results, operation)
            print(formatted_output)
            
            # Show previews for dry runs
            if args.dry_run:
                for result in results:
                    if result.get('success') and result.get('preview'):
                        print(f"\n📄 PREVIEW FOR {result.get('file', 'unknown')}:")
                        print("-" * 60)
                        print(result['preview'])
    
    except KeyboardInterrupt:
        print("\nRefactoring interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()