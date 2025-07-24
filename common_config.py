#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Unified configuration system for Python development tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-19
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import configparser
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import os
import sys

def find_project_root(path: Path = None) -> Optional[Path]:
    """
    Finds the project root by looking for marker files.
    
    Args:
        path: Starting path to search from (default: current directory)
        
    Returns:
        Path to project root or None if not found
    """
    if path is None:
        path = Path.cwd()
    
    current = path.resolve()
    
    # Common project markers in order of preference
    markers = [
        '.pytoolsrc',     # Our config file
        '.git',           # Git repository
        'pyproject.toml', # Python project
        'package.json',   # Node project
        'pom.xml',        # Maven project
        'build.gradle',   # Gradle project
        'Makefile',       # Make-based project
        'CMakeLists.txt', # CMake project
    ]
    
    while current.parent != current:
        for marker in markers:
            marker_path = current / marker
            if marker_path.exists():
                return current
        current = current.parent
    
    return None

def load_config(project_root: Optional[Path] = None) -> configparser.ConfigParser:
    """
    Loads the .pytoolsrc configuration file.
    
    Args:
        project_root: Project root path (auto-detected if None)
        
    Returns:
        ConfigParser instance with loaded configuration
    """
    config = configparser.ConfigParser()
    
    # Set sensible defaults
    config.read_dict({
        'defaults': {
            'all': 'false',
            'include_build': 'false',
            'max_depth': '10',
            'quiet': 'false'
        }
    })
    
    if project_root is None:
        project_root = find_project_root()
    
    if project_root:
        config_file = project_root / '.pytoolsrc'
        if config_file.exists():
            try:
                config.read(config_file)
            except configparser.Error as e:
                print(f"Warning: Error reading config file {config_file}: {e}", file=sys.stderr)
    
    return config

def convert_config_value(value: str, target_type: type) -> Any:
    """
    Convert string config value to appropriate Python type.
    
    Args:
        value: String value from config file
        target_type: Target type for conversion
        
    Returns:
        Converted value
    """
    if target_type == bool:
        return value.lower() in ['true', 'yes', 'on', '1']
    elif target_type == int:
        try:
            return int(value)
        except ValueError:
            return 0
    elif target_type == float:
        try:
            return float(value)
        except ValueError:
            return 0.0
    else:
        return value

def apply_config_to_args(tool_name: str, args: argparse.Namespace, 
                        parser: argparse.ArgumentParser, 
                        config: configparser.ConfigParser = None) -> None:
    """
    Applies defaults from config file to argparse namespace.
    Command-line arguments always override config file settings.
    
    Args:
        tool_name: Name of the tool section in config
        args: Parsed arguments namespace
        parser: ArgumentParser instance for getting defaults
        config: Configuration object (auto-loaded if None)
    """
    if config is None:
        config = load_config()
    
    # Sections to check in order of priority (later overrides earlier)
    sections_to_check = ['defaults']
    if tool_name and config.has_section(tool_name):
        sections_to_check.append(tool_name)
    
    for section_name in sections_to_check:
        if not config.has_section(section_name):
            continue
            
        for key, value in config.items(section_name):
            # Skip if this key doesn't exist as an argument
            if not hasattr(args, key):
                continue
            
            # Get the current value and default
            current_value = getattr(args, key)
            default_value = parser.get_default(key)
            
            # Only apply config if argument is still at default value
            if current_value == default_value:
                # Determine target type from the default value
                if default_value is not None:
                    target_type = type(default_value)
                    converted_value = convert_config_value(value, target_type)
                    setattr(args, key, converted_value)
                else:
                    # If default is None, try to infer from string value
                    if value.lower() in ['true', 'false', 'yes', 'no', 'on', 'off']:
                        setattr(args, key, convert_config_value(value, bool))
                    elif value.isdigit():
                        setattr(args, key, convert_config_value(value, int))
                    else:
                        setattr(args, key, value)

def get_config_value(section: str, key: str, default: Any = None, 
                    config: configparser.ConfigParser = None) -> Any:
    """
    Get a specific configuration value.
    
    Args:
        section: Config section name
        key: Config key name
        default: Default value if not found
        config: Configuration object (auto-loaded if None)
        
    Returns:
        Configuration value or default
    """
    if config is None:
        config = load_config()
    
    try:
        value = config.get(section, key)
        if default is not None:
            return convert_config_value(value, type(default))
        return value
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default

def resolve_config_path(path_str: str, base_path: Path = None) -> Path:
    """
    Resolve a path from config relative to project root.
    
    Args:
        path_str: Path string from config (can contain ~)
        base_path: Base path for resolution (default: project root)
        
    Returns:
        Resolved absolute path
    """
    if not path_str:
        return Path.cwd()
        
    # Expand user home directory
    path_str = os.path.expanduser(path_str)
    path = Path(path_str)
    
    # If absolute, return as-is
    if path.is_absolute():
        return path
    
    # Otherwise resolve relative to base path
    if base_path is None:
        base_path = find_project_root() or Path.cwd()
    
    return (base_path / path).resolve()

def get_config_path(section: str, key: str, default: str = ".", 
                   config: configparser.ConfigParser = None) -> Path:
    """
    Get a path configuration value and resolve it.
    
    Args:
        section: Config section name
        key: Config key name  
        default: Default path if not found
        config: Configuration object (auto-loaded if None)
        
    Returns:
        Resolved absolute Path object
    """
    path_str = get_config_value(section, key, default, config)
    return resolve_config_path(path_str)

def create_default_config(path: Path = None) -> Path:
    """
    Create a default .pytoolsrc configuration file.
    
    Args:
        path: Directory to create config in (default: project root)
        
    Returns:
        Path to created config file
    """
    if path is None:
        path = find_project_root() or Path.cwd()
    
    config_path = path / '.pytoolsrc'
    
    default_config = """# Python Development Tools Configuration
# This file defines project-wide defaults for the development toolkit

[defaults]
# Global defaults applied to all tools
all = false
include_build = false
max_depth = 10
quiet = false
ast_context = true
check_compile = true

[paths]
# Project-specific paths - customize these for your project
# These paths will be resolved relative to the project root
# (where .pytoolsrc is located)
java_source = src/main/java/         # Java source directory
python_source = src/main/python/     # Python source directory
resources = src/main/resources/      # Resources directory
build_output = build/                # Build output directory
documentation = docs/                # Documentation directory

[smart_ls]
# Enhanced directory listing defaults
sort = name
reverse = false
summary = true

[find_files]
# File search defaults  
sort = time
reverse = true
limit = 100

[recent_files]
# Recent files tracker defaults
since = 1h
show_size = true
by_dir = false

[tree_view]
# Directory tree visualization defaults
show_size = false
show_stats = false
max_depth = 5

[dir_stats]
# Directory analysis defaults
show_files = true
show_dirs = true
show_recent = true
show_empty = false

[replace_text]
# Text replacement defaults
backup = true
whole_word = false
dry_run = false

[replace_text_ast]
# AST-based refactoring defaults
dry_run = true
backup = true

[navigate_ast]
# AST navigation defaults
context_lines = 10
json = false

[method_analyzer_ast]
# Method analysis defaults
trace_flow = false
show_args = true

[semantic_diff_ast]
# Semantic diff defaults
score = true
risk_threshold = MEDIUM

[cross_file_analysis_ast]
# Cross-file analysis defaults
analyze = true
show_samples = true
max_samples = 3
recursive = false
max_depth = 3
"""
    
    with open(config_path, 'w') as f:
        f.write(default_config)
    
    return config_path

def show_config_info(config: configparser.ConfigParser = None) -> str:
    """
    Show current configuration information.
    
    Args:
        config: Configuration object (auto-loaded if None)
        
    Returns:
        Formatted configuration information
    """
    if config is None:
        config = load_config()
    
    project_root = find_project_root()
    config_file = project_root / '.pytoolsrc' if project_root else None
    
    output = []
    output.append("🔧 PYTHON TOOLS CONFIGURATION")
    output.append("=" * 50)
    
    if project_root:
        output.append(f"📁 Project root: {project_root}")
        if config_file and config_file.exists():
            output.append(f"⚙️  Config file: {config_file}")
        else:
            output.append("⚙️  Config file: Not found (using defaults)")
    else:
        output.append("📁 Project root: Not detected")
        output.append("⚙️  Config file: Not found (using defaults)")
    
    output.append("")
    output.append("📋 CURRENT CONFIGURATION:")
    
    for section_name in config.sections():
        output.append(f"\n[{section_name}]")
        for key, value in config.items(section_name):
            output.append(f"  {key} = {value}")
    
    if not config.sections():
        output.append("  (Using built-in defaults only)")
    
    return '\n'.join(output)

def main():
    """Command-line interface for configuration management."""
    parser = argparse.ArgumentParser(
        description='Manage Python development tools configuration',
        epilog='''
EXAMPLES:
  # Show current configuration
  common_config.py --show
  
  # Create default config file
  common_config.py --create
  
  # Find project root
  common_config.py --find-root
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--show', action='store_true',
                       help='Show current configuration')
    parser.add_argument('--create', action='store_true',
                       help='Create default .pytoolsrc file')
    parser.add_argument('--find-root', action='store_true',
                       help='Find and show project root')
    
    args = parser.parse_args()
    
    if args.find_root:
        root = find_project_root()
        if root:
            print(f"Project root: {root}")
        else:
            print("Project root: Not found")
    
    elif args.create:
        config_path = create_default_config()
        print(f"✅ Created default configuration: {config_path}")
        print("\nEdit this file to customize tool defaults for your project.")
    
    elif args.show:
        print(show_config_info())
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()