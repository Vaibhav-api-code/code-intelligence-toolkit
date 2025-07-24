#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced Standard Argument Parser - Resolves conflicts and supports tool-specific extensions.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Set

class EnhancedArgumentParser:
    """
    Enhanced argument parser that prevents conflicts and supports tool-specific extensions.
    """
    
    # Core standard arguments (always present)
    CORE_ARGS = {
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
        'dry_run': {
            'flags': ['--dry-run'],
            'action': 'store_true',
            'help': 'Preview changes without applying'
        }
    }
    
    # Tool-specific argument sets
    TOOL_SPECIFIC_ARGS = {
        'search': {
            'file_input': {
                'flags': ['--file'],
                'help': 'Search in specific file'
            },
            'scope': {
                'flags': ['--scope'],
                'default': '.',
                'help': 'Directory scope for search (default: current dir)'
            },
            'search_type': {
                'flags': ['--type'],
                'choices': ['text', 'regex', 'word', 'fixed'],
                'default': 'text',
                'help': 'Search type'
            },
            'ignore_case': {
                'flags': ['-i', '--ignore-case'],
                'action': 'store_true',
                'help': 'Case-insensitive search'
            },
            'whole_word': {
                'flags': ['-w', '--whole-word'],
                'action': 'store_true',
                'help': 'Match whole words only'
            },
            'include_glob': {
                'flags': ['--include', '--glob', '-g'],
                'dest': 'glob',
                'help': 'Include files matching pattern (e.g., "*.java")'
            },
            'exclude': {
                'flags': ['--exclude'],
                'help': 'Exclude files matching pattern'
            },
            'context': {
                'flags': ['-C', '--context'],
                'type': int,
                'metavar': 'N',
                'help': 'Show N lines around match'
            },
            'after_context': {
                'flags': ['-A', '--after-context'],
                'type': int,
                'metavar': 'N',
                'help': 'Show N lines after match'
            },
            'before_context': {
                'flags': ['-B', '--before-context'],
                'type': int,
                'metavar': 'N',
                'help': 'Show N lines before match'
            },
            'recursive': {
                'flags': ['-r', '--recursive'],
                'action': 'store_true',
                'help': 'Search recursively in directories'
            }
        },
        'analyze': {
            'file_input': {
                'flags': ['--file'],
                'help': 'Analyze in specific file'
            },
            'scope': {
                'flags': ['--scope'],
                'default': '.',
                'help': 'Directory scope for analysis (default: current dir)'
            },
            'symbol_type': {
                'flags': ['--type'],
                'choices': ['method', 'class', 'function', 'variable', 'auto'],
                'default': 'auto',
                'help': 'Type of symbol to analyze'
            },
            'max_depth': {
                'flags': ['--max-depth'],
                'type': int,
                'default': 3,
                'help': 'Maximum depth for dependency analysis'
            },
            'show_callers': {
                'flags': ['--show-callers'],
                'action': 'store_true',
                'help': 'Show where this symbol is called from'
            },
            'show_callees': {
                'flags': ['--show-callees'],
                'action': 'store_true',
                'help': 'Show what this symbol calls'
            },
            'language': {
                'flags': ['--language', '--lang'],
                'choices': ['python', 'java', 'javascript', 'cpp', 'go', 'rust'],
                'help': 'Filter by programming language'
            },
            'ignore_case': {
                'flags': ['-i', '--ignore-case'],
                'action': 'store_true',
                'help': 'Case-insensitive analysis'
            }
        },
        'directory': {
            'long_format': {
                'flags': ['-l', '--long'],
                'action': 'store_true',
                'help': 'Long format with details'
            },
            'all_files': {
                'flags': ['-a', '--all'],
                'action': 'store_true',
                'help': 'Show hidden files'
            },
            'sort_order': {
                'flags': ['--sort'],
                'choices': ['name', 'size', 'time', 'ext'],
                'default': 'name',
                'help': 'Sort order'
            },
            'include_glob': {
                'flags': ['--include', '--glob', '-g'],
                'dest': 'glob',
                'help': 'Include files matching pattern'
            },
            'exclude': {
                'flags': ['--exclude'],
                'help': 'Exclude files matching pattern'
            },
            'file_type': {
                'flags': ['--type'],
                'choices': ['f', 'd', 'l', 'all'],
                'default': 'all',
                'help': 'File type filter'
            },
            'recursive': {
                'flags': ['-r', '--recursive'],
                'action': 'store_true',
                'help': 'Recurse into subdirectories'
            },
            'max_depth': {
                'flags': ['--max-depth'],
                'type': int,
                'help': 'Maximum recursion depth'
            },
            'ext_filter': {
                'flags': ['--ext'],
                'help': 'Filter by file extension'
            },
            'limit': {
                'flags': ['--limit', '--max'],
                'type': int,
                'help': 'Limit number of results'
            }
        }
    }
    
    # Common extensions used by many tools
    COMMON_EXTENSIONS = {
        'ast_context': {
            'flags': ['--ast-context'],
            'action': 'store_true',
            'help': 'Show AST context (class/method hierarchy)'
        },
        'no_ast_context': {
            'flags': ['--no-ast-context'],
            'action': 'store_true',
            'help': 'Disable AST context display'
        },
        'format': {
            'flags': ['--format', '-f'],
            'choices': ['text', 'json', 'markdown', 'csv'],
            'default': 'text',
            'help': 'Output format'
        },
        'output': {
            'flags': ['--output', '-o'],
            'help': 'Output file (default: stdout)'
        },
        'summary': {
            'flags': ['--summary'],
            'action': 'store_true',
            'help': 'Show summary only'
        },
        'check_compile': {
            'flags': ['--check-compile'],
            'action': 'store_true',
            'help': 'Check syntax/compilation after operations'
        },
        'no_check_compile': {
            'flags': ['--no-check-compile'],
            'action': 'store_true',
            'help': 'Disable compile checking'
        },
        'force': {
            'flags': ['--force'],
            'action': 'store_true',
            'help': 'Force operation without confirmation'
        }
    }
    
    @staticmethod
    def create_parser(tool_type: str, 
                     description: str, 
                     positional_args: Optional[List[Dict]] = None,
                     extensions: Optional[List[str]] = None,
                     exclude_standard: Optional[List[str]] = None,
                     **kwargs) -> argparse.ArgumentParser:
        """
        Create an enhanced parser that avoids conflicts.
        
        Args:
            tool_type: Type of tool (search, analyze, directory)
            description: Tool description
            positional_args: List of positional argument definitions
            extensions: List of extension names to include
            exclude_standard: List of standard args to exclude
            **kwargs: Additional ArgumentParser arguments
        """
        
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            **kwargs
        )
        
        # Add positional arguments first
        if positional_args:
            for pos_arg in positional_args:
                name = pos_arg.pop('name')
                parser.add_argument(name, **pos_arg)
        
        # Add tool-specific arguments
        if tool_type in EnhancedArgumentParser.TOOL_SPECIFIC_ARGS:
            tool_args = EnhancedArgumentParser.TOOL_SPECIFIC_ARGS[tool_type]
            for arg_name, arg_config in tool_args.items():
                if exclude_standard and arg_name in exclude_standard:
                    continue
                try:
                    flags = arg_config.pop('flags')
                    parser.add_argument(*flags, **arg_config)
                except argparse.ArgumentError as e:
                    # Skip conflicting arguments with a warning
                    print(f"Warning: Skipping conflicting argument {flags}: {e}", file=sys.stderr)
        
        # Add requested extensions
        if extensions:
            for ext_name in extensions:
                if ext_name in EnhancedArgumentParser.COMMON_EXTENSIONS:
                    ext_config = EnhancedArgumentParser.COMMON_EXTENSIONS[ext_name].copy()
                    try:
                        flags = ext_config.pop('flags')
                        parser.add_argument(*flags, **ext_config)
                    except argparse.ArgumentError as e:
                        print(f"Warning: Skipping conflicting extension {flags}: {e}", file=sys.stderr)
        
        # Add core arguments last (these are always included)
        exclude_core = exclude_standard or []
        for arg_name, arg_config in EnhancedArgumentParser.CORE_ARGS.items():
            if arg_name not in exclude_core:
                try:
                    flags = arg_config['flags']
                    config = {k: v for k, v in arg_config.items() if k != 'flags'}
                    parser.add_argument(*flags, **config)
                except argparse.ArgumentError as e:
                    # Core args might conflict with tool-specific ones, skip gracefully
                    print(f"Info: Core argument {flags} already defined", file=sys.stderr)
        
        return parser
    
    @staticmethod
    def create_search_parser(description: str, **kwargs) -> argparse.ArgumentParser:
        """Convenience method for search tools."""
        positional = [{'name': 'pattern', 'nargs': '?', 'help': 'Search pattern or text (optional with --lines or --ranges)'}]
        extensions = ['ast_context', 'no_ast_context']
        return EnhancedArgumentParser.create_parser(
            'search', description, positional_args=positional, 
            extensions=extensions, **kwargs
        )
    
    @staticmethod
    def create_analyze_parser(description: str, **kwargs) -> argparse.ArgumentParser:
        """Convenience method for analyze tools."""
        positional = [{'name': 'target', 'help': 'Name of method/class/symbol to analyze'}]
        extensions = ['ast_context', 'format', 'summary']
        return EnhancedArgumentParser.create_parser(
            'analyze', description, positional_args=positional,
            extensions=extensions, **kwargs
        )
    
    @staticmethod
    def create_directory_parser(description: str, **kwargs) -> argparse.ArgumentParser:
        """Convenience method for directory tools."""
        positional = [{'name': 'path', 'nargs': '?', 'default': '.', 
                      'help': 'Directory path (default: current directory)'}]
        return EnhancedArgumentParser.create_parser(
            'directory', description, positional_args=positional, **kwargs
        )


# Convenience functions for backward compatibility
def create_standard_parser(tool_type: str, description: str, 
                          epilog: Optional[str] = None, **kwargs) -> argparse.ArgumentParser:
    """Enhanced create_standard_parser with conflict resolution."""
    return EnhancedArgumentParser.create_parser(
        tool_type, description, epilog=epilog, **kwargs
    )

def create_search_parser(description: str, **kwargs) -> argparse.ArgumentParser:
    """Create parser for search tools."""
    return EnhancedArgumentParser.create_search_parser(description, **kwargs)

def create_analyze_parser(description: str, **kwargs) -> argparse.ArgumentParser:
    """Create parser for analyze tools."""
    return EnhancedArgumentParser.create_analyze_parser(description, **kwargs)

def create_directory_parser(description: str, **kwargs) -> argparse.ArgumentParser:
    """Create parser for directory tools."""
    return EnhancedArgumentParser.create_directory_parser(description, **kwargs)


if __name__ == "__main__":
    print("Enhanced Standard Argument Parser - Test")
    print("=" * 50)
    
    # Test search parser
    print("\n1. Search Parser:")
    search_parser = create_search_parser('Search for patterns in code')
    search_parser.print_help()
    
    # Test analyze parser
    print("\n\n2. Analyze Parser:")
    analyze_parser = create_analyze_parser('Analyze code symbols')
    analyze_parser.print_help()
    
    # Test directory parser
    print("\n\n3. Directory Parser:")
    dir_parser = create_directory_parser('List directory contents')
    dir_parser.print_help()