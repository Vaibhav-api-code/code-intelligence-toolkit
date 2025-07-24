#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Standardized argument parser for Python tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

class StandardArgumentParser:
    """
    Creates standardized argument parsers for different tool types.
    Ensures consistent interfaces across all tools.
    """
    
    # Common arguments used across multiple tools
    COMMON_ARGS = {
        'verbose': {
            'flags': ['-v', '--verbose'],
            'action': 'store_true',
            'help': 'Enable verbose output'
        },
        'quiet': {
            'flags': ['-q', '--quiet'],
            'action': 'store_true',
            'help': 'Minimal output'
        },
        'json': {
            'flags': ['--json'],
            'action': 'store_true',
            'help': 'Output in JSON format'
        },
        'recursive': {
            'flags': ['-r', '--recursive'],
            'action': 'store_true',
            'help': 'Search recursively in directories'
        },
        'max_depth': {
            'flags': ['--max-depth'],
            'type': int,
            'metavar': 'N',
            'help': 'Maximum recursion depth'
        }
    }
    
    @staticmethod
    def create_parser(tool_type: str, description: str, **kwargs) -> argparse.ArgumentParser:
        """
        Create a standardized parser based on tool type.
        
        Tool types:
        - 'search': Tools that search for patterns/text
        - 'analyze': Tools that analyze code (methods, classes)
        - 'refactor': Tools that modify code
        - 'navigate': Tools that navigate to code locations
        - 'directory': Tools that work with directories
        """
        
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            **kwargs
        )
        
        if tool_type == 'search':
            return StandardArgumentParser._create_search_parser(parser)
        elif tool_type == 'analyze':
            return StandardArgumentParser._create_analyze_parser(parser)
        elif tool_type == 'refactor':
            return StandardArgumentParser._create_refactor_parser(parser)
        elif tool_type == 'navigate':
            return StandardArgumentParser._create_navigate_parser(parser)
        elif tool_type == 'directory':
            return StandardArgumentParser._create_directory_parser(parser)
        else:
            raise ValueError(f"Unknown tool type: {tool_type}")
    
    @staticmethod
    def _create_search_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """Standard interface for search tools."""
        # Positional: pattern
        parser.add_argument('pattern', help='Search pattern or text')
        
        # Location specification
        location_group = parser.add_mutually_exclusive_group()
        location_group.add_argument('--file', '--path', dest='file',
                                   help='Search in specific file')
        location_group.add_argument('--scope', default='.',
                                   help='Directory scope for search (default: current dir)')
        
        # Search options
        parser.add_argument('--type', choices=['text', 'regex', 'word'],
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
        
        # Add common args
        StandardArgumentParser._add_common_args(parser, ['verbose', 'quiet', 'json', 'recursive'])
        
        return parser
    
    @staticmethod
    def _create_analyze_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """Standard interface for code analysis tools."""
        # Positional: target (method/class name)
        parser.add_argument('target', help='Name of method/class/symbol to analyze')
        
        # Location specification
        parser.add_argument('--file', help='Analyze in specific file')
        parser.add_argument('--scope', default='.',
                           help='Directory scope for analysis (default: current dir)')
        
        # Analysis options
        parser.add_argument('--type', choices=['method', 'class', 'function', 'variable', 'auto'],
                           default='auto', help='Type of symbol to analyze')
        parser.add_argument('--max-depth', type=int, default=3,
                           help='Maximum depth for dependency analysis')
        parser.add_argument('--show-callers', action='store_true',
                           help='Show where this symbol is called from')
        parser.add_argument('--show-callees', action='store_true',
                           help='Show what this symbol calls')
        
        # Add common args
        StandardArgumentParser._add_common_args(parser, ['verbose', 'quiet', 'json'])
        
        return parser
    
    @staticmethod
    def _create_refactor_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """Standard interface for refactoring tools."""
        # Subcommands for different refactoring operations
        subparsers = parser.add_subparsers(dest='operation', help='Refactoring operation')
        
        # Rename operation
        rename_parser = subparsers.add_parser('rename', help='Rename symbol')
        rename_parser.add_argument('old_name', help='Current name')
        rename_parser.add_argument('new_name', help='New name')
        rename_parser.add_argument('--file', help='Refactor in specific file')
        rename_parser.add_argument('--scope', default='.',
                                 help='Directory scope (default: current dir)')
        rename_parser.add_argument('--type', choices=['method', 'class', 'function', 'variable', 'auto'],
                                 default='auto', help='Type of symbol')
        rename_parser.add_argument('--dry-run', action='store_true',
                                 help='Preview changes without applying')
        
        # Replace operation
        replace_parser = subparsers.add_parser('replace', help='Replace text')
        replace_parser.add_argument('old_text', help='Text to replace')
        replace_parser.add_argument('new_text', help='Replacement text')
        replace_parser.add_argument('--file', help='Replace in specific file')
        replace_parser.add_argument('--scope', default='.',
                                  help='Directory scope (default: current dir)')
        replace_parser.add_argument('--regex', action='store_true',
                                  help='Use regex patterns')
        replace_parser.add_argument('--dry-run', action='store_true',
                                  help='Preview changes without applying')
        
        # Add common args to main parser
        StandardArgumentParser._add_common_args(parser, ['verbose', 'quiet'])
        
        return parser
    
    @staticmethod
    def _create_navigate_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """Standard interface for navigation tools."""
        # Required: file
        parser.add_argument('file', help='File to navigate in')
        
        # Target specification (one required)
        target_group = parser.add_mutually_exclusive_group(required=True)
        target_group.add_argument('--to', help='Navigate to symbol/line')
        target_group.add_argument('--line', '-l', type=int, help='Go to line number')
        target_group.add_argument('--method', '-m', help='Go to method')
        target_group.add_argument('--class', '-c', dest='class_name', help='Go to class')
        
        # Navigation options
        parser.add_argument('--context', '-C', type=int, default=10,
                           help='Lines of context to show (default: 10)')
        parser.add_argument('--highlight', action='store_true',
                           help='Highlight the target')
        
        # Add common args
        StandardArgumentParser._add_common_args(parser, ['verbose', 'quiet'])
        
        return parser
    
    @staticmethod
    def _create_directory_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """Standard interface for directory tools."""
        # Optional: path (defaults to current directory)
        parser.add_argument('path', nargs='?', default='.',
                           help='Directory path (default: current directory)')
        
        # Display options
        parser.add_argument('-l', '--long', action='store_true',
                           help='Long format with details')
        parser.add_argument('-a', '--all', action='store_true',
                           help='Show hidden files')
        parser.add_argument('--sort', choices=['name', 'size', 'time', 'ext'],
                           default='name', help='Sort order')
        
        # Filter options
        parser.add_argument('--include', '--glob', '-g', dest='glob',
                           help='Include files matching pattern')
        parser.add_argument('--exclude', help='Exclude files matching pattern')
        parser.add_argument('--type', choices=['f', 'd', 'l', 'all'],
                           default='all', help='File type filter')
        
        # Add common args
        StandardArgumentParser._add_common_args(parser, ['verbose', 'quiet', 'json', 'recursive', 'max_depth'])
        
        return parser
    
    @staticmethod
    def _add_common_args(parser: argparse.ArgumentParser, arg_names: List[str]) -> None:
        """Add common arguments to parser."""
        for arg_name in arg_names:
            if arg_name in StandardArgumentParser.COMMON_ARGS:
                arg_config = StandardArgumentParser.COMMON_ARGS[arg_name].copy()
                flags = arg_config.pop('flags')
                parser.add_argument(*flags, **arg_config)
    
    @staticmethod
    def parse_and_validate(parser: argparse.ArgumentParser, 
                          tool_type: str,
                          args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse arguments and perform standard validation.
        Includes pre-flight checks based on tool type.
        """
        parsed_args = parser.parse_args(args)
        
        # Import pre-flight checks if available
        try:
            from preflight_checks import PreflightChecker, run_preflight_checks
            
            checks = []
            
            # File existence checks
            if hasattr(parsed_args, 'file') and parsed_args.file:
                checks.append((PreflightChecker.check_file_readable, (parsed_args.file,)))
            
            # Directory existence checks
            if hasattr(parsed_args, 'scope') and parsed_args.scope and parsed_args.scope != '.':
                checks.append((PreflightChecker.check_directory_accessible, (parsed_args.scope,)))
            
            if hasattr(parsed_args, 'path') and parsed_args.path and parsed_args.path != '.':
                checks.append((PreflightChecker.check_directory_accessible, (parsed_args.path,)))
            
            # Method name validation for analyze tools
            if tool_type == 'analyze' and hasattr(parsed_args, 'target'):
                checks.append((PreflightChecker.validate_method_name, (parsed_args.target,)))
            
            # Run all checks
            if checks:
                run_preflight_checks(checks)
                
        except ImportError:
            pass  # Pre-flight checks not available
        
        return parsed_args
    

def create_standard_parser(tool_type: str, description: str, 
                          epilog: Optional[str] = None) -> argparse.ArgumentParser:
    """Convenience function to create standard parser."""
    return StandardArgumentParser.create_parser(
        tool_type, 
        description,
        epilog=epilog
    )


def parse_standard_args(parser: argparse.ArgumentParser, 
                       tool_type: str,
                       args: Optional[List[str]] = None) -> argparse.Namespace:
    """Convenience function to parse and validate arguments."""
    return StandardArgumentParser.parse_and_validate(parser, tool_type, args)


# Example usage and self-test
if __name__ == "__main__":
    print("Standard Argument Parser - Examples")
    print("=" * 50)
    
    # Example 1: Search tool
    print("\n1. Search Tool Interface:")
    search_parser = create_standard_parser('search', 'Search for patterns in code')
    search_parser.print_help()
    
    # Example 2: Analyze tool
    print("\n\n2. Analyze Tool Interface:")
    analyze_parser = create_standard_parser('analyze', 'Analyze code symbols')
    analyze_parser.print_help()
    
    # Example 3: Test parsing
    print("\n\n3. Test Parsing:")
    test_args = ['TODO', '--file', 'test.py', '-C', '5']
    parsed = parse_standard_args(search_parser, 'search', test_args)
    print(f"Parsed: pattern={parsed.pattern}, file={parsed.file}, context={parsed.context}")