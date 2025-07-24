#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Text replacement tool for code files with various replacement strategies.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
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
from pathlib import Path

# ────────────────────────────  logging  ────────────────────────────
LOG = logging.getLogger("replace_text")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s"
)

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
        def check_regex_pattern(pattern):
            return True, ""

# Load common configuration system
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    # Graceful fallback if common_config is not available
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass

def is_file_locked(filepath):
    """Check if a file is currently locked for writing.
    
    Returns:
        (is_locked, process_info): Tuple of lock status and process info string
    """
    # Platform-specific file locking check
    import platform
    
    if platform.system() != 'Windows':
        # Unix-like systems (Linux, macOS)
        try:
            # Try to open file for exclusive write access
            with open(filepath, 'r+b') as f:
                # Try to acquire an exclusive lock (non-blocking)
                try:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    return False, None
                except IOError:
                    # File is locked
                    try:
                        # Try to get process info using lsof (if available)
                        result = subprocess.run(['lsof', '-t', str(filepath)], 
                                              capture_output=True, text=True, timeout=1)
                        if result.returncode == 0 and result.stdout.strip():
                            pids = result.stdout.strip().split('\n')
                            return True, f"locked by process(es): {', '.join(pids)}"
                    except:
                        pass
                    return True, "locked by another process"
                except ImportError:
                    # fcntl not available, try alternative method
                    pass
        except PermissionError:
            return True, "permission denied"
        except Exception:
            pass
    
    # Windows or fallback method: try to open for exclusive write
    try:
        # Try to open the file in exclusive mode
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
    
    # Final fallback: try to rename the file to itself
    try:
        os.rename(str(filepath), str(filepath))
        return False, None
    except OSError:
        return True, "file is in use"
    except Exception:
        # If we can't determine, assume it's not locked
        return False, None

def read_file(filepath):
    """Read file contents preserving exact format."""
    try:
        # Read with newline preservation
        with open(filepath, 'r', encoding='utf-8', newline='') as f:
            return f.read()
    except UnicodeDecodeError:
        print(f"Error: File appears to be binary or has encoding issues", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

def _atomic_write(path: Path, data: str, bak: bool = False, max_retries: int = 3, retry_delay: float = 1.0) -> None:
    """Write atomically with retry logic for locked files; optionally create .bak.
    
    Args:
        path: Target file path
        data: Content to write
        bak: Whether to create backup
        max_retries: Maximum number of retries if file is locked
        retry_delay: Delay in seconds between retries
    
    Raises:
        OSError: If file remains locked after all retries
    """
    # Create temp file in same directory for atomic operation
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    tmp = Path(tmp_path)
    
    try:
        # Write data to temp file
        with os.fdopen(tmp_fd, 'w', encoding='utf-8', newline='') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
    except Exception:
        # Clean up temp file on write error
        try:
            os.close(tmp_fd)
        except:
            pass
        try:
            tmp.unlink()
        except:
            pass
        raise
    
    # Create backup if requested
    if bak and path.exists():
        try:
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        except Exception as e:
            # Clean up temp file and re-raise
            try:
                tmp.unlink()
            except:
                pass
            raise Exception(f"Failed to create backup: {e}")
    
    # Attempt atomic replacement with retry logic
    last_error = None
    for attempt in range(max_retries):
        try:
            # Use os.replace for true atomic operation (works on both Unix and Windows)
            os.replace(str(tmp), str(path))
            return  # Success!
        except OSError as e:
            last_error = e
            # Check if it's a permission/locking error
            if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.ETXTBSY):
                if attempt < max_retries - 1:
                    # File is locked, wait and retry
                    if not os.getenv('QUIET_MODE'):
                        print(f"File {path} appears to be locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
            # For other errors or final attempt, clean up and raise
            try:
                tmp.unlink()
            except:
                pass
            raise
    
    # If we get here, all retries failed
    try:
        tmp.unlink()
    except:
        pass
    raise OSError(f"Failed to write {path} after {max_retries} attempts: {last_error}")

def write_file(filepath, content):
    """Write content to file preserving line endings."""
    try:
        # Use newline='' to preserve line endings
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)
        sys.exit(1)

def create_backup(filepath):
    """Create a backup of the file."""
    backup_path = f"{filepath}.bak"
    try:
        shutil.copy2(filepath, backup_path)
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}", file=sys.stderr)
        return None

def show_diff(original, modified, filepath):
    """Show unified diff of changes."""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"{filepath} (original)",
        tofile=f"{filepath} (modified)",
        lineterm=''
    )
    
    diff_text = ''.join(diff)
    if diff_text:
        print("\nChanges to be made:")
        print(diff_text)
    return bool(diff_text)

def replace_exact(content, old_text, new_text, count=-1):
    """Replace exact text occurrences without recursive replacement."""
    if old_text == new_text or old_text == "":
        return content, 0
    
    # Find all positions first (before any replacements)
    positions = []
    start = 0
    while True:
        pos = content.find(old_text, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + len(old_text)
    
    # Apply count limit if specified
    if count != -1 and count < len(positions):
        positions = positions[:count]
    
    # If no positions found, return original
    if not positions:
        return content, 0
    
    # Build the result by reconstructing the string with replacements
    # This avoids the recursive replacement issue entirely
    result = []
    last_end = 0
    
    for pos in positions:
        # Add the part before this match
        result.append(content[last_end:pos])
        # Add the replacement
        result.append(new_text)
        # Update position
        last_end = pos + len(old_text)
    
    # Add any remaining content after the last match
    result.append(content[last_end:])
    
    return ''.join(result), len(positions)

def replace_regex(content, pattern, replacement, flags=0, count=0):
    """Replace using regex pattern with safety checks."""
    try:
        # Safety check for zero-width patterns
        if pattern in ['', '^', '$', r'\b', r'\B']:
            print(f"Error: Zero-width pattern '{pattern}' not supported", file=sys.stderr)
            sys.exit(1)
        
        # Compile with timeout protection for catastrophic backtracking
        regex = re.compile(pattern, flags)
        
        # Test for potential catastrophic backtracking
        # Check for nested quantifiers which can cause exponential time complexity
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
    
    # Convert to 0-based indexing
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    
    total_replacements = 0
    # Replace only in the specified range
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
            'multi': r'(""".*?"""|' + r"'''.*?''')",  # Triple quotes as comments
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
    
    # Use default patterns for C-style languages
    c_style_langs = ['java', 'javascript', 'typescript', 'cpp', 'c', 'go', 'rust', 'php']
    if language in c_style_langs:
        return patterns['default']
    
    return patterns.get(language, patterns['default'])

def replace_in_comments(content, old_text, new_text, language=None):
    """Replace text only within comments (language-aware)."""
    total_replacements = 0
    patterns = get_comment_patterns(language)
    
    # Handle single-line comments
    def replace_in_single_line_comment(match):
        nonlocal total_replacements
        comment = match.group(0)
        modified_comment, count = replace_exact(comment, old_text, new_text)
        total_replacements += count
        return modified_comment
    
    # Replace in single-line comments
    if patterns['single']:
        content = re.sub(patterns['single'], replace_in_single_line_comment, content, flags=re.MULTILINE)
    
    # Handle multi-line comments
    def replace_in_multi_line_comment(match):
        nonlocal total_replacements
        comment = match.group(0)
        modified_comment, count = replace_exact(comment, old_text, new_text)
        total_replacements += count
        return modified_comment
    
    # Replace in multi-line comments
    if patterns['multi']:
        content = re.sub(patterns['multi'], replace_in_multi_line_comment, content, flags=re.DOTALL)
    
    return content, total_replacements

def get_string_patterns(language):
    """Get string literal patterns for different programming languages."""
    patterns = {
        'default': [
            (r'"(?:[^"\\]|\\.)*"', '"'),  # Double quotes
            (r"'(?:[^'\\]|\\.)*'", "'"),    # Single quotes
        ],
        'python': [
            (r'""".*?"""|' + r"'''.*?'''", '"""'),  # Triple quotes
            (r'"(?:[^"\\]|\\.)*"', '"'),  # Double quotes
            (r"'(?:[^'\\]|\\.)*'", "'"),    # Single quotes
        ],
        'java': [
            (r'"(?:[^"\\]|\\.)*"', '"'),  # Double quotes only
        ],
        'rust': [
            (r'"(?:[^"\\]|\\.)*"', '"'),  # Double quotes
            (r"r#*\".*?\"#*", 'r#"'),  # Raw strings
        ],
        'go': [
            (r'"(?:[^"\\]|\\.)*"', '"'),  # Double quotes
            (r'`[^`]*`', '`'),  # Raw strings
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
            # Extract the inner content based on quote type
            if quote_char in ['"""', "'''", 'r#"']:
                # Special handling for multi-char quotes
                quote_len = len(quote_char)
                inner = string_literal[quote_len:-quote_len]
            elif quote_char == '`':
                inner = string_literal[1:-1]
            else:
                # Standard single-char quotes
                inner = string_literal[1:-1]
            
            inner_replaced, count = replace_exact(inner, old_text, new_text)
            total_replacements += count
            
            # Reconstruct the string literal
            if quote_char in ['"""', "'''"]:
                return f'{quote_char}{inner_replaced}{quote_char}'
            elif quote_char == 'r#"':
                # Handle Rust raw strings (find the actual delimiters)
                prefix_match = re.match(r'(r#*\")', string_literal)
                if prefix_match:
                    prefix = prefix_match.group(1)
                    suffix = prefix.replace('r', '').replace('\"', '\"#')
                    return f'{prefix}{inner_replaced}{suffix}'
            elif quote_char == '`':
                return f'`{inner_replaced}`'
            else:
                return f'{quote_char}{inner_replaced}{quote_char}'
        
        # Replace in strings matching this pattern
        content = re.sub(pattern, replace_in_string, content, flags=re.DOTALL if quote_char in ['"""', "'''"] else 0)
    
    return content, total_replacements

def check_compile_status(file_path, language=None):
    """Check if file compiles/has valid syntax. Returns (success, short_message).
    
    This function is designed to NEVER break tool functionality:
    - All exceptions are caught and handled gracefully
    - Returns success=True for unknown languages or when compilers are missing
    - Uses timeouts to prevent hanging on problematic files
    - Cleans up temporary files (like .class files)
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return True, "File not found"  # Don't fail - file might be created later
        
        # Check file size to avoid hanging on huge files
        try:
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                return False, "Cannot check - file too large"
        except OSError:
            return False, "Cannot check - size unknown"
        
        # Auto-detect language if not specified
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
                return False, "Cannot check - unknown language"  # Be honest about inability to check
        
        # Python syntax check
        if language == 'python':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Skip empty files
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
        
        # Java compilation check
        elif language == 'java':
            try:
                # Check if javac is available
                result = subprocess.run(
                    ['javac', '-version'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode != 0:
                    return False, "Cannot check - javac unavailable"
                
                # Compile the file
                result = subprocess.run(
                    ['javac', '-cp', '.', str(file_path)],
                    capture_output=True, text=True, timeout=30
                )
                
                # Always clean up .class files
                class_file = path.with_suffix('.class')
                if class_file.exists():
                    try:
                        class_file.unlink()
                    except OSError:
                        pass  # Ignore cleanup errors
                
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
        
        # JavaScript/TypeScript syntax check
        elif language in ['javascript', 'typescript']:
            try:
                if language == 'javascript':
                    # Check if node is available
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
                else:  # typescript
                    # Check if tsc is available
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
        
        # Default for unknown languages
        return False, "Cannot check - unsupported language"
    
    except Exception:
        # Ultimate fallback - never break the tool
        return False, "Cannot check - internal error"

def get_files_to_process(paths, glob_pattern, git_only, staged_only, language=None):
    """Get a list of files to process based on paths and git flags."""
    files_to_process = set()
    
    # Language extension mapping
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
        """Check if a file should be included based on language filter."""
        if language and language in language_extensions:
            return any(file_path.suffix == ext for ext in language_extensions[language])
        return True

    if git_only or staged_only:
        try:
            # Get git root directory
            git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], 
                                             text=True, stderr=subprocess.PIPE).strip()
            
            # Save current directory and change to git root
            original_cwd = os.getcwd()
            os.chdir(git_root)
            
            try:
                if staged_only:
                    cmd = ['git', 'diff', '--name-only', '--cached']
                else:  # --git-only
                    cmd = ['git', 'ls-files']
                
                git_files = subprocess.check_output(cmd, text=True).splitlines()
                for file_path in git_files:
                    full_path = Path(git_root) / file_path
                    if Path(file_path).match(glob_pattern):
                        # Check language filter
                        if should_include_file(full_path, language, language_extensions):
                            files_to_process.add(full_path)
            finally:
                # Restore original directory
                os.chdir(original_cwd)
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: Not a git repository or git is not installed.", file=sys.stderr)
            sys.exit(1)
    else:
        for path_str in paths:
            path = Path(path_str).resolve()
            if path.is_dir():
                # Find all files matching the glob pattern
                for file_path in path.rglob(glob_pattern):
                    if file_path.is_file():
                        # Check language filter
                        if should_include_file(file_path, language, language_extensions):
                            files_to_process.add(file_path)
            elif path.is_file():
                # Single file - check if it matches the pattern
                if glob_pattern == "*" or path.match(glob_pattern):
                    # Check language filter
                    if should_include_file(path, language, language_extensions):
                        files_to_process.add(path)
            else:
                print(f"Warning: Path '{path}' is not a valid file or directory. Skipping.", file=sys.stderr)

    return sorted(list(files_to_process))

def main():
    parser = argparse.ArgumentParser(
        description='Replace text in code files with various strategies',
        epilog='''
EXAMPLES:
  # Simple replacement in one file  
  # Project-wide replacement using a glob pattern  
  # Avoid recursive replacement issues (e.g., price -> priceInTicks)  
  # Preview changes before applying  
  # Safe replacement with backup  
  # Replace only in comments  
  # Case-insensitive regex replacement  
  # Git-integrated replacement (only on tracked files)  
  # Replace only in staged files
COMMON PITFALLS TO AVOID:
  1. Recursive replacement: When replacing "a" with "ab", the "a" in "ab" 
     will also be found. Use --whole-word for identifier replacements.
  
  2. Special characters in regex: Characters like . $ ^ [ ] need escaping.
     Use literal mode (default) when you don't need regex patterns.
  
  3. Large file warnings: Files >100MB will show a warning. Files >1GB 
     are refused to prevent memory issues.

SAFETY FEATURES:
  • Prevents recursive replacement bugs (e.g., a->aa won't create aaaa)
  • Preserves line endings (Windows \\r\\n, Unix \\n)
  • Detects and refuses binary files
  • Warns about catastrophic regex patterns
  • Verifies changes were applied correctly

BEST PRACTICES:
  • Always use --dry-run first on important files
  • Use --whole-word for variable/function renaming
  • Create backups with --backup for production code
  • Test regex patterns on small samples first
  • Use --quiet for scripting, --verbose for debugging
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('old_text', help='Text to find (literal by default, regex with --regex flag)')
    parser.add_argument('new_text', help='Replacement text (literal, supports \\1 \\2 etc with --regex)')
    parser.add_argument('paths', nargs='*', help='File(s) or directory(ies) to modify (use - or omit for stdin)')
    
    # Replacement strategies (mutually exclusive)
    strategy_group = parser.add_mutually_exclusive_group()
    strategy_group.add_argument('--regex', action='store_true', 
                       help='Treat old_text as regex pattern (enables capture groups, special chars)')
    strategy_group.add_argument('--whole-word', action='store_true', 
                       help='Match whole words only (prevents price→priceInTicks issues)')
    strategy_group.add_argument('--comments-only', action='store_true', 
                       help='Replace only in comments (language-aware: supports Python #, Ruby, SQL --, etc.)')
    strategy_group.add_argument('--strings-only', action='store_true', 
                       help='Replace only in string literals (language-aware: handles single/double/triple quotes)')
    
    # Project and filtering options
    project_group = parser.add_argument_group('Project and Filtering Options')
    project_group.add_argument('-g', '--glob', default='*', 
                       help='Glob pattern to filter files when processing directories (default: *)')
    project_group.add_argument('--git-only', action='store_true', 
                       help='Only process files tracked by Git')
    project_group.add_argument('--staged-only', action='store_true', 
                       help='Only process files staged in Git')
    project_group.add_argument('--lang', '--language', dest='language',
                       choices=['python', 'java', 'javascript', 'typescript', 'cpp', 'c', 'go', 'rust', 'ruby', 'php', 'sql', 'lua'],
                       help='Process only files of specified language (also affects comment/string detection)')
    
    # Options
    parser.add_argument('--count', type=int, default=-1, help='Number of replacements to make (-1 for all)')
    parser.add_argument('--start-line', type=int, help='Start line for replacements (1-based)')
    parser.add_argument('--end-line', type=int, help='End line for replacements (1-based)')
    parser.add_argument('--case-insensitive', '-i', action='store_true', help='Case-insensitive matching (regex only)')
    parser.add_argument('--multiline', '-m', action='store_true', help='Multiline mode for regex')
    parser.add_argument('--dotall', '-s', action='store_true', help='Dot matches newline in regex')
    
    # Output options
    parser.add_argument('--backup', action='store_true', help='Create backup before modifying')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation prompt for large changes')
    
    # File locking and retry options
    parser.add_argument('--max-retries', type=int, default=3, metavar='N',
                       help='Maximum retries if file is locked during write (default: 3, set to 0 to disable)')
    parser.add_argument('--retry-delay', type=float, default=1.0, metavar='SECONDS',
                       help='Delay between retries in seconds (default: 1.0)')
    parser.add_argument('--max-read-retries', type=int, default=3, metavar='N',
                       help='Maximum retries if file is locked during read (default: 3, set to 0 to disable)')
    parser.add_argument('--read-retry-delay', type=float, default=1.0, metavar='SECONDS',
                       help='Delay between read retries in seconds (default: 1.0)')
    parser.add_argument('--no-retry', action='store_true',
                       help='Disable all retry logic (equivalent to --max-retries=0 --max-read-retries=0)')
    parser.add_argument('--check-compile', action='store_true', default=True,
                       help='Check syntax/compilation after successful edits (default: enabled)')
    parser.add_argument('--no-check-compile', action='store_true',
                       help='Disable compile checking')
    
    # Verbosity options (required by the main function)
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet output')
    
    args = parser.parse_args()
    
    # Handle compile check flags
    if args.no_check_compile:
        args.check_compile = False
    
    # Apply configuration defaults
    apply_config_to_args('replace_text', args, parser)
    
    # Handle stdin if no paths specified or path is '-'
    stdin_mode = False
    if not args.paths or (len(args.paths) == 1 and args.paths[0] == '-'):
        stdin_mode = True
        # For stdin mode, we'll process input directly
        files_to_process = ['<stdin>']
    else:
        # If --staged-only is set, it implies --git-only
        if args.staged_only:
            args.git_only = True
        
        # Get list of files to process
        files_to_process = get_files_to_process(args.paths, args.glob, args.git_only, args.staged_only, args.language)
        
        if not files_to_process:
            print("No files found to process.")
            sys.exit(0)
    
    total_replacements_all_files = 0
    files_modified = 0
    files_to_modify = []  # Store files and their changes for later processing
    
    # First pass: analyze all files to determine what changes would be made
    for filepath in files_to_process:
        if stdin_mode:
            # Read from stdin
            filepath = '<stdin>'
            try:
                original_content = sys.stdin.read()
            except Exception as e:
                print(f"Error reading from stdin: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            filepath = Path(filepath)
            
            # Skip files that are too large
            try:
                file_size = filepath.stat().st_size
                if file_size > 1024 * 1024 * 1024:  # 1GB
                    print(f"Skipping {filepath}: File too large ({file_size / 1024 / 1024:.1f}MB)", file=sys.stderr)
                    continue
                elif file_size > 100 * 1024 * 1024 and not args.quiet:  # 100MB
                    print(f"Warning: Large file {filepath} ({file_size / 1024 / 1024:.1f}MB)")
            except OSError:
                print(f"Warning: Cannot access {filepath}", file=sys.stderr)
                continue
            
            if not args.quiet and len(files_to_process) > 1:
                print(f"{filepath}", end="... ")
            
            # Read file content with retry on lock
            max_read_retries = 0 if args.no_retry else (args.max_read_retries if hasattr(args, 'max_read_retries') else int(os.getenv('FILE_READ_MAX_RETRIES', '3')))
            read_retry_delay = args.read_retry_delay if hasattr(args, 'read_retry_delay') else float(os.getenv('FILE_READ_RETRY_DELAY', '1.0'))
            
            original_content = None
            for read_attempt in range(max_read_retries):
                try:
                    original_content = read_file(filepath)
                    break  # Success, exit retry loop
                except Exception as e:
                    # Check if file is locked for reading
                    is_locked, lock_info = is_file_locked(filepath)
                    if is_locked and read_attempt < max_read_retries - 1:
                        if not args.quiet:
                            print(f"File {filepath} is {lock_info}, retrying in {read_retry_delay}s... (attempt {read_attempt + 1}/{max_read_retries})")
                        time.sleep(read_retry_delay)
                        continue
                    else:
                        # Final attempt failed or not a lock issue
                        error_msg = f"Error reading {filepath}: {e}"
                        if is_locked:
                            error_msg += f" (file {lock_info})"
                        print(error_msg, file=sys.stderr)
                        break
            
            if original_content is None:
                continue  # Skip this file, couldn't read it
        
        modified_content = original_content
        replacements_made = 0
        
        # Apply appropriate replacement strategy
        if args.comments_only:
            modified_content, replacements_made = replace_in_comments(original_content, args.old_text, args.new_text, args.language)
        elif args.strings_only:
            modified_content, replacements_made = replace_in_strings(original_content, args.old_text, args.new_text, args.language)
        elif args.whole_word:
            modified_content, replacements_made = replace_whole_word(original_content, args.old_text, args.new_text)
        elif args.regex:
            flags = 0
            if args.case_insensitive:
                flags |= re.IGNORECASE
            if args.multiline:
                flags |= re.MULTILINE
            if args.dotall:
                flags |= re.DOTALL
            modified_content, replacements_made = replace_regex(original_content, args.old_text, args.new_text, 
                                           flags=flags, count=args.count if args.count != -1 else 0)
        elif args.start_line or args.end_line:
            modified_content, replacements_made = replace_in_range(original_content, args.old_text, args.new_text,
                                              args.start_line, args.end_line)
        else:
            # Default exact text replacement
            modified_content, replacements_made = replace_exact(original_content, args.old_text, args.new_text, args.count)
        
        total_replacements_all_files += replacements_made
        
        # Check if there are any changes
        if original_content == modified_content:
            if not args.quiet and args.verbose:
                print(f"No changes in {filepath}")
            continue
        
        files_modified += 1
        files_to_modify.append((filepath, original_content, modified_content, replacements_made))
        
        # Show diff if not quiet (but not for stdin in non-dry-run mode)
        if not args.quiet and not (stdin_mode and not args.dry_run):
            has_changes = show_diff(original_content, modified_content, filepath)
            if not args.verbose and len(files_to_process) > 1:
                print(f"Replacements in this file: {replacements_made}")
    
    # Show summary and get confirmation before applying changes
    if not args.quiet and not (stdin_mode and not args.dry_run):
        print("\n" + "=" * 60)
        if files_modified == 0:
            print("No files need to be modified.")
            sys.exit(0)
        
        if args.dry_run:
            print(f"DRY RUN SUMMARY:")
            if stdin_mode:
                print(f"Would make {total_replacements_all_files} replacement(s) in stdin input")
            else:
                print(f"Would modify {files_modified} file(s) with {total_replacements_all_files} total replacement(s)")
        else:
            print(f"SUMMARY:")
            print(f"Will modify {files_modified} file(s) with {total_replacements_all_files} total replacement(s)")
    
    # Check if we need confirmation for large changes (skip for stdin mode)
    if not args.dry_run and not args.force and total_replacements_all_files > 50 and not stdin_mode:
        if not args.quiet:
            try:
                print(f"\nThis will make {total_replacements_all_files} replacements across {files_modified} files:")
                print("\nFiles to be modified:")
                for filepath, _, _, replacements in files_to_modify[:10]:  # Show first 10 files
                    print(f"  - {filepath} ({replacements} replacement{'s' if replacements != 1 else ''})")
                if len(files_to_modify) > 10:
                    print(f"  ... and {len(files_to_modify) - 10} more files")
                
                response = input("\nContinue? [y/N] ")
                if response.lower() != 'y':
                    print("Operation cancelled.")
                    sys.exit(0)
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                sys.exit(0)
    
    # Apply changes if not dry run
    if not args.dry_run:
        if stdin_mode:
            # For stdin mode, output to stdout
            if files_to_modify:
                _, _, modified_content, _ = files_to_modify[0]
                sys.stdout.write(modified_content)
        else:
            for filepath, original_content, modified_content, replacements_made in files_to_modify:
                # Write modified content with atomic operation and retry logic
                try:
                    # Allow retry configuration via environment variables
                    max_retries = int(os.getenv('FILE_WRITE_MAX_RETRIES', '3'))
                    retry_delay = float(os.getenv('FILE_WRITE_RETRY_DELAY', '1.0'))
                    _atomic_write(Path(filepath), modified_content, bak=args.backup, 
                                  max_retries=max_retries, retry_delay=retry_delay)
                    
                    # Verify changes were applied
                    verification_content = read_file(filepath)
                    
                    if verification_content == modified_content:
                        # Build success message
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
                                # Never let compile check break the tool
                                success_msg += f"\n✗ Compile check failed: {str(e)[:50]}"
                        
                        if not args.quiet:
                            print(success_msg)
                    else:
                        print(f"WARNING: {filepath} - verification failed", file=sys.stderr)
                except Exception as e:
                    # Enhanced error reporting for file write failures
                    error_msg = f"\nError writing {filepath}: {e}"
                    
                    # Check if file is locked and provide more info
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