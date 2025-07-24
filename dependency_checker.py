#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Centralized dependency checker for external tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-19
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import shutil
import sys
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

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

class DependencyChecker:
    """Check for external tool dependencies with multi-platform installation guidance."""
    
    # Tool installation instructions for different platforms
    TOOLS = {
        'rg': {
            'name': 'ripgrep',
            'description': 'Fast file searching tool',
            'check_commands': ['rg', 'ripgrep'],
            'install': {
                'macos': 'brew install ripgrep',
                'ubuntu': 'sudo apt-get install ripgrep',
                'debian': 'sudo apt-get install ripgrep',
                'fedora': 'sudo dnf install ripgrep',
                'arch': 'sudo pacman -S ripgrep',
                'windows': 'choco install ripgrep',
                'universal': 'See https://github.com/BurntSushi/ripgrep#installation'
            }
        },
        'java': {
            'name': 'Java',
            'description': 'Java development kit',
            'check_commands': ['java', 'javac'],
            'install': {
                'macos': 'brew install openjdk',
                'ubuntu': 'sudo apt-get install default-jdk',
                'debian': 'sudo apt-get install default-jdk',
                'fedora': 'sudo dnf install java-latest-openjdk-devel',
                'arch': 'sudo pacman -S jdk-openjdk',
                'windows': 'choco install openjdk',
                'universal': 'Download from https://adoptium.net/'
            }
        },
        'gradle': {
            'name': 'Gradle',
            'description': 'Build automation tool',
            'check_commands': ['gradle'],
            'install': {
                'macos': 'brew install gradle',
                'ubuntu': 'sudo apt-get install gradle',
                'debian': 'sudo apt-get install gradle',
                'fedora': 'sudo dnf install gradle',
                'arch': 'sudo pacman -S gradle',
                'windows': 'choco install gradle',
                'universal': 'See https://gradle.org/install/'
            }
        },
        'maven': {
            'name': 'Maven',
            'description': 'Build automation tool',
            'check_commands': ['mvn'],
            'install': {
                'macos': 'brew install maven',
                'ubuntu': 'sudo apt-get install maven',
                'debian': 'sudo apt-get install maven',
                'fedora': 'sudo dnf install maven',
                'arch': 'sudo pacman -S maven',
                'windows': 'choco install maven',
                'universal': 'See https://maven.apache.org/download.cgi'
            }
        },
        'node': {
            'name': 'Node.js',
            'description': 'JavaScript runtime',
            'check_commands': ['node', 'nodejs'],
            'install': {
                'macos': 'brew install node',
                'ubuntu': 'sudo apt-get install nodejs npm',
                'debian': 'sudo apt-get install nodejs npm',
                'fedora': 'sudo dnf install nodejs npm',
                'arch': 'sudo pacman -S nodejs npm',
                'windows': 'choco install nodejs',
                'universal': 'Download from https://nodejs.org/'
            }
        },
        'git': {
            'name': 'Git',
            'description': 'Version control system',
            'check_commands': ['git'],
            'install': {
                'macos': 'brew install git',
                'ubuntu': 'sudo apt-get install git',
                'debian': 'sudo apt-get install git',
                'fedora': 'sudo dnf install git',
                'arch': 'sudo pacman -S git',
                'windows': 'choco install git',
                'universal': 'Download from https://git-scm.com/downloads'
            }
        }
    }
    
    @staticmethod
    def detect_platform() -> str:
        """Detect the current operating system platform."""
        system = platform.system().lower()
        
        if system == 'darwin':
            return 'macos'
        elif system == 'windows':
            return 'windows'
        elif system == 'linux':
            # Try to detect Linux distribution
            try:
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'ubuntu' in content:
                        return 'ubuntu'
                    elif 'debian' in content:
                        return 'debian'
                    elif 'fedora' in content:
                        return 'fedora'
                    elif 'arch' in content:
                        return 'arch'
            except:
                pass
            return 'ubuntu'  # Default Linux
        else:
            return 'ubuntu'  # Default fallback
    
    @classmethod
    def check_tool(cls, tool_key: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a tool is installed.
        
        Returns:
            (is_installed, path_to_tool)
        """
        if tool_key not in cls.TOOLS:
            return False, None
            
        tool_info = cls.TOOLS[tool_key]
        
        for cmd in tool_info['check_commands']:
            path = shutil.which(cmd)
            if path:
                return True, path
                
        return False, None
    
    @classmethod
    def get_installation_instructions(cls, tool_key: str, current_platform: Optional[str] = None) -> str:
        """Get installation instructions for a tool."""
        if tool_key not in cls.TOOLS:
            return f"Unknown tool: {tool_key}"
            
        tool_info = cls.TOOLS[tool_key]
        
        if current_platform is None:
            current_platform = cls.detect_platform()
        
        instructions = [
            f"Error: {tool_info['name']} is not installed.",
            f"{tool_info['name']} is required for this tool to function properly.",
            "",
            "Installation instructions:",
            ""
        ]
        
        # Platform-specific instruction
        if current_platform in tool_info['install']:
            instructions.append(f"For your platform ({current_platform}):")
            instructions.append(f"  {tool_info['install'][current_platform]}")
            instructions.append("")
        
        # Show all platform instructions
        instructions.append("For other platforms:")
        for platform_name, install_cmd in tool_info['install'].items():
            if platform_name != 'universal' and platform_name != current_platform:
                instructions.append(f"  {platform_name.capitalize()}: {install_cmd}")
        
        # Universal instruction
        instructions.append("")
        instructions.append(f"Universal: {tool_info['install']['universal']}")
        
        return "\n".join(instructions)
    
    @classmethod
    def check_and_report(cls, tool_key: str, exit_on_missing: bool = True) -> bool:
        """
        Check for a tool and report if missing.
        
        Args:
            tool_key: Key of the tool to check
            exit_on_missing: Exit the program if tool is missing
            
        Returns:
            True if tool is installed, False otherwise
        """
        is_installed, tool_path = cls.check_tool(tool_key)
        
        if not is_installed:
            print(cls.get_installation_instructions(tool_key), file=sys.stderr)
            if exit_on_missing:
                sys.exit(1)
            return False
            
        return True
    
    @classmethod
    def check_multiple(cls, tool_keys: List[str], exit_on_missing: bool = True) -> Dict[str, bool]:
        """
        Check multiple tools at once.
        
        Returns:
            Dictionary of tool_key: is_installed
        """
        results = {}
        missing = []
        
        for tool_key in tool_keys:
            is_installed, _ = cls.check_tool(tool_key)
            results[tool_key] = is_installed
            if not is_installed:
                missing.append(tool_key)
        
        if missing and exit_on_missing:
            print("Missing required dependencies:", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            for tool_key in missing:
                print(f"\n{cls.get_installation_instructions(tool_key)}", file=sys.stderr)
                print("-" * 60, file=sys.stderr)
            sys.exit(1)
            
        return results

# Convenience functions for backward compatibility
def check_ripgrep(exit_on_missing: bool = True) -> bool:
    """Check if ripgrep is installed."""
    return DependencyChecker.check_and_report('rg', exit_on_missing)

def check_java(exit_on_missing: bool = True) -> bool:
    """Check if Java is installed."""
    return DependencyChecker.check_and_report('java', exit_on_missing)

def check_gradle(exit_on_missing: bool = True) -> bool:
    """Check if Gradle is installed."""
    return DependencyChecker.check_and_report('gradle', exit_on_missing)

def check_maven(exit_on_missing: bool = True) -> bool:
    """Check if Maven is installed."""
    return DependencyChecker.check_and_report('maven', exit_on_missing)

def check_node(exit_on_missing: bool = True) -> bool:
    """Check if Node.js is installed."""
    return DependencyChecker.check_and_report('node', exit_on_missing)

def check_git(exit_on_missing: bool = True) -> bool:
    """Check if Git is installed."""
    return DependencyChecker.check_and_report('git', exit_on_missing)

if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Check for external tool dependencies")
    parser.add_argument('tools', nargs='*', default=['rg'],
                       help='Tools to check (default: rg)')
    args = parser.parse_args()
    
    if args.all:
        tools_to_check = list(DependencyChecker.TOOLS.keys())
    else:
        tools_to_check = args.tools
    
    results = DependencyChecker.check_multiple(tools_to_check, exit_on_missing=False)
    
    print("Dependency Check Results:")
    print("=" * 40)
    for tool, is_installed in results.items():
        tool_name = DependencyChecker.TOOLS[tool]['name']
        status = "✓ Installed" if is_installed else "✗ Not installed"
        print(f"{tool_name}: {status}")
    
    # Show installation instructions for missing tools
    missing = [k for k, v in results.items() if not v]
    if missing:
        print("\nInstallation instructions for missing tools:")
        for tool in missing:
            print(f"\n{DependencyChecker.get_installation_instructions(tool)}")
            print("-" * 60)