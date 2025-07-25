#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced text replacement tool (v7) with advanced features and cross-platform robustness.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import os
import re
import difflib
import tempfile
import shutil
import argparse
import logging
import subprocess
import ast
import time
import errno
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any

# ────────────────────────────  logging  ────────────────────────────
LOG = logging.getLogger("replace_text_v7")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s"
)

# Import shared modules (new in v7)
try:
    from ripgrep_integration import (
        execute_ripgrep_search, find_ripgrep, build_ripgrep_command,
        parse_ripgrep_output, find_files_with_ripgrep
    )
    HAS_RIPGREP_INTEGRATION = True
except ImportError:
    HAS_RIPGREP_INTEGRATION = False
    print("Warning: ripgrep_integration module not found. Some features may be limited.", file=sys.stderr)

try:
    from block_extraction import (
        extract_block_for_line, extract_multiple_blocks, 
        format_block_output, detect_language
    )
    HAS_BLOCK_EXTRACTION = True
except ImportError:
    HAS_BLOCK_EXTRACTION = False
    print("Warning: block_extraction module not found. Block-aware features disabled.", file=sys.stderr)

try:
    from json_pipeline import (
        load_search_results_from_file, load_search_results_from_stdin,
        SearchResults, SearchMatch, create_replacement_plan,
        validate_search_results, print_search_results_summary
    )
    HAS_JSON_PIPELINE = True
except ImportError:
    HAS_JSON_PIPELINE = False
    print("Warning: json_pipeline module not found. JSON pipeline features disabled.", file=sys.stderr)

# Enhanced standard argument parser (prefer over standard)
try:
    from enhanced_standard_arg_parser import create_search_parser
    HAS_ENHANCED_PARSER = True
except ImportError:
    try:
        from standard_arg_parser import create_standard_parser as create_parser
        HAS_ENHANCED_PARSER = False
        HAS_STANDARD_PARSER = True
    except ImportError:
        HAS_ENHANCED_PARSER = False
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
        def check_regex_pattern(pattern):
            return True, ""

# Load common configuration system
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass

# Try to import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

# ────────────────────────────  Core V7 Features  ────────────────────────────

def find_files_for_replacement(search_args: Dict[str, Any]) -> List[str]:
    """
    Enhanced file discovery using ripgrep integration (NEW IN V7).
    Falls back to traditional methods if ripgrep not available.
    """
    if not HAS_RIPGREP_INTEGRATION:
        return get_files_to_process_legacy(
            search_args.get('paths', ['.']),
            search_args.get('glob', '*'),
            search_args.get('git_only', False),
            search_args.get('staged_only', False),
            search_args.get('language')
        )
    
    # Use ripgrep for file discovery
    search_paths = search_args.get('paths', ['.'])
    glob_patterns = search_args.get('glob_patterns', [])
    exclude_patterns = search_args.get('exclude_patterns', [])
    
    try:
        files = find_files_with_ripgrep(search_paths, glob_patterns, exclude_patterns)
        return [str(Path(f).resolve()) for f in files]
    except Exception as e:
        LOG.warning(f"Ripgrep file discovery failed: {e}, falling back to legacy method")
        return get_files_to_process_legacy(
            search_args.get('paths', ['.']),
            search_args.get('glob', '*'),
            search_args.get('git_only', False),
            search_args.get('staged_only', False),
            search_args.get('language')
        )

def search_for_pattern_with_ripgrep(pattern: str, search_args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Use ripgrep to find pattern matches with full context (NEW IN V7).
    """
    if not HAS_RIPGREP_INTEGRATION:
        return []
    
    try:
        results, success = execute_ripgrep_search(
            pattern,
            search_args.get('paths', ['.']),
            context_before=search_args.get('context_before', 0),
            context_after=search_args.get('context_after', 0),
            case_insensitive=search_args.get('case_insensitive', False),
            whole_word=search_args.get('whole_word', False),
            search_type=search_args.get('search_type', 'text'),
            glob_patterns=search_args.get('glob_patterns'),
            exclude_patterns=search_args.get('exclude_patterns'),
            recursive=search_args.get('recursive', True)
        )
        
        return results if success else []
    except Exception as e:
        LOG.warning(f"Ripgrep search failed: {e}")
        return []

def apply_block_aware_replacement(file_path: str, content: str, old_text: str, new_text: str,
                                 block_mode: str = 'preserve', target_lines: List[int] = None) -> Tuple[str, int]:
    """
    Apply replacement with block awareness (NEW IN V7).
    
    Args:
        file_path: Path to file being processed
        content: File content
        old_text: Text to replace
        new_text: Replacement text
        block_mode: 'preserve', 'within', or 'extract'
        target_lines: Specific lines to target (from find results)
        
    Returns:
        Modified content and number of replacements
    """
    if not HAS_BLOCK_EXTRACTION:
        # Fallback to regular replacement
        return replace_exact(content, old_text, new_text)
    
    if block_mode == 'preserve':
        # Standard replacement but preserve block structure
        return replace_exact(content, old_text, new_text)
    elif block_mode == 'within' and target_lines:
        # Replace only within blocks containing target lines
        return replace_within_blocks(file_path, content, old_text, new_text, target_lines)
    elif block_mode == 'extract':
        # Extract blocks and replace within them
        return replace_with_block_extraction(file_path, content, old_text, new_text, target_lines)
    else:
        return replace_exact(content, old_text, new_text)

def replace_within_blocks(file_path: str, content: str, old_text: str, new_text: str, 
                         target_lines: List[int]) -> Tuple[str, int]:
    """
    Replace text only within blocks containing the target lines.
    """
    lines = content.splitlines(keepends=True)
    total_replacements = 0
    
    # Extract all blocks for target lines
    blocks = extract_multiple_blocks(file_path, content, target_lines)
    
    if not blocks:
        return content, 0
    
    # Create a set of all line numbers that are within blocks
    block_lines = set()
    for block in blocks:
        for line_num in range(block['start_line'], block['end_line'] + 1):
            block_lines.add(line_num)
    
    # Replace only in lines that are within blocks
    for i, line in enumerate(lines):
        line_number = i + 1  # Convert to 1-based
        if line_number in block_lines:
            modified_line, count = replace_exact(line, old_text, new_text)
            if count > 0:
                lines[i] = modified_line
                total_replacements += count
    
    return ''.join(lines), total_replacements

def replace_with_block_extraction(file_path: str, content: str, old_text: str, new_text: str,
                                 target_lines: List[int]) -> Tuple[str, int]:
    """
    Extract blocks, apply replacements, and reintegrate.
    """
    if not target_lines:
        return replace_exact(content, old_text, new_text)
    
    lines = content.splitlines(keepends=True)
    total_replacements = 0
    
    # Extract blocks for each target line
    blocks = extract_multiple_blocks(file_path, content, target_lines)
    
    # Sort blocks by start line (process from end to start to avoid line number shifts)
    blocks.sort(key=lambda b: b['start_line'], reverse=True)
    
    for block in blocks:
        # Extract block content
        block_content = block['content']
        
        # Apply replacement to block
        modified_block, count = replace_exact(block_content, old_text, new_text)
        total_replacements += count
        
        if count > 0:
            # Replace the block in the original content
            start_idx = block['start_line'] - 1
            end_idx = block['end_line']
            
            # Replace lines with modified block
            modified_lines = modified_block.splitlines(keepends=True)
            lines[start_idx:end_idx] = modified_lines
    
    return ''.join(lines), total_replacements

def add_ast_context_to_replacements(file_path: str, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhance replacement matches with AST context information (NEW IN V7).
    """
    if not HAS_AST_CONTEXT:
        return matches
    
    try:
        context_finder = ASTContextFinder()
        
        for match in matches:
            line_number = match.get('line_number')
            if line_number:
                context_parts = context_finder.get_context_for_line(file_path, line_number)
                if context_parts:
                    match['ast_context'] = context_finder._format_context_parts(context_parts)
                    
                    # Extract individual context components
                    if context_parts:
                        for part in context_parts:
                            if part.node_type == 'class':
                                match['class_name'] = part.name
                            elif part.node_type in ['method', 'function']:
                                match['method_name'] = part.name
        
        return matches
    except Exception as e:
        LOG.warning(f"AST context extraction failed: {e}")
        return matches

def process_json_pipeline_input(json_input: str) -> Tuple[str, str, List[Dict[str, Any]]]:
    """
    Process JSON pipeline input from find_text (NEW IN V7).
    
    Returns:
        Tuple of (search_pattern, search_type, enhanced_matches)
    """
    if not HAS_JSON_PIPELINE:
        raise ValueError("JSON pipeline support not available")
    
    try:
        if json_input == '-':
            results = load_search_results_from_stdin()
        elif os.path.isfile(json_input):
            results = load_search_results_from_file(json_input)
        else:
            # Treat as JSON string
            from json_pipeline import deserialize_search_results
            results = deserialize_search_results(json_input)
        
        # Validate results
        errors = validate_search_results(results)
        if errors:
            raise ValueError(f"Invalid search results: {'; '.join(errors)}")
        
        # Convert to matches format
        matches = []
        for match in results.matches:
            match_dict = {
                'file_path': match.file_path,
                'line_number': match.line_number,
                'content': match.content,
                'is_match': True
            }
            
            # Add context information if available
            if match.context:
                if match.context.ast_context:
                    match_dict['ast_context'] = match.context.ast_context
                if match.context.block_type:
                    match_dict['block_type'] = match.context.block_type
                    match_dict['block_start'] = match.context.block_start
                    match_dict['block_end'] = match.context.block_end
                if match.context.method_name:
                    match_dict['method_name'] = match.context.method_name
                if match.context.class_name:
                    match_dict['class_name'] = match.context.class_name
            
            matches.append(match_dict)
        
        return results.search_pattern, results.search_type, matches
        
    except Exception as e:
        raise ValueError(f"Error processing JSON pipeline input: {e}")

# ────────────────────────────  Legacy Functions (Preserved for Compatibility)  ────────────────────────────

def is_file_locked(filepath):
    """Check if a file is currently locked for writing."""
    import platform
    
    if platform.system() != 'Windows':
        try:
            with open(filepath, 'r+b') as f:
                try:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    return False, None
                except IOError:
                    try:
                        result = subprocess.run(['lsof', '-t', str(filepath)], 
                                              capture_output=True, text=True, timeout=1)
                        if result.returncode == 0 and result.stdout.strip():
                            pids = result.stdout.strip().split('\n')
                            return True, f"locked by process(es): {', '.join(pids)}"
                    except:
                        pass
                    return True, "locked by another process"
                except ImportError:
                    pass
        except PermissionError:
            return True, "permission denied"
        except Exception:
            pass
    
    try:
        test_fd = os.open(str(filepath), os.O_RDWR | os.O_EXCL)
        os.close(test_fd)
        return False, None
    except OSError as e:
        if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY):
            return True, "locked or in use by another process"
        elif e.errno == errno.ENOENT:
            return False, "file does not exist"
    except Exception:
        pass
    
    try:
        os.rename(str(filepath), str(filepath))
        return False, None
    except OSError:
        return True, "file is in use"
    except Exception:
        return False, None

def read_file(filepath):
    """Read file contents preserving exact format."""
    try:
        with open(filepath, 'r', encoding='utf-8', newline='') as f:
            return f.read()
    except UnicodeDecodeError:
        print(f"Error: File appears to be binary or has encoding issues", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

def _atomic_write(path: Path, data: str, bak: bool = False, max_retries: int = 3, retry_delay: float = 1.0) -> None:
    """Write atomically with retry logic for locked files."""
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    tmp = Path(tmp_path)
    
    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8', newline='') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        try:
            os.close(tmp_fd)
        except:
            pass
        try:
            tmp.unlink()
        except:
            pass
        raise
    
    if bak and path.exists():
        try:
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        except Exception as e:
            try:
                tmp.unlink()
            except:
                pass
            raise Exception(f"Failed to create backup: {e}")
    
    last_error = None
    for attempt in range(max_retries):
        try:
            os.replace(str(tmp), str(path))
            return
        except OSError as e:
            last_error = e
            if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.ETXTBSY):
                if attempt < max_retries - 1:
                    if not os.getenv('QUIET_MODE'):
                        print(f"File {path} appears to be locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
            try:
                tmp.unlink()
            except:
                pass
            raise
    
    try:
        tmp.unlink()
    except:
        pass
    raise OSError(f"Failed to write {path} after {max_retries} attempts: {last_error}")

def show_diff(original, modified, filepath, show_ast_context=False):
    """Show unified diff of changes with optional AST context."""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"{filepath} (original)",
        tofile=f"{filepath} (modified)",
        lineterm=''
    )
    
    diff_lines = list(diff)
    if diff_lines:
        print("\nChanges to be made:")
        
        # Enhanced diff display with AST context (NEW IN V7)
        context_finder = None
        if show_ast_context and HAS_AST_CONTEXT:
            try:
                context_finder = ASTContextFinder()
            except Exception:
                pass
        
        for line in diff_lines:
            # Extract line number from diff output and add AST context
            if line.startswith('@@') and context_finder:
                match = re.search(r'\+([0-9]+)', line)
                if match:
                    line_num = int(match.group(1))
                    try:
                        context_parts = context_finder.get_context_for_line(filepath, line_num)
                        if context_parts:
                            context = context_finder._format_context_parts(context_parts)
                            print(f"{line.rstrip()} [{context}]")
                            continue
                    except Exception:
                        pass
            
            print(line.rstrip())
    
    return bool(diff_lines)

def replace_exact(content, old_text, new_text, count=-1):
    """Replace exact text occurrences without recursive replacement."""
    if old_text == new_text or old_text == "":
        return content, 0
    
    positions = []
    start = 0
    while True:
        pos = content.find(old_text, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + len(old_text)
    
    if count != -1 and count < len(positions):
        positions = positions[:count]
    
    if not positions:
        return content, 0
    
    result = []
    last_end = 0
    
    for pos in positions:
        result.append(content[last_end:pos])
        result.append(new_text)
        last_end = pos + len(old_text)
    
    result.append(content[last_end:])
    
    return ''.join(result), len(positions)

def replace_regex(content, pattern, replacement, flags=0, count=0):
    """Replace using regex pattern with safety checks."""
    try:
        if pattern in ['', '^', '$', r'\b', r'\B']:
            print(f"Error: Zero-width pattern '{pattern}' not supported", file=sys.stderr)
            sys.exit(1)
        
        regex = re.compile(pattern, flags)
        
        import re as regex_module
        nested_quantifiers = regex_module.findall(r'\([^)]*[+*]\)[+*]', pattern)
        if nested_quantifiers or any(dangerous in pattern for dangerous in ['(.*)*', '(.+)+', '(.*)+', '(.+)*']):
            print(f"Warning: Pattern may cause performance issues: {pattern}", file=sys.stderr)
        
        modified_content, num_replacements = regex.subn(replacement, content, count=count)
        return modified_content, num_replacements
    except re.error as e:
        print(f"Invalid regex pattern: {e}", file=sys.stderr)
        sys.exit(1)

def replace_in_range(content, old_text, new_text, start_line=None, end_line=None):
    """Replace text only within specified line range."""
    lines = content.splitlines(keepends=True)
    
    if start_line is None:
        start_line = 1
    if end_line is None:
        end_line = len(lines)
    
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    
    total_replacements = 0
    for i in range(start_idx, end_idx):
        original_line = lines[i]
        modified_line, count = replace_exact(original_line, old_text, new_text)
        if count > 0:
            lines[i] = modified_line
            total_replacements += count
    
    return ''.join(lines), total_replacements

def replace_whole_word(content, word, replacement):
    """Replace whole words only."""
    pattern = r'\b' + re.escape(word) + r'\b'
    return re.subn(pattern, replacement, content)

def get_comment_patterns(language):
    """Get comment patterns for different programming languages."""
    patterns = {
        'default': {
            'single': r'//.*$',
            'multi': r'/\*.*?\*/',
        },
        'python': {
            'single': r'#.*$',
            'multi': r'(""".*?"""|' + r"'''.*?''')",
        },
        'ruby': {
            'single': r'#.*$',
            'multi': r'=begin.*?=end',
        },
        'sql': {
            'single': r'--.*$',
            'multi': r'/\*.*?\*/',
        },
        'lua': {
            'single': r'--.*$',
            'multi': r'--\[\[.*?\]\]',
        },
    }
    
    c_style_langs = ['java', 'javascript', 'typescript', 'cpp', 'c', 'go', 'rust', 'php']
    if language in c_style_langs:
        return patterns['default']
    
    return patterns.get(language, patterns['default'])

def replace_in_comments(content, old_text, new_text, language=None):
    """Replace text only within comments (language-aware)."""
    total_replacements = 0
    patterns = get_comment_patterns(language)
    
    def replace_in_single_line_comment(match):
        nonlocal total_replacements
        comment = match.group(0)
        modified_comment, count = replace_exact(comment, old_text, new_text)
        total_replacements += count
        return modified_comment
    
    if patterns['single']:
        content = re.sub(patterns['single'], replace_in_single_line_comment, content, flags=re.MULTILINE)
    
    def replace_in_multi_line_comment(match):
        nonlocal total_replacements
        comment = match.group(0)
        modified_comment, count = replace_exact(comment, old_text, new_text)
        total_replacements += count
        return modified_comment
    
    if patterns['multi']:
        content = re.sub(patterns['multi'], replace_in_multi_line_comment, content, flags=re.DOTALL)
    
    return content, total_replacements

def get_string_patterns(language):
    """Get string literal patterns for different programming languages."""
    patterns = {
        'default': [
            (r'"(?:[^"\\]|\\.)*"', '"'),
            (r"'(?:[^'\\]|\\.)*'", "'"),
        ],
        'python': [
            (r'""".*?"""|' + r"'''.*?'''", '"""'),
            (r'"(?:[^"\\]|\\.)*"', '"'),
            (r"'(?:[^'\\]|\\.)*'", "'"),
        ],
        'java': [
            (r'"(?:[^"\\]|\\.)*"', '"'),
        ],
        'rust': [
            (r'"(?:[^"\\]|\\.)*"', '"'),
            (r"r#*\".*?\"#*", 'r#"'),
        ],
        'go': [
            (r'"(?:[^"\\]|\\.)*"', '"'),
            (r'`[^`]*`', '`'),
        ],
    }
    
    return patterns.get(language, patterns['default'])

def replace_in_strings(content, old_text, new_text, language=None):
    """Replace text only within string literals (language-aware)."""
    total_replacements = 0
    patterns = get_string_patterns(language)
    
    for pattern, quote_char in patterns:
        def replace_in_string(match):
            nonlocal total_replacements
            string_literal = match.group(0)
            if quote_char in ['"""', "'''", 'r#"']:
                quote_len = len(quote_char)
                inner = string_literal[quote_len:-quote_len]
            elif quote_char == '`':
                inner = string_literal[1:-1]
            else:
                inner = string_literal[1:-1]
            
            inner_replaced, count = replace_exact(inner, old_text, new_text)
            total_replacements += count
            
            if quote_char in ['"""', "'''"]:
                return f'{quote_char}{inner_replaced}{quote_char}'
            elif quote_char == 'r#"':
                prefix_match = re.match(r'(r#*\")', string_literal)
                if prefix_match:
                    prefix = prefix_match.group(1)
                    suffix = prefix.replace('r', '').replace('\"', '\"#')
                    return f'{prefix}{inner_replaced}{suffix}'
            elif quote_char == '`':
                return f'`{inner_replaced}`'
            else:
                return f'{quote_char}{inner_replaced}{quote_char}'
        
        content = re.sub(pattern, replace_in_string, content, flags=re.DOTALL if quote_char in ['"""', "'''"] else 0)
    
    return content, total_replacements

def check_compile_status(file_path, language=None):
    """Check if file compiles/has valid syntax."""
    try:
        path = Path(file_path)
        if not path.exists():
            return True, "File not found"
        
        try:
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:
                return False, "Cannot check - file too large"
        except OSError:
            return False, "Cannot check - size unknown"
        
        if not language:
            suffix = path.suffix.lower()
            if suffix == '.py':
                language = 'python'
            elif suffix == '.java':
                language = 'java'
            elif suffix in ['.js', '.jsx']:
                language = 'javascript'
            elif suffix in ['.ts', '.tsx']:
                language = 'typescript'
            else:
                return False, "Cannot check - unknown language"
        
        if language == 'python':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    return False, "Cannot check - empty file"
                
                ast.parse(content)
                return True, "Compiles"
            except SyntaxError:
                return False, "Syntax Error"
            except UnicodeDecodeError:
                return False, "Cannot check - encoding issue"
            except Exception:
                return False, "Cannot check - parse failed"
        
        elif language == 'java':
            try:
                result = subprocess.run(
                    ['javac', '-version'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode != 0:
                    return False, "Cannot check - javac unavailable"
                
                result = subprocess.run(
                    ['javac', '-cp', '.', str(file_path)],
                    capture_output=True, text=True, timeout=30
                )
                
                class_file = path.with_suffix('.class')
                if class_file.exists():
                    try:
                        class_file.unlink()
                    except OSError:
                        pass
                
                if result.returncode == 0:
                    return True, "Compiles"
                else:
                    return False, "Compile Error"
                    
            except subprocess.TimeoutExpired:
                return False, "Cannot check - compile timeout"
            except FileNotFoundError:
                return False, "Cannot check - javac not found"
            except Exception:
                return False, "Cannot check - compile failed"
        
        elif language in ['javascript', 'typescript']:
            try:
                if language == 'javascript':
                    result = subprocess.run(
                        ['node', '--version'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode != 0:
                        return False, "Cannot check - node unavailable"
                    
                    result = subprocess.run(
                        ['node', '-c', str(file_path)],
                        capture_output=True, text=True, timeout=15
                    )
                else:
                    result = subprocess.run(
                        ['tsc', '--version'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode != 0:
                        return False, "Cannot check - tsc unavailable"
                    
                    result = subprocess.run(
                        ['tsc', '--noEmit', str(file_path)],
                        capture_output=True, text=True, timeout=20
                    )
                
                if result.returncode == 0:
                    return True, "Compiles"
                else:
                    return False, "Syntax Error"
                    
            except subprocess.TimeoutExpired:
                return False, "Cannot check - timeout"
            except FileNotFoundError:
                return False, "Cannot check - compiler not found"
            except Exception:
                return False, "Cannot check - check failed"
        
        return False, "Cannot check - unsupported language"
    
    except Exception:
        return False, "Cannot check - internal error"

def get_files_to_process_legacy(paths, glob_pattern, git_only, staged_only, language=None):
    """Legacy file processing method (preserved for compatibility)."""
    files_to_process = set()
    
    language_extensions = {
        'python': ['.py', '.pyw', '.pyi'],
        'java': ['.java'],
        'javascript': ['.js', '.jsx', '.mjs'],
        'typescript': ['.ts', '.tsx'],
        'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
        'c': ['.c', '.h'],
        'go': ['.go'],
        'rust': ['.rs'],
        'ruby': ['.rb'],
        'php': ['.php'],
        'sql': ['.sql'],
        'lua': ['.lua']
    }
    
    def should_include_file(file_path, language, language_extensions):
        if language and language in language_extensions:
            return any(file_path.suffix == ext for ext in language_extensions[language])
        return True

    if git_only or staged_only:
        try:
            # NOTE: Using direct git for read-only operations (ls-files, diff --name-only)
            # These are safe operations that don't modify repository state
            git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], 
                                             text=True, stderr=subprocess.PIPE).strip()
            
            original_cwd = os.getcwd()
            os.chdir(git_root)
            
            try:
                if staged_only:
                    cmd = ['git', 'diff', '--name-only', '--cached']
                else:
                    cmd = ['git', 'ls-files']
                
                git_files = subprocess.check_output(cmd, text=True).splitlines()
                for file_path in git_files:
                    full_path = Path(git_root) / file_path
                    if Path(file_path).match(glob_pattern):
                        if should_include_file(full_path, language, language_extensions):
                            files_to_process.add(full_path)
            finally:
                os.chdir(original_cwd)
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: Not a git repository or git is not installed.", file=sys.stderr)
            sys.exit(1)
    else:
        for path_str in paths:
            path = Path(path_str).resolve()
            if path.is_dir():
                for file_path in path.rglob(glob_pattern):
                    if file_path.is_file():
                        if should_include_file(file_path, language, language_extensions):
                            files_to_process.add(file_path)
            elif path.is_file():
                if glob_pattern == "*" or path.match(glob_pattern):
                    if should_include_file(path, language, language_extensions):
                        files_to_process.add(path)
            else:
                print(f"Warning: Path '{path}' is not a valid file or directory. Skipping.", file=sys.stderr)

    return sorted(list(files_to_process))

# ────────────────────────────  Main Function  ────────────────────────────

def main():
    """Enhanced main function with v7 features."""
    # Use enhanced parser if available, fallback to standard or basic
    if HAS_ENHANCED_PARSER:
        parser = create_search_parser('Enhanced text replacement tool (v7) with ripgrep integration and block awareness')
    elif HAS_STANDARD_PARSER:
        parser = create_parser('search', 'Enhanced text replacement tool (v7) with ripgrep integration and block awareness')
    else:
        parser = argparse.ArgumentParser(
            description='Enhanced text replacement tool (v7) with ripgrep integration and block awareness',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
    
    # Core replacement arguments
    if not HAS_ENHANCED_PARSER:
        # Add basic arguments for non-enhanced parser
        parser.add_argument('old_text', help='Text to find (literal by default, regex with --regex flag)')
        parser.add_argument('new_text', help='Replacement text (literal, supports \\1 \\2 etc with --regex)')
        parser.add_argument('paths', nargs='*', help='File(s) or directory(ies) to modify (use - or omit for stdin)')
        
        # Location specification
        parser.add_argument('--file', help='Search in specific file')
        parser.add_argument('--scope', default='.', help='Directory scope for search (default: current dir)')
        
        # Search options
        parser.add_argument('--type', choices=['text', 'regex', 'word', 'fixed'],
                           default='text', help='Search type')
        parser.add_argument('-i', '--ignore-case', action='store_true',
                           help='Case-insensitive search')
        parser.add_argument('-w', '--whole-word', action='store_true',
                           help='Match whole words only')
        parser.add_argument('--include', '--glob', '-g', dest='glob',
                           help='Include files matching pattern (e.g., "*.java")')
        parser.add_argument('--exclude', help='Exclude files matching pattern')
        
        # Context options
        parser.add_argument('-A', '--after-context', type=int, metavar='N',
                           help='Show N lines after match')
        parser.add_argument('-B', '--before-context', type=int, metavar='N',
                           help='Show N lines before match')
        parser.add_argument('-C', '--context', type=int, metavar='N',
                           help='Show N lines around match')
        
        # Common args
        parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
        parser.add_argument('-q', '--quiet', action='store_true', help='Minimal output')
        parser.add_argument('--json', action='store_true', help='Output in JSON format')
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    else:
        # Enhanced parser handles most arguments automatically
        parser.add_argument('old_text', help='Text to find')
        parser.add_argument('new_text', help='Replacement text')
        parser.add_argument('paths', nargs='*', help='File(s) or directory(ies) to modify')
    
    # V7 NEW FEATURES
    v7_group = parser.add_argument_group('V7 Enhanced Features')
    v7_group.add_argument('--from-find-json', metavar='JSON_INPUT',
                         help='Use JSON output from find_text as input (file path, - for stdin, or JSON string)')
    v7_group.add_argument('--block-mode', choices=['preserve', 'within', 'extract'],
                         default='preserve', help='Block-aware replacement mode (NEW IN V7)')
    # Note: --ast-context is provided by enhanced_standard_arg_parser when available
    if not HAS_ENHANCED_PARSER:
        v7_group.add_argument('--ast-context', action='store_true',
                             help='Show AST context (class/method hierarchy) in diff output (NEW IN V7)')
    v7_group.add_argument('--use-ripgrep', action='store_true', default=True,
                         help='Use ripgrep for file discovery and searching (default: enabled)')
    v7_group.add_argument('--no-ripgrep', action='store_true',
                         help='Disable ripgrep integration, use legacy methods')
    
    # Replacement strategies
    strategy_group = parser.add_mutually_exclusive_group()
    
    # Only add these if enhanced parser is not available (to avoid conflicts)
    if not HAS_ENHANCED_PARSER:
        strategy_group.add_argument('--regex', action='store_true', 
                           help='Treat old_text as regex pattern (enables capture groups, special chars)')
        strategy_group.add_argument('--whole-word', action='store_true', 
                           help='Match whole words only (prevents price→priceInTicks issues)')
    
    # These are unique to replace_text and safe to add
    strategy_group.add_argument('--comments-only', action='store_true', 
                       help='Replace only in comments (language-aware: supports Python #, Ruby, SQL --, etc.)')
    strategy_group.add_argument('--strings-only', action='store_true', 
                       help='Replace only in string literals (language-aware: handles single/double/triple quotes)')
    
    # Project and filtering options
    project_group = parser.add_argument_group('Project and Filtering Options')
    if not HAS_ENHANCED_PARSER:
        project_group.add_argument('-g', '--glob', default='*', 
                           help='Glob pattern to filter files when processing directories (default: *)')
    project_group.add_argument('--git-only', action='store_true', 
                       help='Only process files tracked by Git')
    project_group.add_argument('--staged-only', action='store_true', 
                       help='Only process files staged in Git')
    project_group.add_argument('--lang', '--language', dest='language',
                       choices=['python', 'java', 'javascript', 'typescript', 'cpp', 'c', 'go', 'rust', 'ruby', 'php', 'sql', 'lua'],
                       help='Process only files of specified language (also affects comment/string detection)')
    
    # Additional options
    parser.add_argument('--count', type=int, default=-1, help='Number of replacements to make (-1 for all)')
    parser.add_argument('--start-line', type=int, help='Start line for replacements (1-based)')
    parser.add_argument('--end-line', type=int, help='End line for replacements (1-based)')
    
    # Only add case-insensitive if enhanced parser doesn't provide it
    if not HAS_ENHANCED_PARSER:
        parser.add_argument('--case-insensitive', '-i', action='store_true', help='Case-insensitive matching (regex only)')
    
    parser.add_argument('--multiline', '-m', action='store_true', help='Multiline mode for regex')
    parser.add_argument('--dotall', '-s', action='store_true', help='Dot matches newline in regex')
    
    # Output options
    parser.add_argument('--backup', action='store_true', help='Create backup before modifying')
    parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation prompt for large changes')
    
    # Non-interactive options
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm all operations (for automation)')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Non-interactive mode - fail on any prompt')
    
    # File locking and retry options
    parser.add_argument('--max-retries', type=int, default=3, metavar='N',
                       help='Maximum retries if file is locked during write (default: 3, set to 0 to disable)')
    parser.add_argument('--retry-delay', type=float, default=1.0, metavar='SECONDS',
                       help='Delay between retries in seconds (default: 1.0)')
    parser.add_argument('--no-retry', action='store_true',
                       help='Disable all retry logic (equivalent to --max-retries=0)')
    parser.add_argument('--check-compile', action='store_true', default=True,
                       help='Check syntax/compilation after successful edits (default: enabled)')
    parser.add_argument('--no-check-compile', action='store_true',
                       help='Disable compile checking')
    
    # Parse arguments with enhanced error messages for common mistakes
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # Check if the error was due to unrecognized arguments
        import sys
        if e.code == 2:  # argparse exits with code 2 for argument errors
            # Check common mistakes in sys.argv
            argv_str = ' '.join(sys.argv[1:])
            suggestions = []
            
            if '--replace-all' in argv_str:
                suggestions.append("Did you mean '-r' or '--recursive' instead of '--replace-all'?")
            if '--all' in argv_str:
                suggestions.append("Did you mean '-r' or '--recursive' instead of '--all'?")
            if '--global' in argv_str:
                suggestions.append("Did you mean '-r' or '--recursive' instead of '--global'?")
            if '--regex' in argv_str and '--type' not in argv_str:
                suggestions.append("Did you mean '--type regex' instead of '--regex'?")
            
            if suggestions:
                print("\nCommon flag suggestions:", file=sys.stderr)
                for suggestion in suggestions:
                    print(f"  • {suggestion}", file=sys.stderr)
                print(f"\nFor help: {sys.argv[0]} --help", file=sys.stderr)
        
        raise  # Re-raise the SystemExit
    
    # Fix argument parsing for enhanced parser (which expects pattern, old_text, new_text, paths)
    if HAS_ENHANCED_PARSER and hasattr(args, 'pattern'):
        # Enhanced parser format: pattern old_text new_text [paths...]
        # We need to shift: pattern -> old_text, old_text -> new_text, new_text -> first path
        
        # Only shift if we have the expected arguments and not using JSON pipeline
        if not getattr(args, 'from_find_json', None):
            temp_old = args.pattern
            temp_new = args.old_text
            temp_paths = [args.new_text] + (args.paths if args.paths else [])
            
            args.old_text = temp_old
            args.new_text = temp_new
            args.paths = temp_paths
        else:
            # For JSON pipeline, arguments are already correct since enhanced parser doesn't support it yet
            pass
    
    # Handle compile check flags
    if args.no_check_compile:
        args.check_compile = False
    
    # Handle ripgrep settings
    if args.no_ripgrep:
        args.use_ripgrep = False
    
    # Apply configuration defaults
    apply_config_to_args('replace_text_v7', args, parser)
    
    # Handle non-interactive mode from environment
    if os.getenv('REPLACE_TEXT_NONINTERACTIVE') == '1':
        args.non_interactive = True
    if os.getenv('REPLACE_TEXT_ASSUME_YES') == '1':
        args.yes = True
    
    # V7 FEATURE: Handle JSON pipeline input
    target_matches = []
    search_pattern = None
    files_to_process = []
    
    if args.from_find_json:
        if not HAS_JSON_PIPELINE:
            print("Error: JSON pipeline support not available. Install required modules.", file=sys.stderr)
            sys.exit(1)
        
        try:
            search_pattern, search_type, target_matches = process_json_pipeline_input(args.from_find_json)
            
            # Extract unique files from matches
            files_to_process = list(set(match['file_path'] for match in target_matches))
            
            print(f"📄 Loaded {len(target_matches)} matches from find_text results")
            print(f"🎯 Targeting {len(files_to_process)} files")
            
            if not args.quiet:
                print_search_results_summary(load_search_results_from_file(args.from_find_json) 
                                            if os.path.isfile(args.from_find_json) else None)
        
        except Exception as e:
            print(f"Error processing JSON pipeline input: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Standard file processing
        stdin_mode = False
        if not args.paths or (len(args.paths) == 1 and args.paths[0] == '-'):
            stdin_mode = True
            files_to_process = ['<stdin>']
        else:
            if args.staged_only:
                args.git_only = True
            
            # V7 FEATURE: Enhanced file discovery with ripgrep
            if args.use_ripgrep and HAS_RIPGREP_INTEGRATION:
                try:
                    search_args = {
                        'paths': args.paths,
                        'glob_patterns': [args.glob] if hasattr(args, 'glob') and args.glob else None,
                        'exclude_patterns': [args.exclude] if hasattr(args, 'exclude') and args.exclude else None,
                        'language': args.language,
                        'git_only': args.git_only,
                        'staged_only': args.staged_only
                    }
                    files_to_process = find_files_for_replacement(search_args)
                except Exception as e:
                    LOG.warning(f"Enhanced file discovery failed: {e}, using legacy method")
                    files_to_process = get_files_to_process_legacy(args.paths, args.glob, args.git_only, args.staged_only, args.language)
            else:
                files_to_process = get_files_to_process_legacy(args.paths, args.glob, args.git_only, args.staged_only, args.language)
        
        if not files_to_process and not stdin_mode:
            print("No files found to process.")
            return 0
    
    total_replacements_all_files = 0
    files_modified = 0
    files_to_modify = []
    
    # Process each file
    for filepath in files_to_process:
        if filepath == '<stdin>':
            # Handle stdin
            try:
                original_content = sys.stdin.read()
                filepath = '<stdin>'
            except Exception as e:
                print(f"Error reading from stdin: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            filepath = Path(filepath)
            
            # Skip large files
            try:
                file_size = filepath.stat().st_size
                if file_size > 1024 * 1024 * 1024:
                    print(f"Skipping {filepath}: File too large ({file_size / 1024 / 1024:.1f}MB)", file=sys.stderr)
                    continue
                elif file_size > 100 * 1024 * 1024 and not args.quiet:
                    print(f"Warning: Large file {filepath} ({file_size / 1024 / 1024:.1f}MB)")
            except OSError:
                print(f"Warning: Cannot access {filepath}", file=sys.stderr)
                continue
            
            if not args.quiet and len(files_to_process) > 1:
                print(f"{filepath}", end="... ")
            
            original_content = read_file(filepath)
        
        modified_content = original_content
        replacements_made = 0
        
        # V7 FEATURE: Block-aware replacement
        if args.block_mode != 'preserve' and target_matches:
            # Get target lines for this file from matches
            file_matches = [m for m in target_matches if m['file_path'] == str(filepath)]
            target_lines = [m['line_number'] for m in file_matches]
            
            if target_lines:
                # V7 FEATURE: Add AST context to matches
                if args.ast_context:
                    file_matches = add_ast_context_to_replacements(str(filepath), file_matches)
                
                modified_content, replacements_made = apply_block_aware_replacement(
                    str(filepath), original_content, args.old_text, args.new_text,
                    args.block_mode, target_lines
                )
            else:
                # No matches for this file, skip
                continue
        else:
            # Standard replacement strategies
            # Use getattr for safe attribute access (enhanced parser might not have all attributes)
            if getattr(args, 'comments_only', False):
                modified_content, replacements_made = replace_in_comments(original_content, args.old_text, args.new_text, getattr(args, 'language', None))
            elif getattr(args, 'strings_only', False):
                modified_content, replacements_made = replace_in_strings(original_content, args.old_text, args.new_text, getattr(args, 'language', None))
            elif getattr(args, 'whole_word', False):
                modified_content, replacements_made = replace_whole_word(original_content, args.old_text, args.new_text)
            elif getattr(args, 'regex', False) or getattr(args, 'type', 'text') == 'regex':
                flags = 0
                if getattr(args, 'case_insensitive', False) or getattr(args, 'ignore_case', False):
                    flags |= re.IGNORECASE
                if getattr(args, 'multiline', False):
                    flags |= re.MULTILINE
                if getattr(args, 'dotall', False):
                    flags |= re.DOTALL
                modified_content, replacements_made = replace_regex(original_content, args.old_text, args.new_text, 
                                               flags=flags, count=getattr(args, 'count', -1) if getattr(args, 'count', -1) != -1 else 0)
            elif getattr(args, 'start_line', None) or getattr(args, 'end_line', None):
                modified_content, replacements_made = replace_in_range(original_content, args.old_text, args.new_text,
                                                  getattr(args, 'start_line', None), getattr(args, 'end_line', None))
            else:
                # Default exact text replacement
                modified_content, replacements_made = replace_exact(original_content, args.old_text, args.new_text, getattr(args, 'count', -1))
        
        total_replacements_all_files += replacements_made
        
        # Check if there are any changes
        if original_content == modified_content:
            if not args.quiet and args.verbose:
                print(f"No changes in {filepath}")
            continue
        
        files_modified += 1
        files_to_modify.append((filepath, original_content, modified_content, replacements_made))
        
        # V7 FEATURE: Enhanced diff display with AST context
        if not args.quiet and not (filepath == '<stdin>' and not args.dry_run):
            has_changes = show_diff(original_content, modified_content, filepath, args.ast_context)
            if not args.verbose and len(files_to_process) > 1:
                print(f"Replacements in this file: {replacements_made}")
    
    # Show summary and get confirmation
    if not args.quiet and not (filepath == '<stdin>' and not args.dry_run):
        print("\n" + "=" * 60)
        if files_modified == 0:
            print("No files need to be modified.")
            return 0
        
        if args.dry_run:
            print(f"DRY RUN SUMMARY:")
            if filepath == '<stdin>':
                print(f"Would make {total_replacements_all_files} replacement(s) in stdin input")
            else:
                print(f"Would modify {files_modified} file(s) with {total_replacements_all_files} total replacement(s)")
        else:
            print(f"SUMMARY:")
            print(f"Will modify {files_modified} file(s) with {total_replacements_all_files} total replacement(s)")
    
    # Confirmation for large changes
    if not args.dry_run and not args.force and total_replacements_all_files > 50 and filepath != '<stdin>':
        if not args.quiet:
            try:
                print(f"\nThis will make {total_replacements_all_files} replacements across {files_modified} files:")
                print("\nFiles to be modified:")
                for filepath, _, _, replacements in files_to_modify[:10]:
                    print(f"  - {filepath} ({replacements} replacement{'s' if replacements != 1 else ''})")
                if len(files_to_modify) > 10:
                    print(f"  ... and {len(files_to_modify) - 10} more files")
                
                # Check for non-interactive mode
                if args.non_interactive:
                    if args.yes or args.force:
                        print("\n[AUTO-CONFIRM] Continue? [y/N] y")
                        response = 'y'
                    else:
                        print("\n❌ ERROR: Large change confirmation required in non-interactive mode")
                        print("   Use --yes or --force to auto-confirm")
                        return 1
                elif args.yes:
                    print("\n[AUTO-CONFIRM] Continue? [y/N] y")
                    response = 'y'
                else:
                    response = input("\nContinue? [y/N] ")
                
                if response.lower() != 'y':
                    print("Operation cancelled.")
                    return 0
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                return 0
    
    # Apply changes if not dry run
    if not args.dry_run:
        if filepath == '<stdin>':
            # For stdin mode, output to stdout
            if files_to_modify:
                _, _, modified_content, _ = files_to_modify[0]
                sys.stdout.write(modified_content)
        else:
            for filepath, original_content, modified_content, replacements_made in files_to_modify:
                # Write modified content with atomic operation
                try:
                    max_retries = int(os.getenv('FILE_WRITE_MAX_RETRIES', '3'))
                    retry_delay = float(os.getenv('FILE_WRITE_RETRY_DELAY', '1.0'))
                    _atomic_write(Path(filepath), modified_content, bak=args.backup, 
                                  max_retries=max_retries, retry_delay=retry_delay)
                    
                    # Verify changes
                    verification_content = read_file(filepath)
                    
                    if verification_content == modified_content:
                        if len(files_to_process) == 1:
                            success_msg = f"✓ Successfully replaced {replacements_made} occurrence{'s' if replacements_made != 1 else ''} in {filepath}"
                        else:
                            success_msg = f"✓ Successfully replaced {replacements_made} occurrence{'s' if replacements_made != 1 else ''} in {Path(filepath).name}"
                        
                        # Check compilation if requested
                        if args.check_compile:
                            try:
                                compile_success, compile_msg = check_compile_status(filepath, args.language)
                                compile_status = f"✓ {compile_msg}" if compile_success else f"✗ {compile_msg}"
                                success_msg += f"\n{compile_status}"
                            except Exception as e:
                                success_msg += f"\n✗ Compile check failed: {str(e)[:50]}"
                        
                        if not args.quiet:
                            print(success_msg)
                    else:
                        print(f"WARNING: {filepath} - verification failed", file=sys.stderr)
                except Exception as e:
                    error_msg = f"\nError writing {filepath}: {e}"
                    
                    is_locked, lock_info = is_file_locked(filepath)
                    if is_locked:
                        error_msg += f"\nFile appears to be {lock_info}"
                        error_msg += "\nTry closing any programs that might have this file open."
                    
                    print(error_msg, file=sys.stderr)
    else:
        if not args.quiet:
            print("\nDry run - no changes applied")
            print("Use without --dry-run to apply changes.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        sys.exit(1)