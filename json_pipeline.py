#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
JSON pipeline support for find → replace workflows.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import json
import sys
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class MatchContext:
    """Context information for a match."""
    ast_context: Optional[str] = None
    block_type: Optional[str] = None  
    block_start: Optional[int] = None
    block_end: Optional[int] = None
    method_name: Optional[str] = None
    class_name: Optional[str] = None

@dataclass  
class SearchMatch:
    """Represents a single search match with full context."""
    file_path: str
    line_number: int
    content: str
    pattern: str
    match_type: str = 'exact'  # 'exact', 'regex', 'word', 'fixed'
    context_before: List[str] = None
    context_after: List[str] = None
    context: Optional[MatchContext] = None
    is_match: bool = True
    
    def __post_init__(self):
        if self.context_before is None:
            self.context_before = []
        if self.context_after is None:
            self.context_after = []
        if self.context is None:
            self.context = MatchContext()

@dataclass
class SearchResults:
    """Complete search results with metadata."""
    matches: List[SearchMatch]
    total_matches: int
    total_files: int
    search_pattern: str
    search_type: str
    timestamp: str
    tool_version: str = "find_text_v6"
    command_args: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.command_args is None:
            self.command_args = {}

def create_search_results(matches: List[Dict[str, Any]], pattern: str, 
                         search_type: str, command_args: Dict[str, Any] = None) -> SearchResults:
    """
    Create SearchResults from raw match data.
    
    Args:
        matches: Raw match dictionaries from ripgrep or other sources
        pattern: Search pattern used
        search_type: Type of search performed
        command_args: Command line arguments used
        
    Returns:
        SearchResults object
    """
    search_matches = []
    files_seen = set()
    
    for match_data in matches:
        if not match_data.get('is_match', True):
            continue  # Skip context lines when building results
            
        file_path = match_data['file_path']
        files_seen.add(file_path)
        
        # Extract context information if available
        context = MatchContext()
        if 'ast_context' in match_data:
            context.ast_context = match_data['ast_context']
        if 'block_type' in match_data:
            context.block_type = match_data['block_type']
            context.block_start = match_data.get('block_start')
            context.block_end = match_data.get('block_end')
        if 'method_name' in match_data:
            context.method_name = match_data['method_name']
        if 'class_name' in match_data:
            context.class_name = match_data['class_name']
        
        match = SearchMatch(
            file_path=file_path,
            line_number=match_data['line_number'],
            content=match_data['content'],
            pattern=pattern,
            match_type=search_type,
            context_before=match_data.get('context_before', []),
            context_after=match_data.get('context_after', []),
            context=context
        )
        
        search_matches.append(match)
    
    return SearchResults(
        matches=search_matches,
        total_matches=len(search_matches),
        total_files=len(files_seen),
        search_pattern=pattern,
        search_type=search_type,
        timestamp=datetime.now().isoformat(),
        command_args=command_args or {}
    )

def serialize_search_results(results: SearchResults) -> str:
    """
    Serialize SearchResults to JSON string.
    
    Args:
        results: SearchResults object
        
    Returns:
        JSON string
    """
    return json.dumps(asdict(results), indent=2, ensure_ascii=False)

def deserialize_search_results(json_str: str) -> SearchResults:
    """
    Deserialize JSON string to SearchResults.
    
    Args:
        json_str: JSON string
        
    Returns:
        SearchResults object
    """
    data = json.loads(json_str)
    
    # Reconstruct matches with proper dataclass objects
    matches = []
    for match_data in data['matches']:
        context_data = match_data.get('context', {})
        context = MatchContext(**context_data) if context_data else MatchContext()
        
        match = SearchMatch(
            file_path=match_data['file_path'],
            line_number=match_data['line_number'],
            content=match_data['content'],
            pattern=match_data['pattern'],
            match_type=match_data.get('match_type', 'exact'),
            context_before=match_data.get('context_before', []),
            context_after=match_data.get('context_after', []),
            context=context,
            is_match=match_data.get('is_match', True)
        )
        matches.append(match)
    
    return SearchResults(
        matches=matches,
        total_matches=data['total_matches'],
        total_files=data['total_files'],
        search_pattern=data['search_pattern'],
        search_type=data['search_type'],
        timestamp=data['timestamp'],
        tool_version=data.get('tool_version', 'unknown'),
        command_args=data.get('command_args', {})
    )

def load_search_results_from_file(file_path: str) -> SearchResults:
    """
    Load SearchResults from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        SearchResults object
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_str = f.read()
        return deserialize_search_results(json_str)
    except Exception as e:
        raise ValueError(f"Error loading search results from {file_path}: {e}")

def save_search_results_to_file(results: SearchResults, file_path: str) -> None:
    """
    Save SearchResults to JSON file.
    
    Args:
        results: SearchResults object
        file_path: Path to save JSON file
    """
    try:
        json_str = serialize_search_results(results)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
    except Exception as e:
        raise ValueError(f"Error saving search results to {file_path}: {e}")

def load_search_results_from_stdin() -> SearchResults:
    """
    Load SearchResults from stdin.
    
    Returns:
        SearchResults object
    """
    try:
        json_str = sys.stdin.read()
        return deserialize_search_results(json_str)
    except Exception as e:
        raise ValueError(f"Error loading search results from stdin: {e}")

def filter_matches_by_file(results: SearchResults, file_patterns: List[str]) -> SearchResults:
    """
    Filter matches by file patterns.
    
    Args:
        results: Original SearchResults
        file_patterns: List of file glob patterns to include
        
    Returns:
        Filtered SearchResults
    """
    import fnmatch
    
    filtered_matches = []
    for match in results.matches:
        file_path = Path(match.file_path)
        
        # Check if file matches any pattern
        for pattern in file_patterns:
            if fnmatch.fnmatch(str(file_path), pattern) or fnmatch.fnmatch(file_path.name, pattern):
                filtered_matches.append(match)
                break
    
    files_seen = set(match.file_path for match in filtered_matches)
    
    return SearchResults(
        matches=filtered_matches,
        total_matches=len(filtered_matches),
        total_files=len(files_seen),
        search_pattern=results.search_pattern,
        search_type=results.search_type,
        timestamp=results.timestamp,
        tool_version=results.tool_version,
        command_args=results.command_args
    )

def filter_matches_by_context(results: SearchResults, context_type: str, 
                             context_value: str = None) -> SearchResults:
    """
    Filter matches by context information.
    
    Args:
        results: Original SearchResults
        context_type: 'block_type', 'method_name', 'class_name', etc.
        context_value: Specific value to match (None for any non-empty value)
        
    Returns:
        Filtered SearchResults
    """
    filtered_matches = []
    
    for match in results.matches:
        if not match.context:
            continue
            
        context_attr = getattr(match.context, context_type, None)
        
        if context_value is None:
            # Include if attribute exists and is not None/empty
            if context_attr:
                filtered_matches.append(match)
        else:
            # Include if attribute matches specific value
            if context_attr == context_value:
                filtered_matches.append(match)
    
    files_seen = set(match.file_path for match in filtered_matches)
    
    return SearchResults(
        matches=filtered_matches,
        total_matches=len(filtered_matches),
        total_files=len(files_seen),
        search_pattern=results.search_pattern,
        search_type=results.search_type,
        timestamp=results.timestamp,
        tool_version=results.tool_version,
        command_args=results.command_args
    )

def create_replacement_plan(results: SearchResults, old_pattern: str, 
                           new_pattern: str, replacement_type: str = 'exact') -> Dict[str, Any]:
    """
    Create a replacement plan from search results.
    
    Args:
        results: SearchResults to base replacements on
        old_pattern: Pattern to replace (can be different from search pattern)
        new_pattern: Replacement pattern
        replacement_type: 'exact', 'regex', 'word', etc.
        
    Returns:
        Replacement plan dictionary
    """
    plan = {
        'replacement_type': replacement_type,
        'old_pattern': old_pattern,
        'new_pattern': new_pattern,
        'source_search': {
            'pattern': results.search_pattern,
            'type': results.search_type,
            'timestamp': results.timestamp
        },
        'targets': []
    }
    
    # Group matches by file for efficient processing
    file_matches = {}
    for match in results.matches:
        file_path = match.file_path
        if file_path not in file_matches:
            file_matches[file_path] = []
        file_matches[file_path].append(match)
    
    # Create replacement targets
    for file_path, matches in file_matches.items():
        target = {
            'file_path': file_path,
            'matches': [
                {
                    'line_number': match.line_number,
                    'original_content': match.content,
                    'context': asdict(match.context) if match.context else None
                }
                for match in matches
            ]
        }
        plan['targets'].append(target)
    
    return plan

def validate_search_results(results: Union[SearchResults, dict]) -> List[str]:
    """
    Validate search results structure and content.
    
    Args:
        results: SearchResults object or dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if isinstance(results, dict):
        try:
            results = SearchResults(**results)
        except Exception as e:
            errors.append(f"Invalid SearchResults structure: {e}")
            return errors
    
    if not isinstance(results, SearchResults):
        errors.append("Invalid results type")
        return errors
    
    # Validate required fields
    if not results.search_pattern:
        errors.append("Missing search_pattern")
    
    if not results.search_type:
        errors.append("Missing search_type")
    
    if not results.timestamp:
        errors.append("Missing timestamp")
    
    # Validate matches
    if results.total_matches != len(results.matches):
        errors.append(f"Match count mismatch: reported {results.total_matches}, actual {len(results.matches)}")
    
    # Validate individual matches
    for i, match in enumerate(results.matches):
        if not match.file_path:
            errors.append(f"Match {i}: missing file_path")
        
        if match.line_number < 1:
            errors.append(f"Match {i}: invalid line_number {match.line_number}")
        
        if not match.content:
            errors.append(f"Match {i}: missing content")
    
    return errors

# Convenience functions for common pipeline operations
def find_to_replace_pipeline(search_results_json: str, old_pattern: str, 
                            new_pattern: str) -> Dict[str, Any]:
    """
    Convert find results to replace plan.
    
    Args:
        search_results_json: JSON string from find_text
        old_pattern: Pattern to replace
        new_pattern: Replacement pattern
        
    Returns:
        Replacement plan dictionary
    """
    results = deserialize_search_results(search_results_json)
    return create_replacement_plan(results, old_pattern, new_pattern)

def print_search_results_summary(results: SearchResults) -> None:
    """Print a summary of search results."""
    print(f"Search Results Summary:")
    print(f"  Pattern: '{results.search_pattern}' ({results.search_type})")
    print(f"  Found: {results.total_matches} matches in {results.total_files} files")
    print(f"  Tool: {results.tool_version}")
    print(f"  Timestamp: {results.timestamp}")
    
    if results.matches:
        print(f"  Files:")
        files = set(match.file_path for match in results.matches)
        for file_path in sorted(files):
            file_matches = [m for m in results.matches if m.file_path == file_path]
            print(f"    {file_path} ({len(file_matches)} matches)")

if __name__ == "__main__":
    # Test the module
    print("Testing JSON pipeline...")
    
    # Create test data
    test_matches = [
        {
            'file_path': 'test.py',
            'line_number': 10,
            'content': 'def test_function():',
            'is_match': True,
            'ast_context': 'TestClass → test_function',
            'block_type': 'function'
        },
        {
            'file_path': 'test.py', 
            'line_number': 25,
            'content': '    test_value = 42',
            'is_match': True,
            'method_name': 'test_function'
        }
    ]
    
    # Test serialization/deserialization
    results = create_search_results(test_matches, "test", "text")
    json_str = serialize_search_results(results)
    restored = deserialize_search_results(json_str)
    
    print(f"✓ Serialization test: {len(restored.matches)} matches restored")
    
    # Test validation
    errors = validate_search_results(results)
    if not errors:
        print("✓ Validation test passed")
    else:
        print(f"✗ Validation errors: {errors}")
    
    # Test replacement plan
    plan = create_replacement_plan(results, "test", "demo")
    print(f"✓ Replacement plan: {len(plan['targets'])} files targeted")