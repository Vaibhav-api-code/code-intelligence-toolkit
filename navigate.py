#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Quick navigation tool for Java files.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re, sys, argparse, logging, os
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging & globals
# ---------------------------------------------------------------------------

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

LOG = logging.getLogger("navigate")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format="%(levelname)s: %(message)s")

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

def find_all_targets(content):
    """Find all navigation targets in the file."""
    targets = {
        'methods': [],
        'fields': [],
        'classes': [],
        'interfaces': [],
        'enums': []
    }
    
    lines = content.splitlines()
    
    # Find methods
    method_pattern = r'^\s*((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.\s]+\s+)?)?(\w+)\s*\(([^)]*)\)'
    for i, line in enumerate(lines):
        match = re.match(method_pattern, line)
        if match and not any(keyword in line for keyword in ['new ', 'return ', '=', 'if ', 'while ']):
            method_name = match.group(4)
            params = match.group(5)
            targets['methods'].append({
                'name': method_name,
                'line': i + 1,
                'signature': f"{method_name}({params})",
                'full_line': line.strip()
            })
    
    # Find fields
    field_pattern = r'^\s*((?:public|private|protected)\s+)?((?:static|final|volatile|transient)\s+)*([\w<>\[\],.\s]+)\s+(\w+)\s*[=;]'
    for i, line in enumerate(lines):
        match = re.match(field_pattern, line)
        if match and 'class ' not in line:
            field_name = match.group(4)
            field_type = match.group(3)
            targets['fields'].append({
                'name': field_name,
                'type': field_type.strip(),
                'line': i + 1,
                'full_line': line.strip()
            })
    
    # Find classes, interfaces, and enums
    class_pattern = r'^\s*((?:public|private|protected)\s+)?((?:static|final|abstract)\s+)*(class|interface|enum)\s+(\w+)'
    for i, line in enumerate(lines):
        match = re.match(class_pattern, line)
        if match:
            target_type = match.group(3)
            target_name = match.group(4)
            target_list = targets.get(f"{target_type}es" if target_type == 'class' else f"{target_type}s", [])
            target_list.append({
                'name': target_name,
                'line': i + 1,
                'full_line': line.strip()
            })
    
    return targets

def navigate_to_method(content, method_name, show_context=True, context_lines=10):
    """Navigate to a specific method."""
    lines = content.splitlines()
    found_methods = []
    
    # Support both "methodName" and "methodName(...)"
    clean_method_name = method_name.split('(')[0]
    
    # Find all occurrences of the method
    escaped = re.escape(clean_method_name)
    method_pattern = rf'^\s*((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.\s]+\s+)?)?{escaped}\s*\([^)]*\)'
    
    for i, line in enumerate(lines):
        if re.match(method_pattern, line):
            found_methods.append({
                'line_num': i + 1,
                'line': line.strip(),
                'start': max(0, i - context_lines) if show_context else i,
                'end': min(len(lines), i + context_lines + 1) if show_context else i + 1
            })
    
    return found_methods

def navigate_to_field(content, field_name, show_context=True, context_lines=5):
    """Navigate to a specific field."""
    lines = content.splitlines()
    found_fields = []
    
    # Find field declarations
    escaped = re.escape(field_name)
    field_pattern = rf'^\s*((?:public|private|protected)\s+)?((?:static|final|volatile|transient)\s+)*([\w<>\[\],.\s]+)\s+{escaped}\s*[=;]'
    
    for i, line in enumerate(lines):
        if re.match(field_pattern, line):
            found_fields.append({
                'line_num': i + 1,
                'line': line.strip(),
                'start': max(0, i - context_lines) if show_context else i,
                'end': min(len(lines), i + context_lines + 1) if show_context else i + 1
            })
    
    return found_fields

def navigate_to_line(content, line_number, window=50, show_context=True):
    """Navigate to a specific line number."""
    lines = content.splitlines()
    
    if line_number < 1 or line_number > len(lines):
        return None
    
    # Adjust to 0-based index
    line_idx = line_number - 1
    
    # Calculate window
    half_window = window // 2
    start = max(0, line_idx - half_window)
    end = min(len(lines), line_idx + half_window + 1)
    
    return {
        'line_num': line_number,
        'line': lines[line_idx].strip() if line_idx < len(lines) else "",
        'start': start,
        'end': end,
        'lines': lines
    }

def navigate_to_multiline_ranges(content, line_ranges, show_context=True):
    """Navigate to multiple line ranges."""
    lines = content.splitlines()
    results = []
    
    for line_range in line_ranges:
        if isinstance(line_range, str):
            # Parse string format like "100-120" or "100±5" or "100:10"
            if '±' in line_range:
                center, context = line_range.split('±', 1)
                center = int(center)
                context = int(context)
                start_line = max(1, center - context)
                end_line = min(len(lines), center + context)
            elif ':' in line_range:
                start, length = line_range.split(':', 1)
                start_line = int(start)
                end_line = min(len(lines), start_line + int(length) - 1)
            elif '-' in line_range:
                start, end = line_range.split('-', 1)
                start_line = int(start)
                end_line = int(end)
            else:
                # Single line
                start_line = end_line = int(line_range)
        elif isinstance(line_range, tuple):
            start_line, end_line = line_range
        else:
            continue
        
        # Validate range
        start_line = max(1, start_line)
        end_line = min(len(lines), end_line)
        
        if start_line <= end_line:
            start_idx = start_line - 1
            end_idx = end_line
            
            results.append({
                'range': f"{start_line}-{end_line}",
                'start_line': start_line,
                'end_line': end_line,
                'lines': lines[start_idx:end_idx],
                'full_content': lines
            })
    
    return results

def navigate_to_method_enhanced(content, method_name, show_signature=True, show_callers=False, context_lines=20):
    """Enhanced method navigation with signature extraction and caller analysis."""
    lines = content.splitlines()
    found_methods = []
    
    # Support both "methodName" and "methodName(...)"
    clean_method_name = method_name.split('(')[0]
    
    # Find method definitions with enhanced pattern
    escaped = re.escape(clean_method_name)
    method_patterns = [
        rf'^\s*((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.\s]+\s+)?)?{escaped}\s*\([^)]*\)',
        rf'^\s*{escaped}\s*\([^)]*\)\s*\{{',  # Simple method without modifiers
    ]
    
    for pattern in method_patterns:
        for i, line in enumerate(lines):
            if re.match(pattern, line, re.IGNORECASE):
                method_info = extract_method_info(lines, i, clean_method_name, context_lines)
                if method_info:
                    found_methods.append(method_info)
                    break  # Found with this pattern, move to next
    
    # Find method callers if requested
    if show_callers:
        callers = find_method_callers(content, clean_method_name)
        for method in found_methods:
            method['callers'] = callers
    
    return found_methods

def _find_closing_brace(content, open_brace_pos):
    """Find the position of the matching closing brace for a given opening brace."""
    if content[open_brace_pos] != '{':
        return -1
    brace_level = 1
    for i in range(open_brace_pos + 1, len(content)):
        char = content[i]
        if char == '{':
            brace_level += 1
        elif char == '}':
            brace_level -= 1
        if brace_level == 0:
            return i
    return -1  # Not found

def extract_method_info(lines, method_line, method_name, context_lines):
    """Extract comprehensive method information."""
    try:
        # Find method signature
        signature_line = lines[method_line].strip()
        
        # Look for JavaDoc above the method
        javadoc = []
        doc_start = method_line - 1
        while doc_start >= 0 and (lines[doc_start].strip().startswith('*') or 
                                 lines[doc_start].strip().startswith('/**') or
                                 lines[doc_start].strip().startswith('//') or
                                 lines[doc_start].strip() == ''):
            if lines[doc_start].strip():
                javadoc.insert(0, lines[doc_start].strip())
            doc_start -= 1
        
        # Find method body using enhanced brace matching
        content = '\n'.join(lines)
        
        # Find the opening brace position
        method_start_char = sum(len(line) + 1 for line in lines[:method_line])  # +1 for newline
        
        # Look for opening brace in the method signature line and following lines
        brace_pos = -1
        search_start = method_start_char
        for i in range(method_line, min(method_line + 5, len(lines))):  # Search up to 5 lines
            line_content = lines[i]
            if '{' in line_content:
                line_start = sum(len(line) + 1 for line in lines[:i])
                brace_pos = line_start + line_content.index('{')
                break
        
        body_end = method_line
        if brace_pos != -1:
            # Use enhanced brace matching
            closing_brace_pos = _find_closing_brace(content, brace_pos)
            if closing_brace_pos != -1:
                # Convert back to line number
                newlines_before_close = content[:closing_brace_pos].count('\n')
                body_end = newlines_before_close
        else:
            # Fallback to simple brace counting
            brace_count = 0
            for i in range(method_line, len(lines)):
                line = lines[i]
                brace_count += line.count('{') - line.count('}')
                body_end = i
                if brace_count == 0 and '{' in ''.join(lines[method_line:i+1]):
                    break
        
        # Extract method parameters
        params = extract_method_parameters(signature_line)
        
        # Extract return type
        return_type = extract_return_type(signature_line)
        
        # Calculate context window
        start = max(0, method_line - context_lines // 2)
        end = min(len(lines), body_end + context_lines // 2)
        
        return {
            'method_name': method_name,
            'signature': signature_line,
            'line_num': method_line + 1,
            'body_start': method_line + 1,
            'body_end': body_end + 1,
            'javadoc': javadoc,
            'parameters': params,
            'return_type': return_type,
            'context_start': start,
            'context_end': end,
            'lines': lines,
            'body_lines': body_end - method_line + 1
        }
    except Exception as e:
        return None

def extract_method_parameters(signature):
    """Extract method parameters from signature."""
    try:
        match = re.search(r'\(([^)]*)\)', signature)
        if match:
            params_str = match.group(1).strip()
            if not params_str:
                return []
            
            params = []
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    # Split type and name
                    parts = param.split()
                    if len(parts) >= 2:
                        param_type = ' '.join(parts[:-1])
                        param_name = parts[-1]
                        params.append({'type': param_type, 'name': param_name})
                    else:
                        params.append({'type': param, 'name': ''})
            return params
    except:
        pass
    return []

def extract_return_type(signature):
    """Extract return type from method signature."""
    try:
        # Remove visibility modifiers and method name/params
        cleaned = re.sub(r'^\s*(public|private|protected)\s+', '', signature)
        cleaned = re.sub(r'\s+(static|final|synchronized|abstract|native)\s+', ' ', cleaned)
        
        # Find return type (everything before method name and parentheses)
        match = re.search(r'^(.*?)\s+\w+\s*\(', cleaned)
        if match:
            return match.group(1).strip()
    except:
        pass
    return 'void'

def find_method_callers(content, method_name):
    """Find where a method is called from."""
    lines = content.splitlines()
    callers = []
    
    # Pattern to find method calls
    call_pattern = rf'\b{re.escape(method_name)}\s*\('
    
    for i, line in enumerate(lines):
        if re.search(call_pattern, line, re.IGNORECASE):
            callers.append({
                'line_num': i + 1,
                'line': line.strip(),
                'context': get_calling_context(lines, i)
            })
    
    return callers

def get_calling_context(lines, line_index):
    """Get context about where a method is being called from."""
    # Look backwards to find the containing method or class
    for i in range(line_index, max(0, line_index - 20), -1):
        line = lines[i].strip()
        
        # Check for method declaration
        if re.match(r'^\s*(public|private|protected).*\w+\s*\([^)]*\)\s*\{?', line):
            return f"in method: {line}"
        
        # Check for class declaration
        if re.match(r'^\s*(public\s+)?class\s+\w+', line):
            return f"in class: {line}"
    
    return "unknown context"

def print_method_navigation_result(results, method_name, show_signature=True, show_callers=False, show_ast_context=False):
    """Print enhanced method navigation results."""
    if not results:
        print(f"Method '{method_name}' not found")
        return
    
    # Initialize AST context finder if needed
    context_finder = None
    if show_ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    
    for i, result in enumerate(results):
        if len(results) > 1:
            print(f"\n{'='*20} Method {i+1} {'='*20}")
        
        # Get AST context if available
        context_str = ""
        if context_finder and 'lines' in result:
            # Get file path from the first argument
            file_path = sys.argv[1] if len(sys.argv) > 1 else None
            if file_path:
                context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(file_path, result['line_num'])
                )
                if context:
                    context_str = f" [{context}]"
        
        print(f"📍 Method: {result['method_name']}{context_str}")
        print(f"📍 Location: lines {result['body_start']}-{result['body_end']} ({result['body_lines']} lines)")
        
        if show_signature:
            print(f"📝 Signature: {result['signature']}")
            
            if result['parameters']:
                print(f"📋 Parameters:")
                for param in result['parameters']:
                    print(f"   • {param['type']} {param['name']}")
            else:
                print(f"📋 Parameters: none")
            
            print(f"↩️  Return type: {result['return_type']}")
        
        # Show JavaDoc if available
        if result['javadoc']:
            print(f"📖 Documentation:")
            for doc_line in result['javadoc'][:3]:  # Show first 3 lines
                print(f"   {doc_line}")
            if len(result['javadoc']) > 3:
                print(f"   ... and {len(result['javadoc']) - 3} more lines")
        
        # Show callers if requested
        if show_callers and 'callers' in result:
            callers = result['callers']
            if callers:
                print(f"📞 Called from {len(callers)} location(s):")
                for caller in callers[:5]:  # Show first 5 callers
                    print(f"   Line {caller['line_num']}: {caller['line']}")
                    if caller['context'] != 'unknown context':
                        print(f"     → {caller['context']}")
                if len(callers) > 5:
                    print(f"   ... and {len(callers) - 5} more locations")
            else:
                print(f"📞 No callers found in this file")
        
        # Show method context
        print(f"\n📄 Method with context:")
        print("=" * 80)
        
        lines = result['lines']
        for j in range(result['context_start'], result['context_end']):
            if j < len(lines):
                is_method_line = result['body_start'] <= j + 1 <= result['body_end']
                is_signature = j + 1 == result['line_num']
                
                if is_signature:
                    prefix = ">>> "
                elif is_method_line:
                    prefix = "  | "
                else:
                    prefix = "    "
                
                print(f"{prefix}{j + 1:4d}: {lines[j]}")

def list_all_targets(targets):
    """List all available navigation targets."""
    print("=" * 80)
    print("NAVIGATION TARGETS")
    print("=" * 80)
    
    # Classes
    if targets['classes']:
        print(f"\nClasses ({len(targets['classes'])}):")
        for cls in sorted(targets['classes'], key=lambda x: x['line']):
            print(f"  {cls['name']:<30} line {cls['line']}")
    
    # Interfaces
    if targets['interfaces']:
        print(f"\nInterfaces ({len(targets['interfaces'])}):")
        for intf in sorted(targets['interfaces'], key=lambda x: x['line']):
            print(f"  {intf['name']:<30} line {intf['line']}")
    
    # Methods
    if targets['methods']:
        print(f"\nMethods ({len(targets['methods'])}):")
        # Group by visibility
        public_methods = [m for m in targets['methods'] if 'public' in m['full_line']]
        private_methods = [m for m in targets['methods'] if 'private' in m['full_line']]
        protected_methods = [m for m in targets['methods'] if 'protected' in m['full_line']]
        package_methods = [m for m in targets['methods'] if not any(v in m['full_line'] for v in ['public', 'private', 'protected'])]
        
        for visibility, methods in [("Public", public_methods), ("Protected", protected_methods), 
                                   ("Package", package_methods), ("Private", private_methods)]:
            if methods:
                print(f"\n  {visibility} ({len(methods)}):")
                for method in sorted(methods, key=lambda x: x['name']):
                    print(f"    {method['signature']:<40} line {method['line']}")
    
    # Fields
    if targets['fields']:
        print(f"\nFields ({len(targets['fields'])}):")
        for field in sorted(targets['fields'], key=lambda x: x['name']):
            print(f"  {field['name']:<30} {field['type']:<20} line {field['line']}")

def print_navigation_result(result, target_type="", show_ast_context=False):
    """Print navigation result with context."""
    # Initialize AST context finder if needed
    context_finder = None
    if show_ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    
    if isinstance(result, list):
        # Multiple results
        if not result:
            print(f"No {target_type} found")
            return
        
        if len(result) == 1:
            result = result[0]
        else:
            print(f"Found {len(result)} occurrences of {target_type}:")
            for i, r in enumerate(result, 1):
                # Get AST context if available
                context_str = ""
                if context_finder:
                    file_path = sys.argv[1] if len(sys.argv) > 1 else None
                    if file_path:
                        context = context_finder._format_context_parts(
                            context_finder.get_context_for_line(file_path, r['line_num'])
                        )
                        if context:
                            context_str = f" [{context}]"
                
                print(f"\n{i}. Line {r['line_num']}{context_str}: {r['line']}")
            return
    
    if not result:
        print(f"{target_type} not found")
        return
    
    # Single result - show with context
    print(f"\n{target_type} at line {result['line_num']}:")
    print("=" * 80)
    
    if 'lines' in result:
        # Line navigation result
        lines = result['lines']
        for i in range(result['start'], result['end']):
            is_target = (i + 1 == result['line_num'])
            prefix = ">>> " if is_target else "    "
            print(f"{prefix}{i + 1:4d}: {lines[i]}")
    else:
        # Method/field navigation result
        with open(sys.argv[1], 'r') as f:
            lines = f.readlines()
        
        for i in range(result['start'], result['end']):
            is_target = (i + 1 == result['line_num'])
            prefix = ">>> " if is_target else "    "
            print(f"{prefix}{i + 1:4d}: {lines[i].rstrip()}")

def search_targets(targets, query):
    """Search for targets matching a query."""
    query_lower = query.lower()
    results = []
    
    # Search in all target types
    for target_type, items in targets.items():
        for item in items:
            if query_lower in item['name'].lower():
                results.append({
                    'type': target_type[:-1],  # Remove 's' from plural
                    'name': item['name'],
                    'line': item['line'],
                    'details': item.get('signature', item.get('type', ''))
                })
    
    return sorted(results, key=lambda x: (x['name'], x['line']))

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Navigate to specific locations in Java files')
    else:
        parser = argparse.ArgumentParser(description='Navigate to specific locations in Java files')
    parser.add_argument('file', help='Java file to navigate')
    parser.add_argument('--to', help='Navigation target (e.g., "method:sendOrder", "line:1500", "field:maxSize")')
    parser.add_argument('--list', action='store_true', help='List all navigation targets')
    parser.add_argument('--search', help='Search for targets containing text')
    parser.add_argument('--show-context', action='store_true', default=True,
                       help='Show context around target (default: True)')
    parser.add_argument('--no-context', dest='show_context', action='store_false',
                       help='Show only the target line')
    parser.add_argument('--window', type=int, default=20,
                       help='Window size for line navigation (default: 20)')
    
    # Multiline ranges support
    parser.add_argument('--ranges', help='Multiple line ranges (e.g., "100-120,200±5,300:10")')
    parser.add_argument('--around-lines', help='Show context around specific line numbers (e.g., "100,200,300")')
    parser.add_argument('--context-size', type=int, default=10,
                       help='Context size for --around-lines (default: 10)')
    
    # Content-based navigation
    parser.add_argument('--to-method', help='Navigate to method and show signature (e.g., "sendOrder")')
    parser.add_argument('--show-signature', action='store_true',
                       help='Show method signature when navigating to methods')
    parser.add_argument('--method-context', type=int, default=20,
                       help='Lines of context around method (default: 20)')
    parser.add_argument('--ast-context', action='store_true',
                       help='Show AST context (class/method) for navigation results')
    parser.add_argument('--encoding', default='utf-8', help='File encoding')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    try:
        with open(args.file, encoding=args.encoding) as f:
            content = f.read()
    except FileNotFoundError:
        LOG.error("File not found: %s", args.file)
        sys.exit(2)
    except UnicodeDecodeError as e:
        LOG.error("Encoding error reading %s – try --encoding", args.file)
        sys.exit(2)
    
    # List all targets if requested
    if args.list:
        targets = find_all_targets(content)
        list_all_targets(targets)
        return
    
    # Search for targets
    if args.search:
        targets = find_all_targets(content)
        results = search_targets(targets, args.search)
        
        if not results:
            print(f"No targets found matching '{args.search}'")
        else:
            print(f"Found {len(results)} target(s) matching '{args.search}':")
            print("-" * 60)
            for r in results:
                details = f" - {r['details']}" if r['details'] else ""
                print(f"{r['type']:<10} {r['name']:<30} line {r['line']:>5}{details}")
        return
    
    # Navigate to specific target
    if args.to:
        if ':' in args.to:
            target_type, target_name = args.to.split(':', 1)
            
            if target_type == 'line':
                try:
                    line_num = int(target_name)
                    result = navigate_to_line(content, line_num, args.window, args.show_context)
                    print_navigation_result(result, f"Line {line_num}", args.ast_context)
                except ValueError:
                    print(f"Error: Invalid line number '{target_name}'")
                    sys.exit(1)
            
            elif target_type == 'method':
                results = navigate_to_method(content, target_name, args.show_context)
                print_navigation_result(results, f"method '{target_name}'", args.ast_context)
            
            elif target_type == 'field':
                results = navigate_to_field(content, target_name, args.show_context)
                print_navigation_result(results, f"field '{target_name}'", args.ast_context)
            
            else:
                print(f"Error: Unknown target type '{target_type}'")
                print("Valid types: method, field, line")
                sys.exit(1)
        else:
            # Try to auto-detect type
            if args.to.isdigit():
                # It's a line number
                line_num = int(args.to)
                result = navigate_to_line(content, line_num, args.window, args.show_context)
                print_navigation_result(result, f"Line {line_num}", args.ast_context)
            else:
                # Try as method first, then field
                results = navigate_to_method(content, args.to, args.show_context)
                if results:
                    print_navigation_result(results, f"method '{args.to}'", args.ast_context)
                else:
                    results = navigate_to_field(content, args.to, args.show_context)
                    if results:
                        print_navigation_result(results, f"field '{args.to}'", args.ast_context)
                    else:
                        print(f"No method or field named '{args.to}' found")
    
    # Handle multiline ranges
    elif args.ranges:
        ranges = args.ranges.split(',')
        results = navigate_to_multiline_ranges(content, ranges, args.show_context)
        
        if not results:
            print("No valid ranges found")
        else:
            print(f"Found {len(results)} range(s):")
            print("=" * 80)
            
            for i, result in enumerate(results):
                if i > 0:
                    print("\n" + "-" * 40)
                
                print(f"Range {result['range']} (lines {result['start_line']}-{result['end_line']}):")
                for j, line in enumerate(result['lines']):
                    line_num = result['start_line'] + j
                    print(f"{line_num:4d}: {line}")
    
    # Handle around-lines
    elif args.around_lines:
        line_numbers = [int(x.strip()) for x in args.around_lines.split(',')]
        ranges = [f"{line_num}±{args.context_size}" for line_num in line_numbers]
        results = navigate_to_multiline_ranges(content, ranges, args.show_context)
        
        if not results:
            print("No valid line numbers found")
        else:
            print(f"Context around {len(line_numbers)} line(s):")
            print("=" * 80)
            
            for i, result in enumerate(results):
                if i > 0:
                    print("\n" + "-" * 40)
                
                center_line = line_numbers[i]
                print(f"Context around line {center_line} (showing lines {result['start_line']}-{result['end_line']}):")
                for j, line in enumerate(result['lines']):
                    line_num = result['start_line'] + j
                    prefix = ">>> " if line_num == center_line else "    "
                    print(f"{prefix}{line_num:4d}: {line}")
    
    # Handle enhanced method navigation
    elif args.to_method:
        results = navigate_to_method_enhanced(
            content, args.to_method, 
            show_signature=args.show_signature, 
            show_callers=args.show_callers,
            context_lines=args.method_context
        )
        print_method_navigation_result(
            results, args.to_method, 
            show_signature=args.show_signature,
            show_callers=args.show_callers,
            show_ast_context=args.ast_context
        )
    
    else:
        print("Error: Please specify --to, --list, --search, --ranges, --around-lines, or --to-method")
        sys.exit(1)

if __name__ == "__main__":
    main()