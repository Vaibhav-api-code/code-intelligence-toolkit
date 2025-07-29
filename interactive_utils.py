#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Interactive Utilities v3 - Enhanced with .pytoolsrc configuration support

This module provides comprehensive functionality for all tools to properly handle
non-interactive environments with support for:
- Basic yes/no confirmations
- Typed phrase confirmations  
- Numbered selection menus
- Multi-option prompts (y/n/force, y/n/q)
- Multi-step confirmations
- Environment variable support
- .pytoolsrc configuration file support

Author: Code Intelligence Toolkit Team
Created: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import os
from typing import Optional, Any, List, Union, Tuple
from enum import Enum

# Try to import config support
try:
    from common_config import load_config, get_config_value
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False
    load_config = None
    get_config_value = None

# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class PromptChoice(Enum):
    """Enumeration for multi-choice prompt results."""
    YES = "yes"
    NO = "no"
    QUIT = "quit"
    FORCE = "force"
    ALL = "all"
    NONE = "none"
    CUSTOM = "custom"


# Global config cache
_config_cache = None


def _get_config():
    """Get cached configuration."""
    global _config_cache
    if _config_cache is None and HAS_CONFIG:
        _config_cache = load_config()
    return _config_cache


def is_interactive() -> bool:
    """
    Check if we're running in an interactive terminal.
    
    Checks in order:
    1. Global PYTOOLSRC_NON_INTERACTIVE environment variable
    2. .pytoolsrc [defaults] non_interactive setting
    3. TTY detection
    4. CI environment detection
    
    Returns:
        bool: True if interactive, False otherwise
    """
    # Check global environment override
    if os.getenv('PYTOOLSRC_NON_INTERACTIVE') == '1':
        return False
    
    # Check config file setting
    if HAS_CONFIG:
        config = _get_config()
        if config:
            non_interactive = get_config_value('defaults', 'non_interactive', False, config)
            if non_interactive:
                return False
    
    # Check if stdin is a TTY
    if not sys.stdin.isatty():
        return False
    
    # Check common CI environment variables
    ci_vars = [
        'CI',                      # Generic CI indicator
        'CONTINUOUS_INTEGRATION',  # Generic CI indicator
        'GITHUB_ACTIONS',         # GitHub Actions
        'GITLAB_CI',              # GitLab CI
        'JENKINS_URL',            # Jenkins
        'TRAVIS',                 # Travis CI
        'CIRCLECI',              # CircleCI
        'TEAMCITY_VERSION',       # TeamCity
        'BUILDKITE',             # Buildkite
        'DRONE',                 # Drone CI
        'CODEBUILD_BUILD_ID',    # AWS CodeBuild
        'TF_BUILD',              # Azure DevOps
    ]
    
    if any(os.getenv(var) for var in ci_vars):
        return False
    
    # Check for explicit non-interactive flags
    non_interactive_vars = [
        'NONINTERACTIVE',
        'DEBIAN_FRONTEND',  # Often set to 'noninteractive' in Docker
    ]
    
    for var in non_interactive_vars:
        value = os.getenv(var, '').lower()
        if value in ('1', 'true', 'yes', 'noninteractive'):
            return False
    
    return True


def safe_input(
    prompt: str,
    default: Optional[str] = None,
    tool_name: Optional[str] = None,
    env_var: Optional[str] = None,
    flag_hint: str = "--yes"
) -> str:
    """
    Safe input that handles non-interactive mode gracefully.
    
    Args:
        prompt: The prompt to display
        default: Default value to use in non-interactive mode
        tool_name: Name of the tool (for error messages)
        env_var: Environment variable to check for auto-yes
        flag_hint: Command-line flag to suggest (default: --yes)
    
    Returns:
        str: User input or default value
        
    Raises:
        SystemExit: If non-interactive and no default provided
    """
    # Check tool-specific environment variable
    if env_var and os.getenv(env_var) == '1':
        if default is not None:
            print(f"{prompt} [auto-answering from {env_var}: {default}]")
            return default
    
    # Check config file for tool-specific assume_yes
    if HAS_CONFIG and tool_name:
        config = _get_config()
        if config:
            assume_yes = get_config_value(tool_name.lower(), 'assume_yes', False, config)
            if assume_yes and default is not None:
                print(f"{prompt} [auto-answering from .pytoolsrc: {default}]")
                return default
    
    if not is_interactive():
        if default is not None:
            print(f"{prompt} [auto-answering: {default}]")
            return default
        else:
            tool_str = f"{tool_name}: " if tool_name else ""
            print(f"\n{Colors.RED}ERROR: {tool_str}Interactive input required but running in non-interactive mode.{Colors.END}")
            print(f"       Use {flag_hint} flag to skip confirmation")
            if env_var:
                print(f"       Or set {env_var}=1 environment variable")
            print(f"       Or set 'assume_yes = true' in .pytoolsrc [{tool_name or 'defaults'}] section")
            print(f"       Original prompt: {prompt}")
            sys.exit(1)
    
    try:
        return input(prompt)
    except EOFError:
        # This can still happen if TTY detection fails
        print(f"\n{Colors.RED}ERROR: Unexpected EOF while reading input.{Colors.END}")
        print(f"       This usually means the tool is running in a non-interactive environment.")
        print(f"       Use {flag_hint} flag or set appropriate environment variable.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)  # Standard exit code for SIGINT


def get_confirmation(
    prompt: str,
    default: bool = False,
    tool_name: Optional[str] = None,
    env_var: Optional[str] = None,
    flag_hint: str = "--yes",
    accept_responses: Optional[list] = None,
    typed_confirmation: Optional[str] = None
) -> bool:
    """
    Get yes/no confirmation from user with non-interactive support.
    
    Args:
        prompt: The confirmation prompt
        default: Default value (True/False) for non-interactive mode
        tool_name: Name of the tool
        env_var: Environment variable to check
        flag_hint: Command-line flag to suggest
        accept_responses: List of acceptable "yes" responses (default: ['y', 'yes'])
        typed_confirmation: If set, user must type this exact string to confirm
        
    Returns:
        bool: True if confirmed, False otherwise
    """
    if accept_responses is None:
        accept_responses = ['y', 'yes']
    
    # Check for auto-yes environment variable
    if env_var and os.getenv(env_var) == '1':
        print(f"{prompt} [auto-confirmed by {env_var}]")
        return True
    
    # Check config file for tool-specific assume_yes
    if HAS_CONFIG and tool_name:
        config = _get_config()
        if config:
            assume_yes = get_config_value(tool_name.lower(), 'assume_yes', False, config)
            auto_confirm = get_config_value(tool_name.lower(), 'auto_confirm', False, config)
            if assume_yes or auto_confirm:
                print(f"{prompt} [auto-confirmed by .pytoolsrc]")
                return True
    
    # Handle typed confirmation
    if typed_confirmation:
        full_prompt = f"{prompt}\nType '{typed_confirmation}' to confirm: "
        response = safe_input(
            full_prompt,
            default=typed_confirmation if default else None,
            tool_name=tool_name,
            env_var=env_var,
            flag_hint=flag_hint
        )
        return response == typed_confirmation
    
    # Handle yes/no confirmation
    suffix = " [Y/n]: " if default else " [y/N]: "
    full_prompt = prompt + suffix
    
    response = safe_input(
        full_prompt,
        default='y' if default else 'n',
        tool_name=tool_name,
        env_var=env_var,
        flag_hint=flag_hint
    )
    
    response = response.strip().lower()
    
    # Empty response uses default
    if not response:
        return default
    
    return response in accept_responses


def get_multi_choice(
    prompt: str,
    choices: List[Tuple[str, PromptChoice]],
    default: Optional[PromptChoice] = None,
    tool_name: Optional[str] = None,
    env_var: Optional[str] = None,
    flag_hint: str = "--yes",
    custom_responses: Optional[dict] = None
) -> PromptChoice:
    """
    Get multi-choice selection from user (e.g., y/n/force, y/n/q).
    
    Args:
        prompt: The prompt to display
        choices: List of tuples (key, PromptChoice) e.g., [('y', PromptChoice.YES), ('n', PromptChoice.NO)]
        default: Default choice for non-interactive mode
        tool_name: Name of the tool
        env_var: Environment variable to check
        flag_hint: Command-line flag to suggest
        custom_responses: Dict mapping input strings to PromptChoice values
        
    Returns:
        PromptChoice: The selected choice
    """
    # Build choice string for prompt
    choice_str = "/".join([k.upper() if c == default else k for k, c in choices])
    full_prompt = f"{prompt} [{choice_str}]: "
    
    # Check for force environment variable
    force_env = env_var.replace('ASSUME_YES', 'FORCE_YES') if env_var else None
    if force_env and os.getenv(force_env) == '1' and any(c == PromptChoice.FORCE for _, c in choices):
        print(f"{prompt} [auto-answering from {force_env}: force]")
        return PromptChoice.FORCE
    
    # Check config file for force
    if HAS_CONFIG and tool_name:
        config = _get_config()
        if config:
            force = get_config_value(tool_name.lower(), 'force', False, config)
            if force and any(c == PromptChoice.FORCE for _, c in choices):
                print(f"{prompt} [auto-answering from .pytoolsrc: force]")
                return PromptChoice.FORCE
    
    # Check for auto-yes
    if env_var and os.getenv(env_var) == '1' and default:
        print(f"{prompt} [auto-answering from {env_var}: {default.value}]")
        return default
    
    # Get input
    response = safe_input(
        full_prompt,
        default=default.value if default else None,
        tool_name=tool_name,
        env_var=env_var,
        flag_hint=flag_hint
    )
    
    response = response.strip().lower()
    
    # Empty response uses default
    if not response and default:
        return default
    
    # Check custom responses first
    if custom_responses and response in custom_responses:
        return custom_responses[response]
    
    # Check standard choices
    for key, choice in choices:
        if response == key.lower():
            return choice
    
    # Invalid response
    print(f"Invalid choice: {response}")
    return PromptChoice.NO  # Safe default


def get_numbered_selection(
    prompt: str,
    items: List[str],
    allow_quit: bool = True,
    default_index: Optional[int] = None,
    tool_name: Optional[str] = None,
    env_var: Optional[str] = None,
    flag_hint: str = "--select INDEX",
    zero_cancels: bool = True
) -> Optional[int]:
    """
    Get numbered selection from a list (for interactive restore/undo operations).
    
    Args:
        prompt: The prompt to display
        items: List of items to choose from
        allow_quit: Whether to allow 'q' to quit
        default_index: Default selection index for non-interactive mode
        tool_name: Name of the tool
        env_var: Environment variable to check
        flag_hint: Command-line flag to suggest
        zero_cancels: Whether entering '0' cancels the operation
        
    Returns:
        Optional[int]: Selected index (0-based) or None if cancelled
    """
    if not items:
        print("No items to select from.")
        return None
    
    # Display items
    for i, item in enumerate(items, 1):
        print(f"{i}. {item}")
    
    # Build prompt
    if zero_cancels:
        selection_prompt = f"{prompt} (1-{len(items)}) or 0 to cancel"
    else:
        selection_prompt = f"{prompt} (1-{len(items)})"
    
    if allow_quit:
        selection_prompt += " or 'q' to quit"
    selection_prompt += ": "
    
    # In non-interactive mode, use default or fail
    if not is_interactive():
        if default_index is not None:
            print(f"{selection_prompt} [auto-selecting: {default_index + 1}]")
            return default_index
        else:
            print(f"\n{Colors.RED}ERROR: Interactive selection required but running in non-interactive mode.{Colors.END}")
            print(f"       Use {flag_hint} to specify selection")
            if env_var:
                print(f"       Or set {env_var}_SELECT=INDEX environment variable")
            return None
    
    # Get input
    try:
        response = input(selection_prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled.")
        return None
    
    # Handle quit
    if allow_quit and response.lower() == 'q':
        return None
    
    # Handle cancel
    if zero_cancels and response == '0':
        return None
    
    # Parse number
    try:
        selection = int(response)
        if 1 <= selection <= len(items):
            return selection - 1  # Convert to 0-based index
        else:
            print(f"Invalid selection: {selection}")
            return None
    except ValueError:
        print(f"Invalid input: {response}")
        return None


def require_interactive(operation: str, tool_name: Optional[str] = None) -> None:
    """
    Require interactive mode for a specific operation.
    
    Args:
        operation: Description of the operation
        tool_name: Name of the tool
        
    Raises:
        SystemExit: Always in non-interactive mode
    """
    if not is_interactive():
        tool_str = f"{tool_name}: " if tool_name else ""
        print(f"\n{Colors.RED}ERROR: {tool_str}'{operation}' requires interactive mode.{Colors.END}")
        print(f"       This operation cannot be performed in non-interactive environments.")
        print(f"       Please run this command from an interactive terminal.")
        sys.exit(1)


def get_multi_confirmation(
    confirmations: List[Tuple[str, Optional[str]]],
    tool_name: Optional[str] = None,
    env_var: Optional[str] = None,
    flag_hint: str = "--force"
) -> bool:
    """
    Get multiple confirmations in sequence (for very dangerous operations).
    
    Args:
        confirmations: List of (prompt, typed_phrase) tuples
        tool_name: Name of the tool
        env_var: Environment variable to check
        flag_hint: Command-line flag to suggest
        
    Returns:
        bool: True if all confirmations passed, False otherwise
    """
    # Check for force environment variable
    force_env = env_var.replace('ASSUME_YES', 'FORCE_YES') if env_var else None
    if force_env and os.getenv(force_env) == '1':
        print(f"All confirmations auto-confirmed by {force_env}")
        return True
    
    # Check config file for force
    if HAS_CONFIG and tool_name:
        config = _get_config()
        if config:
            force = get_config_value(tool_name.lower(), 'force', False, config)
            if force:
                print(f"All confirmations auto-confirmed by .pytoolsrc")
                return True
    
    # Get each confirmation
    for prompt, typed_phrase in confirmations:
        if typed_phrase:
            if not get_confirmation(
                prompt,
                typed_confirmation=typed_phrase,
                tool_name=tool_name,
                env_var=env_var,
                flag_hint=flag_hint
            ):
                return False
        else:
            if not get_confirmation(
                prompt,
                tool_name=tool_name,
                env_var=env_var,
                flag_hint=flag_hint
            ):
                return False
    
    return True


# Convenience functions
def check_auto_yes_env(tool_name: str, args: Any) -> None:
    """
    Check and apply tool-specific auto-yes environment variable and config.
    
    Args:
        tool_name: Name of the tool (e.g., 'text_undo', 'safe_file_manager')
        args: Argument namespace to update
    """
    # Check environment variable
    env_var = get_tool_env_var(tool_name)
    if os.getenv(env_var) == '1' and hasattr(args, 'yes'):
        args.yes = True
    
    # Also check for force flag
    force_env = env_var.replace('ASSUME_YES', 'FORCE_YES')
    if os.getenv(force_env) == '1' and hasattr(args, 'force'):
        args.force = True
    
    # Check for non-interactive
    noninteractive_env = env_var.replace('ASSUME_YES', 'NONINTERACTIVE')
    if os.getenv(noninteractive_env) == '1' and hasattr(args, 'non_interactive'):
        args.non_interactive = True
    
    # Check config file settings
    if HAS_CONFIG:
        config = _get_config()
        if config:
            # Check tool-specific section
            tool_section = tool_name.lower().replace('-', '_')
            
            if hasattr(args, 'yes'):
                assume_yes = get_config_value(tool_section, 'assume_yes', False, config)
                auto_confirm = get_config_value(tool_section, 'auto_confirm', False, config)
                if assume_yes or auto_confirm:
                    args.yes = True
            
            if hasattr(args, 'force'):
                force = get_config_value(tool_section, 'force', False, config)
                if force:
                    args.force = True
            
            if hasattr(args, 'non_interactive'):
                non_interactive = get_config_value(tool_section, 'non_interactive', False, config)
                if non_interactive:
                    args.non_interactive = True


def get_tool_env_var(tool_name: str, suffix: str = "ASSUME_YES") -> str:
    """
    Get the standard environment variable name for a tool.
    
    Args:
        tool_name: Name of the tool
        suffix: Environment variable suffix (default: "ASSUME_YES")
        
    Returns:
        str: Environment variable name (e.g., TEXT_UNDO_ASSUME_YES)
    """
    return f"{tool_name.upper().replace('-', '_')}_{suffix}"


def print_non_interactive_help(tool_name: str, operations: List[str]) -> None:
    """
    Print helpful message about non-interactive mode options.
    
    Args:
        tool_name: Name of the tool
        operations: List of operations that can be automated
    """
    env_var = get_tool_env_var(tool_name)
    tool_section = tool_name.lower().replace('-', '_')
    print(f"\n{Colors.CYAN}Non-Interactive Mode Options:{Colors.END}")
    print(f"  - Use --yes flag to auto-confirm {', '.join(operations)}")
    print(f"  - Set {env_var}=1 environment variable")
    print(f"  - Add 'assume_yes = true' to .pytoolsrc [{tool_section}] section")
    print(f"  - Use --non-interactive flag for strict non-interactive mode")
    print(f"  - Use --force flag for high-risk operations")


# Export all public functions
__all__ = [
    'Colors',
    'PromptChoice',
    'is_interactive',
    'safe_input',
    'get_confirmation',
    'get_multi_choice',
    'get_numbered_selection',
    'get_multi_confirmation',
    'require_interactive',
    'check_auto_yes_env',
    'get_tool_env_var',
    'print_non_interactive_help',
]