#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Robust ripgrep integration module extracted from find_text_v6.py.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import re
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

def find_ripgrep():
    """Find ripgrep executable with fallback options."""
    # Try common ripgrep executable names
    rg_names = ['rg', 'ripgrep']
    
    for name in rg_names:
        rg_path = shutil.which(name)
        if rg_path:
            return rg_path
    
    # Check common installation paths
    common_paths = [
        '/usr/local/bin/rg',
        '/opt/homebrew/bin/rg',
        '/usr/bin/rg',
        os.path.expanduser('~/.cargo/bin/rg'),
        os.path.expanduser('~/bin/rg')
    ]
    
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    return None

def build_ripgrep_command(pattern: str, search_paths: List[str], 
                         context_before: int = 0, context_after: int = 0,
                         case_insensitive: bool = False, whole_word: bool = False,
                         search_type: str = 'text', glob_patterns: List[str] = None,
                         exclude_patterns: List[str] = None, recursive: bool = True,
                         max_count: Optional[int] = None) -> List[str]:
    """
    Build robust ripgrep command with explicit flags and safe pattern handling.
    
    Args:
        pattern: Search pattern
        search_paths: List of paths to search
        context_before: Lines of context before matches
        context_after: Lines of context after matches  
        case_insensitive: Case-insensitive search
        whole_word: Match whole words only
        search_type: 'text', 'regex', 'word', or 'fixed'
        glob_patterns: Include file patterns (e.g., ['*.java', '*.py'])
        exclude_patterns: Exclude file patterns
        recursive: Search recursively
        max_count: Maximum number of matches per file
        
    Returns:
        Complete ripgrep command as list of strings
    """
    rg_path = find_ripgrep()
    if not rg_path:
        raise FileNotFoundError("ripgrep (rg) not found. Please install ripgrep.")
    
    # Start with base command and explicit flags for deterministic output
    cmd = [
        rg_path,
        "--line-number",
        "--with-filename", 
        "--color=never",  # Explicit for deterministic output
    ]
    
    # Add context flags
    if context_before > 0:
        cmd.extend(["-B", str(context_before)])
    if context_after > 0:
        cmd.extend(["-A", str(context_after)])
    
    # Add search type flags
    if search_type == 'fixed' or search_type == 'text':
        cmd.append("--fixed-strings")
    elif search_type == 'word':
        cmd.append("--word-regexp")
    # regex is default, no flag needed
    
    # Add case sensitivity
    if case_insensitive:
        cmd.append("--ignore-case")
    
    # Add whole word matching
    if whole_word:
        cmd.append("--word-regexp")
    
    # Add recursion control
    if not recursive:
        cmd.append("--max-depth=1")
    
    # Add max count per file
    if max_count:
        cmd.extend(["--max-count", str(max_count)])
    
    # Add include patterns (glob patterns)
    if glob_patterns:
        for pattern_str in glob_patterns:
            cmd.extend(["--glob", pattern_str])
    
    # Add exclude patterns
    if exclude_patterns:
        for exclude in exclude_patterns:
            cmd.extend(["--glob", f"!{exclude}"])
    
    # Safe pattern handling with -e flag
    cmd.extend(["-e", pattern])
    
    # Add separator to prevent option confusion
    cmd.append("--")
    
    # Add search paths
    cmd.extend(search_paths)
    
    return cmd

def parse_ripgrep_output(output: str, show_context: bool = True) -> List[Dict[str, Any]]:
    """
    Parse ripgrep output with enhanced cross-platform path support.
    
    Args:
        output: Raw ripgrep output
        show_context: Whether to include context lines in results
        
    Returns:
        List of dictionaries with parsed match information
    """
    results = []
    lines = output.splitlines()
    
    for line in lines:
        if not line.strip():
            continue
            
        # Enhanced regex to handle Windows drive letters and other edge cases
        # Accept drive letters or other colons in the path (cross-platform support)
        match = re.match(r'^(.*):(\d+)([:|-])(.*)', line)
        
        if match:
            file_path = match.group(1)
            line_number = int(match.group(2))
            separator = match.group(3)
            content = match.group(4)
            
            # Determine if this is a match line or context line
            is_match = separator == ':'
            is_context = separator == '-'
            
            # Only include context lines if requested
            if not show_context and is_context:
                continue
                
            result = {
                'file_path': file_path,
                'line_number': line_number,
                'content': content,
                'is_match': is_match,
                'is_context': is_context,
                'raw_line': line
            }
            
            results.append(result)
    
    return results

def execute_ripgrep_search(pattern: str, search_paths: List[str], **kwargs) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Execute ripgrep search with comprehensive error handling.
    
    Args:
        pattern: Search pattern
        search_paths: List of paths to search
        **kwargs: Additional arguments passed to build_ripgrep_command
        
    Returns:
        Tuple of (results, success_flag)
    """
    try:
        cmd = build_ripgrep_command(pattern, search_paths, **kwargs)
        
        # Execute with timeout protection
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120,  # 2 minute timeout
            check=False   # Don't raise on non-zero exit codes
        )
        
        # ripgrep returns 1 when no matches found, which is normal
        if result.returncode == 0:
            # Matches found
            parsed_results = parse_ripgrep_output(result.stdout, 
                                                kwargs.get('show_context', True))
            return parsed_results, True
        elif result.returncode == 1:
            # No matches found (normal)
            return [], True
        else:
            # Actual error
            print(f"ripgrep error (code {result.returncode}): {result.stderr}", file=sys.stderr)
            return [], False
            
    except subprocess.TimeoutExpired:
        print("ripgrep search timed out after 2 minutes", file=sys.stderr)
        return [], False
    except FileNotFoundError:
        print("ripgrep (rg) not found. Please install ripgrep.", file=sys.stderr)
        return [], False
    except Exception as e:
        print(f"Error executing ripgrep: {e}", file=sys.stderr)
        return [], False

def find_files_with_ripgrep(search_paths: List[str], glob_patterns: List[str] = None,
                           exclude_patterns: List[str] = None) -> List[str]:
    """
    Use ripgrep to find files matching patterns.
    
    Args:
        search_paths: Directories to search
        glob_patterns: Include file patterns
        exclude_patterns: Exclude file patterns
        
    Returns:
        List of file paths
    """
    rg_path = find_ripgrep()
    if not rg_path:
        return []
    
    cmd = [rg_path, "--files", "--color=never"]
    
    # Add include patterns
    if glob_patterns:
        for pattern in glob_patterns:
            cmd.extend(["--glob", pattern])
    
    # Add exclude patterns  
    if exclude_patterns:
        for exclude in exclude_patterns:
            cmd.extend(["--glob", f"!{exclude}"])
    
    # Add separator and paths
    cmd.append("--")
    cmd.extend(search_paths)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        else:
            return []
    except Exception:
        return []

# Convenience functions for common use cases
def simple_search(pattern: str, path: str, case_insensitive: bool = False) -> List[Dict[str, Any]]:
    """Simple text search in a file or directory."""
    results, success = execute_ripgrep_search(
        pattern, [path], 
        case_insensitive=case_insensitive,
        search_type='text'
    )
    return results if success else []

def regex_search(pattern: str, path: str, context: int = 0) -> List[Dict[str, Any]]:
    """Regex search with context lines."""
    results, success = execute_ripgrep_search(
        pattern, [path],
        search_type='regex',
        context_before=context,
        context_after=context
    )
    return results if success else []

def multi_file_search(pattern: str, directory: str, file_types: List[str] = None) -> List[Dict[str, Any]]:
    """Search across multiple files of specific types."""
    glob_patterns = file_types if file_types else None
    results, success = execute_ripgrep_search(
        pattern, [directory],
        glob_patterns=glob_patterns,
        recursive=True
    )
    return results if success else []

if __name__ == "__main__":
    # Test the module
    print("Testing ripgrep integration...")
    
    # Test if ripgrep is available
    rg_path = find_ripgrep()
    if rg_path:
        print(f"✓ Found ripgrep at: {rg_path}")
        
        # Test simple search
        results = simple_search("def", ".", case_insensitive=True)
        print(f"✓ Found {len(results)} matches for 'def'")
        
        # Test command building
        cmd = build_ripgrep_command("test", ["."], context_before=2, search_type='regex')
        print(f"✓ Built command: {' '.join(cmd[:5])}...")
    else:
        print("✗ ripgrep not found")