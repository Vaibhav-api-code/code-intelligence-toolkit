#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Block extraction module extracted from find_text_v6.py.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import ast
import re
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

def detect_language(file_path: str, content: str = None) -> str:
    """Detect programming language from file extension and content."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix in ['.py', '.pyw', '.pyi']:
        return 'python'
    elif suffix in ['.java']:
        return 'java'
    elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
        return 'javascript'
    elif suffix in ['.cpp', '.cc', '.cxx', '.hpp', '.h']:
        return 'cpp'
    elif suffix in ['.c', '.h']:
        return 'c'
    elif suffix in ['.go']:
        return 'go'
    elif suffix in ['.rs']:
        return 'rust'
    
    # Try to detect from content if available
    if content:
        if 'def ' in content and 'import ' in content:
            return 'python'
        elif 'public class' in content or 'private class' in content:
            return 'java'
        elif 'function ' in content and ('{' in content or '=>' in content):
            return 'javascript'
    
    return 'unknown'

def extract_python_block_ast(content: str, target_line: int) -> Optional[Tuple[int, int, str]]:
    """
    Extract code block containing target line using Python AST.
    
    Returns:
        Tuple of (start_line, end_line, block_type) or None
    """
    try:
        tree = ast.parse(content)
        lines = content.splitlines()
        
        class BlockFinder(ast.NodeVisitor):
            def __init__(self):
                self.found_block = None
                self.target_line = target_line
            
            def visit_node_with_body(self, node, block_type):
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    
                    # Check if target line is within this block
                    if start_line <= self.target_line <= end_line:
                        # Find the most specific (smallest) block containing the line
                        if (self.found_block is None or 
                            (end_line - start_line) < (self.found_block[1] - self.found_block[0])):
                            self.found_block = (start_line, end_line, block_type)
                
                self.generic_visit(node)
            
            def visit_If(self, node):
                self.visit_node_with_body(node, 'if')
            
            def visit_For(self, node):
                self.visit_node_with_body(node, 'for')
            
            def visit_While(self, node):
                self.visit_node_with_body(node, 'while')
            
            def visit_Try(self, node):
                self.visit_node_with_body(node, 'try')
            
            def visit_With(self, node):
                self.visit_node_with_body(node, 'with')
            
            def visit_FunctionDef(self, node):
                self.visit_node_with_body(node, 'function')
            
            def visit_AsyncFunctionDef(self, node):
                self.visit_node_with_body(node, 'async_function')
            
            def visit_ClassDef(self, node):
                self.visit_node_with_body(node, 'class')
        
        finder = BlockFinder()
        finder.visit(tree)
        return finder.found_block
        
    except SyntaxError:
        return None
    except Exception:
        return None

def extract_java_block_regex(content: str, target_line: int) -> Optional[Tuple[int, int, str]]:
    """
    Extract Java code block using regex patterns for common structures.
    
    Returns:
        Tuple of (start_line, end_line, block_type) or None
    """
    lines = content.splitlines()
    if target_line > len(lines):
        return None
    
    # Look backwards from target line to find block start
    block_patterns = [
        (r'^\s*if\s*\(', 'if'),
        (r'^\s*for\s*\(', 'for'), 
        (r'^\s*while\s*\(', 'while'),
        (r'^\s*try\s*\{', 'try'),
        (r'^\s*catch\s*\(', 'catch'),
        (r'^\s*finally\s*\{', 'finally'),
        (r'^\s*(public|private|protected)?\s*(static)?\s*\w+.*\(.*\)\s*\{', 'method'),
        (r'^\s*(public|private|protected)?\s*class\s+\w+', 'class'),
    ]
    
    start_line = None
    block_type = None
    
    # Search backwards for block start
    for line_num in range(target_line - 1, max(0, target_line - 50), -1):
        line = lines[line_num]
        for pattern, b_type in block_patterns:
            if re.match(pattern, line):
                start_line = line_num + 1  # Convert to 1-based
                block_type = b_type
                break
        if start_line:
            break
    
    if not start_line:
        return None
    
    # Find block end by counting braces
    brace_count = 0
    end_line = start_line
    in_block = False
    
    for line_num in range(start_line - 1, len(lines)):
        line = lines[line_num]
        
        # Count braces in line
        for char in line:
            if char == '{':
                brace_count += 1
                in_block = True
            elif char == '}':
                brace_count -= 1
                
                # Block ends when brace count returns to 0
                if in_block and brace_count == 0:
                    end_line = line_num + 1  # Convert to 1-based
                    return (start_line, end_line, block_type)
    
    # If we didn't find a clean end, return a reasonable boundary
    return (start_line, min(start_line + 50, len(lines)), block_type)

def extract_javascript_block_regex(content: str, target_line: int) -> Optional[Tuple[int, int, str]]:
    """
    Extract JavaScript code block using regex patterns.
    
    Returns:
        Tuple of (start_line, end_line, block_type) or None
    """
    lines = content.splitlines()
    if target_line > len(lines):
        return None
    
    block_patterns = [
        (r'^\s*if\s*\(', 'if'),
        (r'^\s*for\s*\(', 'for'),
        (r'^\s*while\s*\(', 'while'),
        (r'^\s*try\s*\{', 'try'),
        (r'^\s*catch\s*\(', 'catch'),
        (r'^\s*function\s+\w+', 'function'),
        (r'^\s*const\s+\w+\s*=\s*\(.*\)\s*=>', 'arrow_function'),
        (r'^\s*class\s+\w+', 'class'),
    ]
    
    # Similar logic to Java but adapted for JavaScript syntax
    start_line = None
    block_type = None
    
    for line_num in range(target_line - 1, max(0, target_line - 50), -1):
        line = lines[line_num]
        for pattern, b_type in block_patterns:
            if re.match(pattern, line):
                start_line = line_num + 1
                block_type = b_type
                break
        if start_line:
            break
    
    if not start_line:
        return None
    
    # JavaScript uses similar brace counting to Java
    brace_count = 0
    end_line = start_line
    in_block = False
    
    for line_num in range(start_line - 1, len(lines)):
        line = lines[line_num]
        
        for char in line:
            if char == '{':
                brace_count += 1
                in_block = True
            elif char == '}':
                brace_count -= 1
                if in_block and brace_count == 0:
                    end_line = line_num + 1
                    return (start_line, end_line, block_type)
    
    return (start_line, min(start_line + 50, len(lines)), block_type)

def extract_block_for_line(file_path: str, content: str, line_number: int) -> Optional[Dict[str, Any]]:
    """
    Extract the code block containing the specified line.
    
    Args:
        file_path: Path to the file (for language detection)
        content: File content
        line_number: Target line number (1-based)
        
    Returns:
        Dictionary with block information or None
    """
    language = detect_language(file_path, content)
    lines = content.splitlines()
    
    if line_number < 1 or line_number > len(lines):
        return None
    
    block_info = None
    
    # Use language-specific block extraction
    if language == 'python':
        block_info = extract_python_block_ast(content, line_number)
    elif language == 'java':
        block_info = extract_java_block_regex(content, line_number)
    elif language in ['javascript', 'typescript']:
        block_info = extract_javascript_block_regex(content, line_number)
    else:
        # Generic approach for unknown languages
        # Try to find some kind of block structure
        block_info = extract_generic_block(content, line_number)
    
    if not block_info:
        return None
    
    start_line, end_line, block_type = block_info
    
    # Extract the block content
    block_lines = lines[start_line-1:end_line]
    block_content = '\n'.join(block_lines)
    
    return {
        'start_line': start_line,
        'end_line': end_line,
        'block_type': block_type,
        'content': block_content,
        'line_count': end_line - start_line + 1,
        'language': language,
        'target_line': line_number,
        'relative_line': line_number - start_line + 1
    }

def extract_generic_block(content: str, target_line: int) -> Optional[Tuple[int, int, str]]:
    """
    Generic block extraction for unknown languages.
    Looks for indentation-based or brace-based blocks.
    """
    lines = content.splitlines()
    if target_line > len(lines):
        return None
    
    # Check if this looks like a brace-based language
    has_braces = '{' in content and '}' in content
    
    if has_braces:
        # Use brace counting similar to Java/JavaScript
        return extract_brace_block(lines, target_line)
    else:
        # Use indentation-based approach similar to Python
        return extract_indentation_block(lines, target_line)

def extract_brace_block(lines: List[str], target_line: int) -> Optional[Tuple[int, int, str]]:
    """Extract block based on brace matching."""
    # Simple brace-based block detection
    start_line = target_line
    end_line = target_line
    
    # Find start by looking for opening brace
    for line_num in range(target_line - 1, max(0, target_line - 20), -1):
        if '{' in lines[line_num]:
            start_line = line_num + 1
            break
    
    # Find end by counting braces
    brace_count = 0
    for line_num in range(start_line - 1, len(lines)):
        line = lines[line_num]
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0 and '}' in line:
            end_line = line_num + 1
            break
    
    return (start_line, end_line, 'block')

def extract_indentation_block(lines: List[str], target_line: int) -> Optional[Tuple[int, int, str]]:
    """Extract block based on indentation."""
    if target_line > len(lines):
        return None
    
    target_line_content = lines[target_line - 1]
    if not target_line_content.strip():
        return None
    
    # Get indentation level of target line
    target_indent = len(target_line_content) - len(target_line_content.lstrip())
    
    # Find block boundaries based on indentation
    start_line = target_line
    end_line = target_line
    
    # Look backwards for start
    for line_num in range(target_line - 2, -1, -1):
        line = lines[line_num]
        if line.strip():  # Skip empty lines
            indent = len(line) - len(line.lstrip())
            if indent < target_indent:
                start_line = line_num + 2  # Start after this line
                break
            start_line = line_num + 1
    
    # Look forwards for end
    for line_num in range(target_line, len(lines)):
        line = lines[line_num]
        if line.strip():  # Skip empty lines
            indent = len(line) - len(line.lstrip())
            if indent < target_indent:
                end_line = line_num
                break
            end_line = line_num + 1
    
    return (start_line, end_line, 'indented_block')

def extract_multiple_blocks(file_path: str, content: str, line_numbers: List[int]) -> List[Dict[str, Any]]:
    """
    Extract blocks for multiple line numbers.
    
    Args:
        file_path: Path to the file
        content: File content
        line_numbers: List of target line numbers
        
    Returns:
        List of block information dictionaries
    """
    blocks = []
    for line_num in line_numbers:
        block = extract_block_for_line(file_path, content, line_num)
        if block:
            blocks.append(block)
    return blocks

def format_block_output(block: Dict[str, Any], show_line_numbers: bool = True) -> str:
    """
    Format block for display.
    
    Args:
        block: Block information dictionary
        show_line_numbers: Whether to show line numbers
        
    Returns:
        Formatted block string
    """
    if not block:
        return ""
    
    lines = block['content'].splitlines()
    output_lines = []
    
    # Add header
    header = f"[{block['block_type'].title()} block at lines {block['start_line']}-{block['end_line']}]"
    output_lines.append(header)
    output_lines.append("=" * len(header))
    
    # Add content with optional line numbers
    for i, line in enumerate(lines):
        if show_line_numbers:
            line_num = block['start_line'] + i
            # Highlight the target line
            marker = " >>> " if line_num == block['target_line'] else "     "
            output_lines.append(f"{line_num:4d}:{marker}{line}")
        else:
            marker = " >>> " if i == block['relative_line'] - 1 else "     "
            output_lines.append(f"{marker}{line}")
    
    output_lines.append("=" * len(header))
    
    return '\n'.join(output_lines)

if __name__ == "__main__":
    # Test the module
    print("Testing block extraction...")
    
    # Test Python code
    python_code = '''
def example_function():
    if True:
        for i in range(10):
            try:
                print(i)
            except:
                pass
    '''
    
    block = extract_block_for_line("test.py", python_code, 5)
    if block:
        print("✓ Python block extraction working")
        print(format_block_output(block))
    else:
        print("✗ Python block extraction failed")
    
    # Test Java code
    java_code = '''
public class Test {
    public void method() {
        if (condition) {
            for (int i = 0; i < 10; i++) {
                System.out.println(i);
            }
        }
    }
}
    '''
    
    block = extract_block_for_line("Test.java", java_code, 6)
    if block:
        print("✓ Java block extraction working") 
        print(format_block_output(block))
    else:
        print("✗ Java block extraction failed")