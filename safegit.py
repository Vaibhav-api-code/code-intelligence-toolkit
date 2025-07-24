#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
SafeGIT - A protective wrapper around git to prevent AI disasters.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import subprocess
import argparse
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import shutil
import zipfile
import fcntl
import tempfile
import hashlib
import uuid

# Import our existing SafeGitCommands functionality
from safe_git_commands import SafeGitCommands, format_safety_report

# Import configuration system
from common_config import load_config, get_config_value

# -------- Cross-platform file locking & atomic write utilities --------
import contextlib

def _atomic_write(path: Path, data: str, mode: str = 'w', encoding: str = 'utf-8'):
    """Write to a temp file and atomically replace target."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + f'.tmp-{uuid.uuid4().hex}')
    with open(tmp, mode, encoding=encoding) as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)

@contextlib.contextmanager
def acquire_lock(lock_path: Path):
    """Cross-platform exclusive lock. Yields file handle."""
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, 'a+')
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl as _fcntl
            _fcntl.flock(fh.fileno(), _fcntl.LOCK_EX)
        yield fh
    finally:
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl as _fcntl
                _fcntl.flock(fh.fileno(), _fcntl.LOCK_UN)
        except Exception:
            pass
        fh.close()

from safegit_undo_stack import UndoStack


class SafeGitContext:
    """Manages git operation context for environment-aware safety rules."""
    
    def __init__(self):
        self.context_file = Path('.git/safegit-context.json')
        self.context = self._load_context()
    
    def _load_context(self) -> Dict:
        """Load context from .git/safegit-context.json."""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default context
        return {
            'environment': 'development',
            'mode': 'normal',
            'restrictions': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    def save_context(self):
        """Save current context to file with atomic write and locking."""
        self.context['updated_at'] = datetime.now().isoformat()
        
        # Ensure .git directory exists
        git_dir = Path('.git')
        if not git_dir.exists():
            return
        
        # Create temporary file in same directory for atomic rename
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.context_file.parent,
            prefix='.safegit-context-',
            suffix='.tmp'
        )
        
        try:
            # Write to temp file with exclusive lock
            with os.fdopen(temp_fd, 'w') as f:
                # Acquire exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(self.context, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is written to disk
                finally:
                    # Lock is automatically released when file is closed
                    pass
            
            # Atomic rename (works on POSIX systems)
            os.replace(temp_path, self.context_file)
            
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise e
    
    def set_environment(self, env: str):
        """Set the environment (development, staging, production)."""
        valid_envs = ['development', 'staging', 'production']
        if env not in valid_envs:
            raise ValueError(f"Invalid environment. Must be one of: {valid_envs}")
        
        self.context['environment'] = env
        self.save_context()
    
    def set_mode(self, mode: str):
        """Set the mode (normal, code-freeze, maintenance, paranoid)."""
        valid_modes = ['normal', 'code-freeze', 'maintenance', 'paranoid']
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        
        self.context['mode'] = mode
        self.save_context()
    
    def add_restriction(self, restriction: str):
        """Add a custom restriction."""
        if restriction not in self.context['restrictions']:
            self.context['restrictions'].append(restriction)
            self.save_context()
    
    def remove_restriction(self, restriction: str):
        """Remove a custom restriction."""
        if restriction in self.context['restrictions']:
            self.context['restrictions'].remove(restriction)
            self.save_context()
    
    def is_command_allowed(self, command: str) -> Tuple[bool, Optional[str]]:
        """Check if a command is allowed based on current context."""
        env = self.context['environment']
        mode = self.context['mode']
        
        # Production environment restrictions
        if env == 'production':
            # No force pushes in production
            if re.search(r'push.*--force', command) or re.search(r'push.*-f\b', command):
                return False, "Force push is not allowed in production environment"
            
            # No reset --hard in production
            if re.search(r'reset.*--hard', command):
                return False, "Hard reset is not allowed in production environment"
            
            # No clean -fdx in production
            if re.search(r'clean.*-[fdxX]', command):
                return False, "Force clean is not allowed in production environment"
            
            # No rebasing in production
            if command.startswith('rebase'):
                return False, "Rebasing is not allowed in production environment"
        
        # Code freeze mode restrictions
        if mode == 'code-freeze':
            # Only allow read operations and hotfix branches
            write_operations = ['push', 'commit', 'merge', 'rebase', 'reset', 'clean']
            for op in write_operations:
                if command.startswith(op):
                    # Allow hotfix branches
                    if 'hotfix' in command or 'HOTFIX' in command:
                        return True, None
                    return False, f"{op} operations are restricted during code freeze (except for hotfix branches)"
        
        # Paranoid mode restrictions
        if mode == 'paranoid':
            # Define safe commands allowed in paranoid mode
            safe_commands = [
                'status', 'log', 'diff', 'fetch', 'show', 'ls-files',
                'branch', 'tag', 'remote'
            ]
            
            # Extract the base command (first word)
            base_command = command.split()[0] if command.split() else ''
            
            # Check if it's a safe command
            if base_command not in safe_commands:
                return False, f"Command '{base_command}' is not allowed in paranoid mode. Only safe read-only commands are permitted: {', '.join(safe_commands)}"
            
            # Additional checks for specific commands
            if base_command == 'branch':
                # Don't allow branch deletion in paranoid mode
                if re.search(r'-[dD]|--delete', command):
                    return False, "Branch deletion is not allowed in paranoid mode"
            
            if base_command == 'tag':
                # Only allow listing tags, not creating/deleting
                if len(command.split()) > 1 and not any(flag in command for flag in ['-l', '--list', '-n']):
                    return False, "Only tag listing is allowed in paranoid mode"
            
            if base_command == 'remote':
                # Only allow listing remotes
                if len(command.split()) > 1 and command.split()[1] not in ['show', 'get-url', '-v', '--verbose']:
                    return False, "Only remote listing/viewing is allowed in paranoid mode"
        
        # Check custom restrictions
        for restriction in self.context['restrictions']:
            if restriction in command:
                return False, f"Command contains restricted pattern: {restriction}"
        
        return True, None
    
    def get_status(self) -> str:
        """Get current context status as a formatted string."""
        return f"""
SafeGit Context:
  Environment: {self.context['environment']}
  Mode: {self.context['mode']}
  Restrictions: {', '.join(self.context['restrictions']) if self.context['restrictions'] else 'None'}
  Last Updated: {self.context['updated_at']}
"""


class SafeGitWrapper:
    """Main wrapper class that intercepts git commands."""
    
    def __init__(self):
        """Initialize the wrapper with non-interactive support and config integration."""
        # Initialize flags with defaults
        self.non_interactive = False
        self.force_yes = False
        self.assume_yes = False
        self.dry_run = False
        
        # Load configuration from .pytoolsrc first
        self._load_config()
        
        # Check environment variables (can override config)
        self._check_environment()
        
        # Initialize other components
        self.safegit = SafeGitCommands()
        self.real_git = self._find_real_git()
        self.intercepted_count = 0
        self.context = SafeGitContext()
        self.log_file = Path('.git/safegit-log.json')
        self._ensure_log_directory()
        self.undo_stack = UndoStack()  # Multi-level undo support
    
    def _load_config(self):
        """Load configuration from .pytoolsrc file."""
        try:
            config = load_config()
            
            # Check [safegit] section first
            self.non_interactive = get_config_value('safegit', 'non_interactive', False, config)
            self.assume_yes = get_config_value('safegit', 'assume_yes', False, config)
            self.force_yes = get_config_value('safegit', 'force_yes', False, config)
            self.dry_run = get_config_value('safegit', 'dry_run', False, config)
            
            # Fall back to [defaults] section if not found in [safegit]
            if not config.has_section('safegit'):
                # Check defaults section for common flags
                self.assume_yes = get_config_value('defaults', 'yes', False, config) or self.assume_yes
                self.dry_run = get_config_value('defaults', 'dry_run', False, config) or self.dry_run
                
        except Exception as e:
            # Silently continue with defaults if config loading fails
            pass
    
    def _check_environment(self):
        """Check environment variables for non-interactive mode (overrides config)."""
        # Check for CI environment
        if any(os.environ.get(var) for var in ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 
                                                'GITLAB_CI', 'JENKINS_URL', 'TRAVIS']):
            self.non_interactive = True
            self.assume_yes = True
            
        # Check SafeGIT-specific environment variables (these override config)
        env_non_interactive = os.environ.get('SAFEGIT_NONINTERACTIVE', '').lower()
        if env_non_interactive in ['1', 'true', 'yes']:
            self.non_interactive = True
            
        env_assume_yes = os.environ.get('SAFEGIT_ASSUME_YES', '').lower()
        if env_assume_yes in ['1', 'true', 'yes']:
            self.assume_yes = True
            
        env_force_yes = os.environ.get('SAFEGIT_FORCE_YES', '').lower()
        if env_force_yes in ['1', 'true', 'yes']:
            self.force_yes = True
    
    def _get_user_input(self, prompt: str, valid_responses: List[str] = None, 
                       danger_level: str = 'low') -> str:
        """Get user input with non-interactive support."""
        if self.dry_run:
            print(f"[DRY RUN] Would prompt: {prompt}")
            return 'n'  # Always deny in dry-run mode
            
        if self.non_interactive or self.assume_yes or self.force_yes:
            # Determine automatic response based on danger level and flags
            
            # Special handling for typed confirmations
            if any(phrase in prompt for phrase in ['Type', 'type']):
                if self.force_yes:
                    # Extract expected response from prompt
                    if "Type 'PROCEED'" in prompt:
                        response = 'PROCEED'
                    elif "Type 'DELETE'" in prompt:
                        response = 'DELETE'
                    elif "Type 'YES'" in prompt:
                        response = 'YES'
                    elif "Type 'MIRROR PUSH'" in prompt:
                        response = 'MIRROR PUSH'
                    elif "Type 'DELETE REMOTE'" in prompt:
                        response = 'DELETE REMOTE'
                    elif "Type 'EXPIRE REFLOG'" in prompt:
                        response = 'EXPIRE REFLOG'
                    elif "Type 'DELETE REFERENCE'" in prompt:
                        response = 'DELETE REFERENCE'
                    elif "Type 'FORCE'" in prompt:
                        response = 'FORCE'
                    elif "Type 'I accept the risk'" in prompt:
                        response = 'I accept the risk'
                    elif "Type 'I understand the" in prompt:
                        response = 'I understand the protection risks' if 'protection' in prompt else 'I understand the risks'
                    elif "Type the branch name" in prompt:
                        # For branch name confirmation, we'd need to parse it from context
                        print(f"\n❌ ERROR: Branch name confirmation requires manual input")
                        print(f"   Prompt was: {prompt}")
                        sys.exit(1)
                    else:
                        print(f"\n❌ ERROR: Unknown typed confirmation in non-interactive mode")
                        print(f"   Prompt was: {prompt}")
                        sys.exit(1)
                    print(f"[AUTO-CONFIRM] {prompt} {response}")
                    return response
                else:
                    print(f"\n❌ ERROR: Typed confirmation requires --force-yes flag")
                    print(f"   Prompt was: {prompt}")
                    sys.exit(1)
            
            # Yes/No prompts
            if '[Y/n]' in prompt or '[y/N]' in prompt:
                if danger_level == 'high' and not self.force_yes:
                    print(f"\n❌ ERROR: High-risk operation requires --force-yes flag")
                    print(f"   Prompt was: {prompt}")
                    sys.exit(1)
                elif danger_level == 'medium' and not (self.assume_yes or self.force_yes):
                    print(f"\n❌ ERROR: Medium-risk operation requires --yes or --force-yes flag")
                    print(f"   Prompt was: {prompt}")
                    sys.exit(1)
                else:
                    # Default to 'y' for Yes/No when flags allow
                    response = 'y'
                    print(f"[AUTO-YES] {prompt} {response}")
                    return response
            
            # Multiple choice [1/2/3]
            if '[1/2/3]' in prompt:
                if self.assume_yes or self.force_yes:
                    response = '1'  # Default to first (usually safest) option
                    print(f"[AUTO-SELECT] {prompt} {response}")
                    return response
                else:
                    print(f"\n❌ ERROR: Multiple choice requires --yes or --force-yes flag")
                    print(f"   Prompt was: {prompt}")
                    sys.exit(1)
            
            # Unknown prompt type
            print(f"\n❌ ERROR: Unhandled prompt type in non-interactive mode")
            print(f"   Prompt was: {prompt}")
            sys.exit(1)
        
        # Interactive mode - normal input
        return input(prompt)
    
    # Dangerous command patterns that must be intercepted
    DANGEROUS_PATTERNS = [
        # git reset --hard
        (r'^reset\s+.*--hard', 'reset_hard'),
        # git clean with force flags
        (r'^clean\s+.*-[fdxX]', 'clean_force'),
        # git checkout with force or paths
        (r'^checkout\s+.*(-f|--force)', 'checkout_force'),
        (r'^checkout\s+\.', 'checkout_dot'),
        (r'^checkout\s+--\s+', 'checkout_path'),
        # history rewrite & ref updates
        (r'^rebase(\s|$)', 'rebase'),
        (r'^update-ref\s+.*-d', 'update_ref_delete'),
        (r'^(filter-branch|filter-repo)(\s|$)', 'filter_branch'),
        (r'^replace(\s|$)', 'replace_ref'),
        (r'^notes\s+prune', 'notes_prune'),
        # remote destructive pushes
        (r'^push\s+.*--force(?!-with-lease)', 'push_force'),
        (r'^push\s+.*--mirror', 'push_mirror'),
        (r'^push\s+.*--delete', 'push_delete'),
        # working tree destructive
        (r'^worktree\s+remove\s+.*--force', 'worktree_remove_force'),
        (r'^sparse-checkout\s+set', 'sparse_checkout_set'),
        # stash destruction
        (r'^stash\s+(drop|clear)', 'stash_drop_clear'),
        # gc/prune
        (r'^gc\s+.*--prune', 'gc_prune'),
        (r'^reflog\s+expire', 'reflog_expire'),
        # submodules / lfs
        (r'^submodule\s+deinit', 'submodule_deinit'),
        (r'^lfs\s+prune', 'lfs_prune'),
        # git branch -D
        (r'^branch\s+.*-D', 'branch_delete_force'),
        (r'^branch\s+.*--delete\s+--force', 'branch_delete_force'),
        # git commit --amend on public branches
        (r'^commit\s+.*--amend', 'commit_amend'),
        # git merge with strategy options that can be destructive
        (r'^merge\s+.*--strategy=ours', 'merge_ours'),
        # git reflog expire (enhanced)
        (r'^reflog\s+expire\s+.*--expire-unreachable', 'reflog_expire_unreachable'),
        (r'^reflog\s+expire\s+.*--all', 'reflog_expire_all'),
        (r'^reflog\s+expire', 'reflog_expire'),
        # git switch --discard-changes
        (r'^switch\s+.*--discard-changes', 'switch_discard_changes'),
        # git worktree remove --force
        (r'^worktree\s+remove\s+.*--force', 'worktree_remove_force'),
        (r'^worktree\s+remove\s+.*-f\b', 'worktree_remove_force'),
        # git update-ref -d (delete references)
        (r'^update-ref\s+.*-d', 'update_ref_delete'),
        (r'^update-ref\s+.*--delete', 'update_ref_delete'),
        # git cherry-pick --abort
        (r'^cherry-pick\s+.*--abort', 'cherry_pick_abort'),
        # git am --abort
        (r'^am\s+.*--abort', 'am_abort'),
        # git notes operations
        (r'^notes\s+prune', 'notes_prune'),
        # git lfs operations
        (r'^lfs\s+prune', 'lfs_prune'),
        # git submodule operations
        (r'^submodule\s+deinit', 'submodule_deinit'),
        # git sparse-checkout operations
        (r'^sparse-checkout\s+set', 'sparse_checkout_set'),
        (r'^sparse-checkout\s+reapply', 'sparse_checkout_reapply'),
    ]
    
    
    def _find_real_git(self) -> str:
        """Find the real git executable."""
        # First check for git.real (in case we're in wrapper mode)
        git_real_paths = ['/usr/bin/git.real', '/usr/local/bin/git.real']
        for path in git_real_paths:
            if os.path.exists(path):
                return path
        
        # Otherwise find regular git
        try:
            result = subprocess.run(['which', 'git'], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return 'git'  # Fallback
    
    def _detect_repository_info(self) -> Dict:
        """Detect repository characteristics for safety adjustments."""
        repo_info = {
            'is_bare': False,
            'has_worktrees': False,
            'has_submodules': False,
            'uses_lfs': False,
            'is_shallow': False,
            'remote_count': 0
        }
        
        try:
            # Check if bare repository
            result = subprocess.run(
                [self.real_git, 'rev-parse', '--is-bare-repository'],
                capture_output=True, text=True
            )
            repo_info['is_bare'] = result.stdout.strip() == 'true'
            
            # Check for worktrees
            result = subprocess.run(
                [self.real_git, 'worktree', 'list'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                worktree_count = len(result.stdout.strip().split('\n'))
                repo_info['has_worktrees'] = worktree_count > 1
            
            # Check for submodules
            repo_info['has_submodules'] = os.path.exists('.gitmodules')
            
            # Check for LFS
            result = subprocess.run(
                [self.real_git, 'lfs', 'ls-files'],
                capture_output=True, text=True
            )
            repo_info['uses_lfs'] = bool(result.stdout.strip()) if result.returncode == 0 else False
            
            # Check if shallow clone
            result = subprocess.run(
                [self.real_git, 'rev-parse', '--is-shallow-repository'],
                capture_output=True, text=True
            )
            repo_info['is_shallow'] = result.stdout.strip() == 'true'
            
            # Count remotes
            result = subprocess.run(
                [self.real_git, 'remote'],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                repo_info['remote_count'] = len(result.stdout.strip().split('\n'))
            
        except Exception as e:
            print(f"Warning: Could not detect repository info: {e}", file=sys.stderr)
        
        return repo_info
    
    def _check_branch_protection(self, branch: str, remote: str = 'origin') -> Dict:
        """Check if branch has protection rules (GitHub/GitLab/Bitbucket)."""
        protection_info = {
            'protected': False,
            'push_restrictions': False,
            'require_pull_request': False,
            'platform': None,
            'message': ''
        }
        
        # Try to detect platform from remote URL
        try:
            result = subprocess.run(
                [self.real_git, 'remote', 'get-url', remote],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                remote_url = result.stdout.strip()
                if 'github.com' in remote_url:
                    protection_info['platform'] = 'GitHub'
                elif 'gitlab' in remote_url:
                    protection_info['platform'] = 'GitLab'
                elif 'bitbucket' in remote_url:
                    protection_info['platform'] = 'Bitbucket'
        except:
            pass
        
        # Check if this is a commonly protected branch
        protected_branch_patterns = [
            'main', 'master', 'develop', 'development',
            'staging', 'production', 'release', 'stable'
        ]
        
        if any(pattern in branch.lower() for pattern in protected_branch_patterns):
            protection_info['protected'] = True
            protection_info['message'] = f"Branch '{branch}' appears to be a protected branch"
            
            # For main/master, assume strict protection
            if branch in ['main', 'master']:
                protection_info['push_restrictions'] = True
                protection_info['require_pull_request'] = True
                protection_info['message'] += " with likely push restrictions"
        
        return protection_info
    
    def _check_upstream_divergence(self, branch: str) -> Dict:
        """Check detailed divergence between local and upstream branch."""
        divergence_info = {
            'has_upstream': False,
            'ahead': 0,
            'behind': 0,
            'diverged': False,
            'common_ancestor': None,
            'conflict_risk': 'low',
            'details': []
        }
        
        try:
            # Check if branch has upstream
            upstream_result = subprocess.run(
                [self.real_git, 'rev-parse', '--abbrev-ref', f'{branch}@{{upstream}}'],
                capture_output=True, text=True
            )
            
            if upstream_result.returncode != 0:
                divergence_info['details'].append("No upstream branch configured")
                return divergence_info
            
            upstream = upstream_result.stdout.strip()
            divergence_info['has_upstream'] = True
            
            # Get ahead/behind counts
            count_result = subprocess.run(
                [self.real_git, 'rev-list', '--left-right', '--count', f'{upstream}...HEAD'],
                capture_output=True, text=True
            )
            
            if count_result.returncode == 0:
                counts = count_result.stdout.strip().split()
                if len(counts) == 2:
                    divergence_info['behind'] = int(counts[0])
                    divergence_info['ahead'] = int(counts[1])
                    divergence_info['diverged'] = (divergence_info['behind'] > 0 and 
                                                   divergence_info['ahead'] > 0)
            
            # Get common ancestor
            merge_base_result = subprocess.run(
                [self.real_git, 'merge-base', 'HEAD', upstream],
                capture_output=True, text=True
            )
            
            if merge_base_result.returncode == 0:
                divergence_info['common_ancestor'] = merge_base_result.stdout.strip()[:8]
            
            # Assess conflict risk
            if divergence_info['diverged']:
                if divergence_info['behind'] > 10 or divergence_info['ahead'] > 10:
                    divergence_info['conflict_risk'] = 'high'
                elif divergence_info['behind'] > 5 or divergence_info['ahead'] > 5:
                    divergence_info['conflict_risk'] = 'medium'
                else:
                    divergence_info['conflict_risk'] = 'low'
                
                divergence_info['details'].append(
                    f"Branch has diverged: {divergence_info['ahead']} ahead, "
                    f"{divergence_info['behind']} behind {upstream}"
                )
            elif divergence_info['behind'] > 0:
                divergence_info['details'].append(
                    f"Branch is {divergence_info['behind']} commits behind {upstream}"
                )
            elif divergence_info['ahead'] > 0:
                divergence_info['details'].append(
                    f"Branch is {divergence_info['ahead']} commits ahead of {upstream}"
                )
            else:
                divergence_info['details'].append(f"Branch is up to date with {upstream}")
            
            # Check for uncommitted changes that would conflict
            status_result = subprocess.run(
                [self.real_git, 'status', '--porcelain'],
                capture_output=True, text=True
            )
            
            if status_result.stdout.strip():
                modified_count = len(status_result.stdout.strip().split('\n'))
                divergence_info['details'].append(
                    f"Warning: {modified_count} uncommitted changes present"
                )
                if divergence_info['conflict_risk'] == 'low':
                    divergence_info['conflict_risk'] = 'medium'
            
        except Exception as e:
            divergence_info['details'].append(f"Error checking divergence: {str(e)}")
        
        return divergence_info
    
    def _ensure_log_directory(self):
        """Ensure the log directory exists."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _log_operation(self, command: str, action: str, result: str = 'pending', metadata: Dict = None):
        """Log operations with non-interactive context."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'action': action,
            'result': result,
            'mode': 'non-interactive' if self.non_interactive else 'interactive',
            'flags': {
                'assume_yes': self.assume_yes,
                'force_yes': self.force_yes,
                'dry_run': self.dry_run
            },
            'metadata': metadata or {}
        }
        
        # Add CI context if applicable
        if self.non_interactive:
            log_entry['ci_detected'] = any(os.environ.get(var) for var in 
                                          ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL'])
        
        # Atomic write to log
        lock_path = self.log_file.with_suffix('.lock')
        with acquire_lock(lock_path):
            logs = []
            if self.log_file.exists():
                try:
                    with open(self.log_file, 'r') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            logs.append(log_entry)
            
            # Keep last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            _atomic_write(self.log_file, json.dumps(logs, indent=2, default=str))
    
    def _log_interception(self, command: List[str], action: str, details: Dict):
        """Log intercepted commands for audit with atomic append and locking."""
        log_entry = {
            'id': str(uuid.uuid4()),  # Unique ID for each entry
            'timestamp': datetime.now().isoformat(),
            'command': ' '.join(command),
            'action': action,
            'cwd': os.getcwd(),
            'user': os.environ.get('USER', 'unknown'),
            'details': details,
            'stash_ref': details.get('stash_ref')  # Include stash reference if present
        }
        
        # Use file locking for concurrent append operations
        max_retries = 5
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Open in append mode with exclusive lock
                with open(self.log_file, 'a') as f:
                    # Try to acquire exclusive lock (non-blocking)
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    try:
                        # Write the log entry
                        f.write(json.dumps(log_entry) + '\n')
                        f.flush()
                        os.fsync(f.fileno())  # Ensure written to disk
                        break  # Success, exit retry loop
                    finally:
                        # Release lock
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        
            except IOError as e:
                if e.errno == 11:  # Resource temporarily unavailable (lock held)
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        # Last attempt failed, log to stderr
                        print(f"Warning: Could not write to log file (locked): {e}", file=sys.stderr)
                else:
                    raise
    
    def _is_dangerous_command(self, args: List[str]) -> Optional[Tuple[str, str]]:
        """Check if a git command is dangerous."""
        if not args:
            return None
        
        # Join args to form the command string (excluding 'git' if present)
        if args[0] == 'git':
            command_str = ' '.join(args[1:])
        else:
            command_str = ' '.join(args)
        
        # Check against dangerous patterns
        for pattern, danger_type in self.DANGEROUS_PATTERNS:
            if re.match(pattern, command_str, re.IGNORECASE):
                return (command_str, danger_type)
        
        return None
    
    def _handle_reset_hard(self, args: List[str]) -> int:
        """Handle git reset --hard interception."""
        print("🛡️  SafeGIT: Intercepting dangerous 'git reset --hard' command")
        print()
        
        # Extract files/paths from the command
        files = []
        commit = "HEAD"
        
        for i, arg in enumerate(args):
            if arg == '--hard':
                continue
            elif arg == 'reset':
                continue
            elif arg.startswith('-'):
                continue
            elif i > 0 and args[i-1] in ['reset', '--hard']:
                commit = arg
            else:
                files.append(arg)
        
        # If no specific files, assume all files
        if not files:
            files = ['.']
        
        # Check safety
        safety_report = self.safegit.check_reset_safety(files)
        format_safety_report(safety_report)
        
        if self.dry_run:
            print("\n🔍 DRY-RUN: Showing what would happen:")
            print(f"   • Would reset to: {commit}")
            print(f"   • Would affect: {len(safety_report.get('files', []))} file(s)")
            print(f"   • Total changes that would be lost: {safety_report.get('total_changes', 0)} lines")
            
            if not safety_report['safe']:
                print("\n⚠️  DRY-RUN: This operation would lose uncommitted changes!")
                print("   In real execution, SafeGIT would:")
                print("   1. Offer to use 'git reset --keep' instead")
                print("   2. Create a backup stash before proceeding")
                print("   3. Show reflog recovery instructions after")
            else:
                print("\n✅ DRY-RUN: Operation would be safe to proceed")
            
            return 0
        
        if not safety_report['safe']:
            print("\n⚠️  This operation would lose uncommitted changes!")
            print("\n💡 Alternative: Use 'git reset --keep' instead of '--hard'")
            print("   • --keep preserves uncommitted changes in your working tree")
            print("   • --hard discards ALL uncommitted changes permanently")
            print("\nYou have three options:")
            print("  1. Use 'git reset --keep' (safer - preserves uncommitted changes)")
            print("  2. Create a backup and proceed with --hard")
            print("  3. Cancel the operation")
            
            response = self._get_user_input("\nChoose an option [1/2/3] (default: 1): ", 
                                               danger_level='medium').strip() or '1'
            
            if response == '1':
                # Use --keep instead
                print("\n✅ Using safer 'git reset --keep' instead...")
                keep_args = [arg if arg != '--hard' else '--keep' for arg in args]
                result = self._run_git_command(keep_args)
                if result == 0:
                    # Show reflog recovery hint
                    self._show_reflog_hint('reset', commit)
                return result
            elif response == '2':
                print("\n🔒 Creating backup and performing safe reset...")
                # Create timestamp for stash message to match what safe_reset will use
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filenames = ", ".join([os.path.basename(f) for f in files[:3]])
                if len(files) > 3:
                    filenames += f" (+{len(files)-3} more)"
                stash_message = f"SAFEGIT-BACKUP-RESET - {timestamp} - {filenames}"
                
                success = self.safegit.safe_reset(files, mode='hard', backup=True)
                if success:
                    # Log the stash creation with stash reference
                    self._log_interception(args, 'reset_hard_stash_created', {
                        'stash_message': stash_message,
                        'stash_ref': 'stash@{0}',  # Most recent stash
                        'files': files
                    })
                    # Push to undo stack
                    self.undo_stack.push_operation({
                        'type': 'reset_hard',
                        'command': args,
                        'description': f'Hard reset to {commit}',
                        'backups': {'stash_ref': 'stash@{0}', 'stash_message': stash_message}
                    })
                    # Show reflog recovery hint
                    self._show_reflog_hint('reset', commit)
                return 0 if success else 1
            else:
                print("\n❌ Operation cancelled.")
                return 1
        else:
            # Even if "safe", still require confirmation for hard reset
            print(f"\n⚠️  Reset --hard will discard {safety_report.get('total_changes', 0)} lines of changes")
            print("   While this appears safe, --hard is permanently destructive.")
            print("\n💡 Safer option: Use 'git reset --keep' to preserve uncommitted changes")
            
            response = self._get_user_input("\nProceed with --hard anyway? Type 'PROCEED' to confirm: ", 
                                               danger_level='high')
            
            if response == 'PROCEED':
                print("\n✅ Proceeding with hard reset...")
                
                # Push to undo stack before executing
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
                self.undo_stack.push_operation({
                    'type': 'reset_hard',
                    'command': args,
                    'description': f'Hard reset to {commit}',
                    'backups': {}
                })
                
                result = self._run_git_command(args)
                if result == 0:
                    # Show reflog recovery hint after successful reset
                    self._show_reflog_hint('reset', commit)
                return result
            else:
                print("\n❌ Operation cancelled.")
                return 1
    
    def _handle_clean_force(self, args: List[str]) -> int:
        """Handle git clean -f interception."""
        print("🛡️  SafeGIT: Intercepting dangerous 'git clean' command")
        print()
        
        # Check what would be deleted
        safety_report = self.safegit.check_clean_safety()
        format_safety_report(safety_report)
        
        if self.dry_run:
            print("\n🔍 DRY-RUN: Showing what would happen:")
            print(f"   • Would delete: {safety_report.get('total_files', 0)} file(s)")
            print(f"   • Total size: {self.safegit._format_size(safety_report.get('total_size', 0))}")
            
            categories = safety_report.get('categories', {})
            if categories:
                print("\n   File categories that would be deleted:")
                for category, info in categories.items():
                    if info.get('count', 0) > 0:
                        print(f"   • {category}: {info['count']} files")
            
            if not safety_report['safe']:
                print("\n⚠️  DRY-RUN: This operation would permanently delete important files!")
                print("   In real execution, SafeGIT would:")
                print("   1. Offer to create a zip backup of all files")
                print("   2. Show exact files to be deleted")
                print("   3. Remind that git clean bypasses recycle bin")
            else:
                print("\n✅ DRY-RUN: Operation would be safe to proceed")
            
            return 0
        
        if not safety_report['safe']:
            print("\n⚠️  This operation would permanently delete untracked files!")
            print("📌 Remember: git clean bypasses the recycle bin - files are gone forever!")
            response = self._get_user_input("\nDo you want to create a backup and proceed safely? [Y/n]: ",
                                               danger_level='medium')
            
            if response.lower() != 'n':
                print("\n🔒 Creating backup and performing safe clean...")
                # Extract dry-run flag if present
                dry_run = '--dry-run' in args or '-n' in args
                success = self.safegit.safe_clean(backup=True, dry_run=dry_run, force=True)
                if success and not dry_run:
                    # Show recovery hint for clean operations
                    self._show_reflog_hint('clean')
                return 0 if success else 1
            else:
                print("\n❌ Operation cancelled.")
                return 1
        else:
            # Even if "safe", still require confirmation for clean
            total_files = safety_report.get('total_files', 0)
            total_size = self.safegit._format_size(safety_report.get('total_size', 0))
            
            print(f"\n⚠️  Git clean will permanently delete {total_files} untracked files ({total_size})")
            print("   Files deleted by git clean CANNOT be recovered!")
            print("   They bypass the Recycle Bin/Trash!")
            
            print("\n💡 Safer alternatives:")
            print("   1. git clean -n (see what would be deleted first)")
            print("   2. Create a backup zip before cleaning")
            
            response = self._get_user_input(f"\nPermanently delete {total_files} files? Type 'DELETE' to confirm: ",
                                               danger_level='high')
            
            if response == 'DELETE':
                print(f"\n🗑️  Permanently deleting {total_files} files...")
                
                # Push to undo stack before executing (with backup info)
                self.undo_stack.push_operation({
                    'type': 'clean_force',
                    'command': args,
                    'description': f'Clean deleted {total_files} files ({total_size})',
                    'backups': {'note': 'Files permanently deleted - no backup possible'}
                })
                
                result = self._run_git_command(args)
                if result == 0 and not ('--dry-run' in args or '-n' in args):
                    # Show recovery hint for clean operations
                    self._show_reflog_hint('clean')
                return result
            else:
                print("\n❌ Operation cancelled.")
                return 1
    
    def _handle_checkout_force(self, args: List[str]) -> int:
        """Handle git checkout -f or checkout . interception."""
        print("🛡️  SafeGIT: Intercepting dangerous 'git checkout' command")
        print()
        
        # Check for uncommitted changes
        result = subprocess.run([self.real_git, 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if self.dry_run:
            if result.stdout.strip():
                changes = result.stdout.strip().split('\n')
                print("\n🔍 DRY-RUN: Showing what would happen:")
                print(f"   • Would discard changes in: {len(changes)} file(s)")
                print("\n   Files with changes that would be lost:")
                for change in changes[:5]:
                    print(f"   {change}")
                if len(changes) > 5:
                    print(f"   ... and {len(changes) - 5} more")
                
                print("\n⚠️  DRY-RUN: This operation would lose uncommitted changes!")
                print("   In real execution, SafeGIT would:")
                print("   1. Offer to stash changes before checkout")
                print("   2. Create automatic backup stash")
                print("   3. Show stash recovery command after")
            else:
                print("\n🔍 DRY-RUN: No uncommitted changes detected")
                print("✅ DRY-RUN: Operation would be safe to proceed")
            
            return 0
        
        if result.stdout.strip():
            print("⚠️  You have uncommitted changes that would be lost!")
            print("\nUncommitted files:")
            lines = result.stdout.strip().splitlines()
            for line in lines[:10]:
                print(f"  {line}")
            extra = len(lines) - 10
            if extra > 0:
                print(f"  ... and {extra} more")
            
            response = self._get_user_input("\nDo you want to stash changes and proceed safely? [Y/n]: ",
                                               danger_level='medium')
            
            if response.lower() != 'n':
                print("\n🔒 Stashing changes...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stash_message = f'SAFEGIT-CHECKOUT-BACKUP - {timestamp}'
                stash_result = subprocess.run(
                    [self.real_git, 'stash', 'push', '-m', stash_message],
                    capture_output=True,
                    text=True
                )
                if stash_result.returncode == 0:
                    print("✅ Changes stashed successfully")
                    print("   To recover: git stash pop")
                    # Log the stash creation with stash reference
                    self._log_interception(args, 'checkout_stash_created', {
                        'stash_message': stash_message,
                        'stash_ref': 'stash@{0}'  # Most recent stash
                    })
                    return self._run_git_command(args)
                else:
                    print("❌ Failed to stash changes")
                    return 1
            else:
                print("\n❌ Operation cancelled.")
                return 1
        else:
            # No uncommitted changes, but still dangerous
            print("\n⚠️  No uncommitted changes detected, but this is still a dangerous operation")
            print("   Checkout with --force can have unexpected side effects")
            
            response = self._get_user_input("\nProceed with force checkout? Type 'PROCEED' to confirm: ",
                                               danger_level='high')
            
            if response == 'PROCEED':
                print("\n✅ Proceeding with force checkout...")
                return self._run_git_command(args)
            else:
                print("\n❌ Operation cancelled.")
                return 1
    
    def _handle_push_force(self, args: List[str]) -> int:
        """Handle git push --force interception."""
        print("🛡️  SafeGIT: Intercepting dangerous 'git push --force' command")
        print()
        
        # Try to determine the branch
        branch_result = subprocess.run([self.real_git, 'branch', '--show-current'], 
                                     capture_output=True, text=True)
        current_branch = branch_result.stdout.strip()
        
        # Check if this is a critical branch
        is_critical_branch = current_branch in ['main', 'master', 'develop', 'production']
        
        # Perform enhanced safety checks
        protection_info = self._check_branch_protection(current_branch)
        divergence_info = self._check_upstream_divergence(current_branch)
        
        if self.dry_run:
            print("\n🔍 DRY-RUN: Showing what would happen:")
            print(f"   • Would force push branch: {current_branch}")
            
            if is_critical_branch:
                print(f"   • ⚠️  CRITICAL: This is a protected branch!")
            
            if protection_info['protected']:
                print(f"   • 🔒 Branch has protection rules detected!")
                if protection_info['push_restrictions']:
                    print(f"   • 🚫 Push restrictions active")
                if protection_info['require_pull_request']:
                    print(f"   • 📋 Requires pull request workflow")
            
            # Enhanced divergence analysis
            if divergence_info['has_upstream']:
                if divergence_info['ahead'] > 0 and divergence_info['behind'] > 0:
                    print(f"   • ⚠️  DANGEROUS: Local and remote have diverged!")
                    print(f"   • Ahead by {divergence_info['ahead']} commits, behind by {divergence_info['behind']} commits")
                    print("   • Would OVERWRITE remote commits")
                    if divergence_info['conflict_risk'] == 'high':
                        print("   • 🔥 HIGH CONFLICT RISK - Merge conflicts likely")
                elif divergence_info['behind'] > 0:
                    print(f"   • ⚠️  Local is {divergence_info['behind']} commits behind remote")
                    print("   • Would lose remote commits")
                elif divergence_info['ahead'] > 0:
                    print(f"   • ✅ Local is {divergence_info['ahead']} commits ahead")
                    print("   • Safer to push (no remote overwrites)")
            else:
                print("   • ⚠️  No upstream tracking - cannot verify safety")
            
            print("\n⚠️  DRY-RUN: Force push would rewrite remote history!")
            print("   In real execution, SafeGIT would:")
            print("   1. Convert to --force-with-lease by default")
            print("   2. Require extra confirmation for critical branches")
            print("   3. Show detailed divergence analysis")
            print("   4. Check branch protection rules")
            
            return 0
        
        print("⚠️  CONVERTING TO SAFER --force-with-lease BY DEFAULT")
        print()
        print("📚 Why --force-with-lease is safer:")
        print("   • It checks if the remote branch has new commits you haven't seen")
        print("   • Prevents accidentally overwriting teammates' work")
        print("   • Only overwrites if your local view matches the remote")
        print("   • Recommended best practice for force pushing")
        
        print(f"\n📍 Current branch: {current_branch}")
        
        if is_critical_branch:
            print(f"🚨 CRITICAL: This is a protected branch!")
        
        if protection_info['protected']:
            print(f"🔒 BRANCH PROTECTION DETECTED!")
            if protection_info['push_restrictions']:
                print("   • This branch has push restrictions")
                print("   • Force push may be blocked by the remote")
            if protection_info['require_pull_request']:
                print("   • Branch requires pull request workflow")
                print("   • Direct push may violate team policy")
        
        # Show detailed divergence analysis
        if divergence_info['has_upstream']:
            if divergence_info['ahead'] > 0 and divergence_info['behind'] > 0:
                print(f"\n⚠️  DIVERGENCE WARNING:")
                print(f"   • Local is {divergence_info['ahead']} ahead, {divergence_info['behind']} behind")
                print(f"   • This will overwrite {divergence_info['behind']} remote commits")
                if divergence_info['conflict_risk'] == 'high':
                    print("   • 🔥 HIGH CONFLICT RISK - Check for merge conflicts first")
                elif divergence_info['conflict_risk'] == 'medium':
                    print("   • ⚠️  Medium conflict risk - Review changes carefully")
            elif divergence_info['behind'] > 0:
                print(f"\n⚠️  BEHIND WARNING:")
                print(f"   • You're {divergence_info['behind']} commits behind remote")
                print(f"   • This would lose remote work!")
            elif divergence_info['ahead'] > 0:
                print(f"\n✅ AHEAD STATUS:")
                print(f"   • You're {divergence_info['ahead']} commits ahead")
                print(f"   • Safer to push (no remote work will be lost)")
        else:
            print("\n⚠️  NO UPSTREAM: Cannot verify divergence safety")
        
        print("\n🔐 SafeGIT will use --force-with-lease for safety")
        print("   This will fail if the remote has changes you haven't pulled")
        
        # Enhanced confirmation logic based on risk factors
        if protection_info['protected'] or (divergence_info['behind'] > 0 and divergence_info['ahead'] > 0):
            print("\n🔴 HIGH RISK FORCE PUSH DETECTED!")
            if protection_info['protected']:
                print("   • Branch has protection rules")
            if divergence_info['behind'] > 0 and divergence_info['ahead'] > 0:
                print(f"   • Would overwrite {divergence_info['behind']} remote commits")
            print("\n⚠️  This operation requires extra confirmation.")
            
            confirm_risk = self._get_user_input("\nType 'I accept the risk' to proceed with --force-with-lease: ",
                                                    danger_level='high')
            if confirm_risk != 'I accept the risk':
                print("\n❌ Operation cancelled.")
                return 1
        
        # Ask for confirmation for the safer option
        response = self._get_user_input(f"\nProceed with safer --force-with-lease? [Y/n]: ",
                                           danger_level='medium')
        
        if response.lower() in ['n', 'no']:
            print("\n⚠️  You declined the safer option.")
            print("   If you REALLY need raw --force (NOT RECOMMENDED):")
            print("   • It will overwrite ALL remote changes")
            print("   • You could lose teammates' commits")
            print("   • There is NO safety check")
            
            # Enhanced confirmation for raw force
            if protection_info['protected']:
                print(f"\n🚨🚨🚨 TRIPLE WARNING: Force pushing to protected branch '{current_branch}'!")
                print("   • This may violate branch protection rules")
                print("   • Remote may reject the push")
                print("   • Team policies may be violated")
                
                confirm1 = self._get_user_input("\nType 'I understand the protection risks' to continue: ",
                                                 danger_level='high')
                if confirm1 != 'I understand the protection risks':
                    print("\n❌ Operation cancelled.")
                    return 1
                
                confirm2 = self._get_user_input("Type the branch name to confirm protected branch force push: ",
                                                 danger_level='high')
                if confirm2 != current_branch:
                    print("\n❌ Operation cancelled - branch name mismatch.")
                    return 1
            elif is_critical_branch:
                print(f"\n🚨🚨 DOUBLE WARNING: Force pushing to '{current_branch}' is EXTREMELY DANGEROUS!")
                confirm1 = self._get_user_input("\nType 'I understand the risks' to continue: ",
                                                 danger_level='high')
                if confirm1 != 'I understand the risks':
                    print("\n❌ Operation cancelled.")
                    return 1
                
                confirm2 = self._get_user_input("Type the branch name to confirm force push: ",
                                                 danger_level='high')
                if confirm2 != current_branch:
                    print("\n❌ Operation cancelled - branch name mismatch.")
                    return 1
            else:
                dangerous_confirm = self._get_user_input("\nAre you ABSOLUTELY SURE you want raw --force? Type 'FORCE': ",
                                                          danger_level='high')
                if dangerous_confirm != 'FORCE':
                    print("\n❌ Operation cancelled.")
                    return 1
            
            # Log the dangerous raw force push with detailed context
            self._log_interception(args, 'force_push_raw_allowed', {
                'branch': current_branch,
                'protected': protection_info['protected'],
                'diverged': divergence_info['behind'] > 0,
                'risk_level': 'critical' if protection_info['protected'] else 'high'
            })
            print("\n⚠️  Proceeding with raw --force as requested...")
            return self._run_git_command(args)
        
        # Default path: convert to --force-with-lease
        # Replace --force with --force-with-lease in the args
        safe_args = []
        for arg in args:
            if arg == '--force' or arg == '-f':
                safe_args.append('--force-with-lease')
            else:
                safe_args.append(arg)
        
        # Log the safer operation with enhanced context
        self._log_interception(args, 'force_push_converted_to_lease', {
            'branch': current_branch,
            'original_args': args,
            'safe_args': safe_args,
            'protected': protection_info['protected'],
            'ahead': divergence_info['ahead'],
            'behind': divergence_info['behind'],
            'risk_level': 'high' if (protection_info['protected'] or divergence_info['behind'] > 0) else 'medium'
        })
        
        print("\n✅ Using --force-with-lease for safety")
        print(f"   Command: git {' '.join(safe_args)}")
        
        return self._run_git_command(safe_args)
    
    def _handle_stash_clear(self, args: List[str], danger_type: str) -> int:
        """Handle git stash clear/drop --all with backup."""
        print("🛡️  SafeGIT: Intercepting dangerous stash operation")
        print()
        print("⚠️  WARNING: This will delete ALL your stashes permanently!")
        
        # List all stashes
        result = subprocess.run([self.real_git, 'stash', 'list'], 
                              capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("\n✅ No stashes found - nothing to clear.")
            print("⚠️  Command would still execute 'git stash clear'")
            
            response = self._get_user_input("\nExecute stash clear anyway? [y/N]: ",
                                               danger_level='medium')
            if response.lower() == 'y':
                return self._run_git_command(args)
            else:
                print("❌ Operation cancelled.")
                return 1
        
        stashes = result.stdout.strip().split('\n')
        print(f"\n📋 Found {len(stashes)} stash(es) that would be deleted:")
        for stash in stashes[:5]:
            print(f"   {stash}")
        if len(stashes) > 5:
            print(f"   ... and {len(stashes) - 5} more")
        
        if self.dry_run:
            print("\n🔍 DRY-RUN: Would backup all stashes before deletion")
            print("   Backup location: git_stash_backup_[timestamp].txt")
            return 0
        
        print("\n💡 SafeGIT can backup all stashes before deletion")
        response = self._get_user_input("Create backup and proceed? [Y/n]: ",
                                           danger_level='medium')
        
        if response.lower() != 'n':
            # Create backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"git_stash_backup_{timestamp}.txt"
            
            print(f"\n🔒 Creating backup: {backup_file}")
            with open(backup_file, 'w') as f:
                f.write(f"Git Stash Backup - {datetime.now()}\n")
                f.write("=" * 60 + "\n\n")
                
                for i, stash in enumerate(stashes):
                    f.write(f"{stash}\n")
                    f.write("-" * 40 + "\n")
                    
                    # Get stash content
                    show_result = subprocess.run(
                        [self.real_git, 'stash', 'show', '-p', f'stash@{{{i}}}'],
                        capture_output=True, text=True
                    )
                    f.write(show_result.stdout)
                    f.write("\n" + "=" * 60 + "\n\n")
            
            print(f"✅ Backup created: {backup_file}")
            print("   To restore a stash: git apply <relevant section from backup>")
            
            # Push to undo stack before executing
            self.undo_stack.push_operation({
                'type': 'stash_clear',
                'command': args,
                'description': f'Cleared {len(stashes)} stashes',
                'backups': {'backup_file': backup_file}
            })
            
            return self._run_git_command(args)
        else:
            print("\n❌ Operation cancelled.")
            return 1
    
    def _handle_aggressive_gc(self, args: List[str], danger_type: str) -> int:
        """Handle aggressive garbage collection with safety checks."""
        print("🛡️  SafeGIT: Intercepting aggressive garbage collection")
        print()
        
        if danger_type == 'gc_prune_now':
            print("⚠️  CRITICAL: --prune=now deletes objects IMMEDIATELY!")
            print("   No grace period means NO recovery if you made a mistake")
        else:
            print("⚠️  WARNING: Aggressive GC will rewrite your entire repository")
            print("   This can be VERY slow and may cause issues")
        
        # Check for recent operations
        reflog_result = subprocess.run(
            [self.real_git, 'reflog', '--since=1.hour.ago'],
            capture_output=True, text=True
        )
        
        if reflog_result.stdout.strip():
            recent_ops = len(reflog_result.stdout.strip().split('\n'))
            print(f"\n⚠️  Found {recent_ops} operations in the last hour!")
            print("   Recent operations may have unreachable objects")
        
        if self.dry_run:
            print("\n🔍 DRY-RUN: Would check for unreachable objects")
            print("   Would require confirmation before proceeding")
            return 0
        
        # For prune=now, force a safer alternative
        if danger_type == 'gc_prune_now':
            print("\n💡 SafeGIT recommends using a grace period instead")
            print("   Suggested: git gc --prune=1.hour.ago")
            response = self._get_user_input("\nUse safer alternative? [Y/n]: ",
                                               danger_level='low')
            
            if response.lower() != 'n':
                # Replace --prune=now with --prune=1.hour.ago
                safe_args = []
                for arg in args:
                    if arg == '--prune=now':
                        safe_args.append('--prune=1.hour.ago')
                    else:
                        safe_args.append(arg)
                print("\n✅ Using safer grace period")
                return self._run_git_command(safe_args)
        
        print("\n⚠️  This operation is risky!")
        response = self._get_user_input("Are you SURE you want to proceed? Type 'YES': ",
                                           danger_level='high')
        
        if response == 'YES':
            return self._run_git_command(args)
        else:
            print("\n❌ Operation cancelled.")
            return 1
    
    def _handle_filter_operations(self, args: List[str], danger_type: str) -> int:
        """Handle filter-branch and filter-repo with strong warnings."""
        print("🛡️  SafeGIT: Intercepting repository history rewrite")
        print()
        print("🚨 EXTREME DANGER: This operation rewrites ENTIRE repository history!")
        print()
        
        if danger_type == 'filter_branch':
            print("⚠️  git filter-branch is deprecated and dangerous")
            print("   Consider using 'git filter-repo' or BFG Repo-Cleaner instead")
        else:
            print("⚠️  git filter-repo will rewrite all commits")
            print("   All commit SHAs will change")
            print("   All forks/clones will need to be re-cloned")
        
        if self.dry_run:
            print("\n🔍 DRY-RUN: Would block this operation")
            print("   SafeGIT strongly discourages history rewriting")
            return 0
        
        print("\n❌ SafeGIT blocks this operation by default")
        print("\n💡 Alternatives:")
        print("   1. For removing files: Use BFG Repo-Cleaner")
        print("   2. For cleaning history: Create new repo with clean history")
        print("   3. For removing secrets: Rotate the secrets instead")
        
        print("\n⚠️  If you MUST proceed:")
        print("   1. Make a complete backup of your repository")
        print("   2. Notify all team members")
        print("   3. Use the command directly (not through SafeGIT)")
        
        return 1
    
    def _handle_push_destructive(self, args: List[str], danger_type: str) -> int:
        """Handle git push --mirror and --delete operations."""
        print("🛡️  SafeGIT: Intercepting destructive push operation")
        print()
        
        if danger_type == 'push_mirror':
            print("🚨 EXTREME DANGER: Push --mirror will overwrite the entire remote repository!")
            print("   • ALL remote branches will be replaced with local ones")
            print("   • Remote branches not present locally will be DELETED")
            print("   • This affects ALL collaborators immediately")
            print("   • Cannot be easily undone")
            
            if self.dry_run:
                print("\n🔍 DRY-RUN: Would completely mirror local repository to remote")
                print("   This is one of the most dangerous git operations!")
                return 0
            
            print("\n❌ SafeGIT strongly recommends against --mirror pushes")
            print("💡 Consider these safer alternatives:")
            print("   1. Push specific branches: git push origin branch-name")
            print("   2. Use --force-with-lease for individual branches")
            print("   3. Coordinate with team before repository-wide changes")
            
            response = self._get_user_input("\nAre you ABSOLUTELY CERTAIN? Type 'MIRROR PUSH' to proceed: ",
                                               danger_level='high')
            if response == 'MIRROR PUSH':
                print("\n⚠️  Proceeding with dangerous mirror push...")
                return self._run_git_command(args)
            else:
                print("\n❌ Operation cancelled.")
                return 1
                
        elif danger_type == 'push_delete':
            # Extract branch name from args
            branch_name = "remote branch"
            for i, arg in enumerate(args):
                if arg == '--delete' and i + 2 < len(args):
                    branch_name = args[i + 2]
                    break
            
            print(f"🚨 WARNING: Push --delete will permanently delete '{branch_name}' from remote!")
            print("   • Remote branch will be immediately deleted")
            print("   • Affects all collaborators who have this branch")
            print("   • Branch commits may become unreachable")
            
            if self.dry_run:
                print(f"\n🔍 DRY-RUN: Would delete remote branch '{branch_name}'")
                return 0
            
            print(f"\n💡 Recovery will require:")
            print("   1. Finding the branch SHA from reflog")
            print("   2. Recreating the branch: git push origin <sha>:<branch-name>")
            
            response = self._get_user_input(f"\nDelete remote branch '{branch_name}'? Type 'DELETE REMOTE' to confirm: ",
                                               danger_level='high')
            if response == 'DELETE REMOTE':
                print(f"\n🗑️  Deleting remote branch '{branch_name}'...")
                return self._run_git_command(args)
            else:
                print("\n❌ Operation cancelled.")
                return 1
    
    def _handle_reflog_expire(self, args: List[str], danger_type: str) -> int:
        """Handle git reflog expire operations."""
        print("🛡️  SafeGIT: Intercepting reflog expiration")
        print()
        
        print("🚨 CRITICAL WARNING: Expiring reflog entries removes your safety net!")
        print("   • Reflog is your primary recovery mechanism for lost commits")
        print("   • Once expired, commits may become permanently unrecoverable")
        print("   • This affects your ability to undo mistakes")
        
        if danger_type == 'reflog_expire_all':
            print("   • 🔥 --expire-all removes ALL reflog entries!")
        elif danger_type == 'reflog_expire_unreachable':
            print("   • 🔥 --expire-unreachable removes unreachable entries!")
        
        if self.dry_run:
            print("\n🔍 DRY-RUN: Would expire reflog entries")
            print("   This significantly reduces your ability to recover from mistakes!")
            return 0
        
        print("\n💡 SafeGIT recommendation: Keep reflog entries for safety")
        print("   Default git keeps reflog for 90 days - this is usually sufficient")
        print("   Only expire reflog if you have specific space requirements")
        
        response = self._get_user_input("\nExpire reflog entries anyway? Type 'EXPIRE REFLOG' to confirm: ",
                                           danger_level='high')
        if response == 'EXPIRE REFLOG':
            print("\n⚠️  Proceeding with reflog expiration...")
            return self._run_git_command(args)
        else:
            print("\n❌ Operation cancelled.")
            return 1
    
    def _handle_update_ref_delete(self, args: List[str], danger_type: str) -> int:
        """Handle git update-ref -d operations."""
        print("🛡️  SafeGIT: Intercepting low-level reference deletion")
        print()
        
        # Extract ref name from args
        ref_name = "reference"
        for i, arg in enumerate(args):
            if arg in ['-d', '--delete'] and i + 1 < len(args):
                ref_name = args[i + 1]
                break
        
        print(f"🚨 WARNING: Low-level deletion of '{ref_name}' reference!")
        print("   • This is a low-level git operation")
        print("   • May make commits unreachable")
        print("   • Recovery requires advanced git knowledge")
        print("   • Could affect repository integrity")
        
        if self.dry_run:
            print(f"\n🔍 DRY-RUN: Would delete reference '{ref_name}'")
            return 0
        
        print(f"\n💡 Recovery information:")
        print("   • Check reflog: git reflog")
        print("   • Find SHA: git log --oneline")
        print(f"   • Recreate: git update-ref {ref_name} <sha>")
        
        response = self._get_user_input(f"\nDelete reference '{ref_name}'? Type 'DELETE REFERENCE' to confirm: ",
                                           danger_level='high')
        if response == 'DELETE REFERENCE':
            print(f"\n🗑️  Deleting reference '{ref_name}'...")
            return self._run_git_command(args)
        else:
            print("\n❌ Operation cancelled.")
            return 1
    
    def _handle_generic_dangerous(self, args: List[str], danger_type: str) -> int:
        """Handle other dangerous commands generically."""
        # Dry-run mode for generic dangerous commands
        if self.dry_run:
            print(f"🛡️  SafeGIT: Intercepting potentially dangerous command: {' '.join(args)}")
            print()
            print("\n🔍 DRY-RUN: Showing what would happen:")
            
            # Command-specific dry-run information
            if danger_type == 'rebase':
                print("   • Would rewrite commit history")
                print("   • Would potentially cause conflicts")
                print("   • Recovery possible via ORIG_HEAD")
            elif danger_type == 'branch_delete_force':
                branch_name = None
                for i, arg in enumerate(args):
                    if arg in ['-D', '--delete'] and i + 1 < len(args):
                        branch_name = args[i + 1]
                        break
                if branch_name:
                    print(f"   • Would force delete branch: {branch_name}")
                print("   • May lose unique commits if not merged")
                print("   • Recovery possible via reflog")
            elif danger_type == 'commit_amend':
                print("   • Would modify the previous commit")
                print("   • Would change commit SHA")
                print("   • Original available in reflog")
            elif danger_type == 'stash_drop':
                print("   • Would permanently delete stashed changes")
                print("   • NOT recoverable once dropped")
            elif danger_type == 'gc_prune':
                print("   • Would permanently remove unreachable objects")
                print("   • Would clean up reflog entries")
            elif danger_type == 'gc_prune_now':
                print("   • Would IMMEDIATELY delete unreachable objects")
                print("   • NO grace period - permanent deletion")
            elif danger_type == 'gc_aggressive':
                print("   • Would rewrite entire repository")
                print("   • Very slow operation")
            elif danger_type == 'stash_clear' or danger_type == 'stash_drop_all':
                print("   • Would delete ALL stashes permanently")
                print("   • Complete loss of stashed work")
            elif danger_type == 'rebase_interactive':
                print("   • Would open interactive rebase editor")
                print("   • Complex history rewriting possible")
            elif danger_type == 'rebase_onto':
                print("   • Would perform complex branch surgery")
                print("   • High risk of losing commits")
            elif danger_type == 'filter_repo':
                print("   • Would rewrite ENTIRE repository history")
                print("   • Completely irreversible operation")
            elif danger_type == 'reflog_expire_unreachable':
                print("   • Would delete unreachable reflog entries")
                print("   • Removes ability to recover lost commits")
            elif danger_type == 'lfs_prune':
                print("   • Would delete LFS objects not in current refs")
                print("   • Large files may be unrecoverable")
            elif danger_type == 'submodule_deinit':
                print("   • Would remove submodule working directory")
                print("   • Uncommitted submodule changes lost")
            elif danger_type == 'sparse_checkout_set':
                print("   • Would change visible files in working directory")
                print("   • Files may appear to vanish")
            
            print("\n⚠️  DRY-RUN: This is a potentially dangerous operation!")
            print("   In real execution, SafeGIT would:")
            print("   1. Show detailed warnings")
            print("   2. Require explicit confirmation")
            print("   3. Show recovery options after completion")
            
            return 0
        
        # Special handling for commit --amend
        if danger_type == 'commit_amend':
            # Check if the current commit has been pushed
            try:
                # Check if current branch has upstream tracking
                result = subprocess.run(
                    [self.real_git, 'rev-parse', 'HEAD@{u}'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    # No upstream branch set - amend is safe
                    print("✅ No upstream branch detected - amending is safe.")
                    self._log_interception(args, 'commit_amend_safe_no_upstream', {})
                    result = self._run_git_command(args)
                    if result == 0:
                        self._show_reflog_hint('commit_amend')
                    return result
                else:
                    # Check if HEAD matches upstream
                    upstream_ref = result.stdout.strip()
                    head_result = subprocess.run(
                        [self.real_git, 'rev-parse', 'HEAD'],
                        capture_output=True,
                        text=True
                    )
                    head_ref = head_result.stdout.strip()
                    
                    upstream_commit_result = subprocess.run(
                        [self.real_git, 'rev-parse', upstream_ref],
                        capture_output=True,
                        text=True
                    )
                    upstream_commit = upstream_commit_result.stdout.strip()
                    
                    if head_ref == upstream_commit:
                        # HEAD matches upstream - commit has been pushed
                        print(f"🛡️  SafeGIT: Intercepting potentially dangerous command: {' '.join(args)}")
                        print()
                        print("⚠️  WARNING: This commit has already been pushed!")
                        print("   Amending pushed commits rewrites history and can cause problems for other developers.")
                        print("   Consider creating a new commit instead.")
                        
                        response = self._get_user_input("\nDo you still want to amend? [y/N]: ",
                                                           danger_level='medium')
                        
                        if response.lower() == 'y':
                            self._log_interception(args, 'commit_amend_pushed_allowed', {})
                            result = self._run_git_command(args)
                            if result == 0:
                                self._show_reflog_hint('commit_amend')
                            return result
                        else:
                            print("\n❌ Operation cancelled.")
                            return 1
                    else:
                        # HEAD is ahead of upstream - safe to amend
                        print("✅ Commit has not been pushed - amending is safe.")
                        self._log_interception(args, 'commit_amend_safe_not_pushed', {})
                        result = self._run_git_command(args)
                        if result == 0:
                            self._show_reflog_hint('commit_amend')
                        return result
                        
            except Exception as e:
                # If we can't determine push status, fall back to generic warning
                print(f"⚠️  Could not determine if commit was pushed: {e}")
                # Fall through to generic handling
        
        # Generic handling for other dangerous commands
        print(f"🛡️  SafeGIT: Intercepting potentially dangerous command: {' '.join(args)}")
        print()
        print("⚠️  This command can have destructive effects.")
        
        # Command-specific warnings
        warnings = {
            'rebase': "Rebasing rewrites history and can cause conflicts for other developers.",
            'rebase_interactive': "Interactive rebase allows complex history rewriting. Easy to lose commits.",
            'rebase_onto': "Rebase --onto performs complex branch surgery. Commits can be lost.",
            'filter_branch': "filter-branch is extremely dangerous and can corrupt your repository.",
            'filter_repo': "filter-repo rewrites entire repository history. This is irreversible.",
            'branch_delete_force': "Force deleting a branch may lose unique commits forever.",
            'gc_prune': "Aggressive garbage collection permanently removes unreachable objects.",
            'gc_prune_now': "Prune=now immediately deletes objects with no grace period!",
            'gc_aggressive': "Aggressive GC rewrites entire repository. Can be very slow.",
            'stash_drop': "Dropped stashes cannot be recovered.",
            'stash_clear': "This will delete ALL your stashes permanently!",
            'stash_drop_all': "This will delete ALL your stashes permanently!",
            'commit_amend': "Amending commits rewrites history.",
            'merge_ours': "This merge strategy discards all changes from the other branch.",
            'reflog_expire': "Expiring reflog entries removes your safety net for recovery.",
            'reflog_expire_unreachable': "Expiring unreachable entries removes ability to recover lost commits!",
            'reflog_expire_all': "Expiring all reflog entries removes entire history safety net!",
            'switch_discard_changes': "This will discard all local changes in your working directory.",
            'worktree_remove_force': "Force removing worktree may delete uncommitted changes.",
            'update_ref_delete': "Deleting references at low level. Recovery may be difficult.",
            'cherry_pick_abort': "Aborting cherry-pick loses conflict resolution work.",
            'am_abort': "Aborting patch application loses conflict resolution work.",
            'notes_prune': "Pruning notes permanently removes git notes.",
            'lfs_prune': "LFS prune deletes large file objects. Ensure they're backed up.",
            'submodule_deinit': "Deinitializing submodule removes its working tree.",
            'sparse_checkout_set': "Sparse checkout can make files appear to vanish.",
            'sparse_checkout_reapply': "Reapplying sparse checkout may hide uncommitted changes."
        }
        
        if danger_type in warnings:
            print(f"   {warnings[danger_type]}")
        
        response = self._get_user_input("\nDo you want to proceed? [y/N]: ",
                                           danger_level='medium')
        
        if response.lower() == 'y':
            self._log_interception(args, f'{danger_type}_allowed', {})
            result = self._run_git_command(args)
            
            # Show reflog hints for specific operations
            if result == 0:
                if danger_type == 'rebase':
                    self._show_reflog_hint('rebase')
                elif danger_type == 'branch_delete_force':
                    # Try to extract branch name
                    branch_name = None
                    for i, arg in enumerate(args):
                        if arg in ['-D', '--delete'] and i + 1 < len(args):
                            branch_name = args[i + 1]
                            break
                    self._show_reflog_hint('branch_delete', branch_name)
                elif danger_type == 'commit_amend':
                    self._show_reflog_hint('commit_amend')
            
            return result
        else:
            print("\n❌ Operation cancelled.")
            return 1
    
    def _handle_undo_command(self, interactive: bool = False) -> int:
        """Handle the undo command using multi-level undo stack."""
        if interactive:
            print("🔄 SafeGIT Interactive Undo Mode\n")
            return 0 if self.undo_stack.undo(interactive=True) else 1
        else:
            print("🔄 SafeGIT Undo: Reverting last operation...\n")
            return 0 if self.undo_stack.undo(levels=1) else 1
    
    def _show_reflog_hint(self, operation: str, target: str = None):
        """Show reflog recovery hint after destructive operations."""
        print("\n💡 Recovery Information:")
        print("─" * 50)
        
        if operation == 'reset':
            print("If this was a mistake, you can recover the previous state with:")
            print(f"  git reset --hard HEAD@{{1}}")
            print("\nTo see what was at HEAD before this operation:")
            print("  git reflog")
            print("  git show HEAD@{1}")
            
        elif operation == 'rebase':
            print("If the rebase went wrong, you can recover the original branch state with:")
            print(f"  git reset --hard ORIG_HEAD")
            print("\nTo see the reflog for this branch:")
            print("  git reflog")
            
        elif operation == 'commit_amend':
            print("The original commit is still in the reflog. To recover it:")
            print("  git reflog  # Find the original commit SHA")
            print("  git reset --hard <original-sha>")
            print("\nOr create a new branch from the original commit:")
            print("  git branch backup-original HEAD@{1}")
            
        elif operation == 'branch_delete':
            if target:
                print(f"The deleted branch '{target}' can be recovered if you know its last commit.")
                print("To find the last commit:")
                print(f"  git reflog | grep '{target}'")
                print("\nOnce you find the SHA, recreate the branch:")
                print("  git branch <branch-name> <sha>")
            
        elif operation == 'clean':
            print("⚠️  Note: git clean permanently deletes files. They are NOT in the reflog.")
            print("However, SafeGIT created a backup (if you used the safe option).")
            print("Check your stashes: git stash list | grep SAFEGIT")
            
        print("─" * 50)
    
    def _run_git_command(self, args: List[str]) -> int:
        """Run the actual git command."""
        try:
            # Remove 'git' from args if present
            if args and args[0] == 'git':
                args = args[1:]
            
            if self.dry_run:
                print(f"\n📋 DRY-RUN: Would execute: git {' '.join(args)}")
                # For dry-run, try to show what the command would do
                self._explain_command_effects(args)
                return 0
            
            result = subprocess.run([self.real_git] + args)
            return result.returncode
        except Exception as e:
            print(f"Error running git command: {e}", file=sys.stderr)
            return 1
    
    def _explain_command_effects(self, args: List[str]):
        """Explain what a git command would do in dry-run mode."""
        if not args:
            return
        
        command = args[0]
        
        # Explain common commands
        if command == 'reset':
            if '--hard' in args:
                print("   Effect: Would discard ALL uncommitted changes permanently")
                print("   Effect: Would move HEAD to specified commit")
            elif '--keep' in args:
                print("   Effect: Would move HEAD but preserve uncommitted changes")
            else:
                print("   Effect: Would unstage changes but keep modifications")
                
        elif command == 'clean':
            print("   Effect: Would permanently delete untracked files")
            if '-d' in args:
                print("   Effect: Would also delete untracked directories")
            if '-x' in args or '-X' in args:
                print("   Effect: Would also delete ignored files")
                
        elif command == 'checkout':
            if '-f' in args or '--force' in args:
                print("   Effect: Would discard local changes and switch branches")
            elif len(args) > 1 and args[1] == '.':
                print("   Effect: Would discard ALL changes in current directory")
            else:
                print("   Effect: Would switch branches or restore files")
                
        elif command == 'push':
            if '--force' in args or '-f' in args:
                print("   Effect: Would overwrite remote branch history")
            elif '--force-with-lease' in args:
                print("   Effect: Would force push only if remote hasn't changed")
            else:
                print("   Effect: Would push commits to remote repository")
                
        elif command == 'rebase':
            print("   Effect: Would rewrite commit history")
            if '-i' in args:
                print("   Effect: Would open interactive rebase editor")
                
        elif command == 'commit':
            if '--amend' in args:
                print("   Effect: Would modify the previous commit")
            else:
                print("   Effect: Would create a new commit")
                
        elif command == 'branch':
            if '-D' in args or ('--delete' in args and '--force' in args):
                print("   Effect: Would force delete branch, possibly losing commits")
            elif '-d' in args or '--delete' in args:
                print("   Effect: Would delete branch if fully merged")
            else:
                print("   Effect: Would create or list branches")
                
        elif command == 'stash':
            if args[1:] and args[1] in ['drop', 'clear']:
                print("   Effect: Would permanently delete stashed changes")
            elif args[1:] and args[1] == 'pop':
                print("   Effect: Would apply and remove stash")
            else:
                print("   Effect: Would save or list stashed changes")
    
    def run(self, args: List[str]) -> int:
        """Main entry point for the wrapper."""
        # Parse non-interactive flags first
        if '--yes' in args or '-y' in args:
            self.assume_yes = True
            args = [arg for arg in args if arg not in ['--yes', '-y']]
            
        if '--force-yes' in args:
            self.force_yes = True
            self.assume_yes = True  # force-yes implies yes
            args = [arg for arg in args if arg != '--force-yes']
            
        if '--non-interactive' in args or '--batch' in args:
            self.non_interactive = True
            args = [arg for arg in args if arg not in ['--non-interactive', '--batch']]
            
        # Check for dry-run flag
        if '--dry-run' in args:
            self.dry_run = True
            args = [arg for arg in args if arg != '--dry-run']
            print("🔍 DRY-RUN MODE: Simulating command without executing")
            print("─" * 50)
        
        # Check for help or version
        if not args or args[0] in ['-h', '--help', 'help']:
            self._show_help()
            return 0
        
        if args[0] in ['-v', '--version', 'version']:
            print("SafeGIT v2.0 - Git wrapper for AI safety with non-interactive support")
            print(f"Real git: {self.real_git}")
            return 0
        
        # Check for undo commands
        if args[0] == 'undo':
            if self.dry_run:
                print("🔄 DRY-RUN: Would show undo history and allow reverting operations")
                return 0
            # Check for interactive mode or levels
            interactive = '--interactive' in args or '-i' in args
            return self._handle_undo_command(interactive=interactive)
        
        # Check for undo history command
        if args[0] == 'undo-history':
            self.undo_stack.show_history(limit=20)
            return 0
        
        # Check for context commands
        context_result = self._handle_context_commands(args)
        if context_result is not None:
            return context_result
        
        # Check context-based restrictions first
        allowed, reason = self.context.is_command_allowed(' '.join(args))
        if not allowed:
            print(f"🛡️  SafeGIT: Command blocked by context rules")
            print(f"❌  {reason}")
            print(self.context.get_status())
            return 1
        
        # Check if this is a dangerous command
        danger_check = self._is_dangerous_command(args)
        
        if danger_check:
            command_str, danger_type = danger_check
            self.intercepted_count += 1
            
            # Log the interception
            self._log_interception(args, 'intercepted', {'danger_type': danger_type})
            
            # Handle specific dangerous commands
            if danger_type == 'reset_hard':
                return self._handle_reset_hard(args)
            elif danger_type == 'clean_force':
                return self._handle_clean_force(args)
            elif danger_type in ['checkout_force', 'checkout_dot', 'checkout_path']:
                return self._handle_checkout_force(args)
            elif danger_type == 'push_force':
                return self._handle_push_force(args)
            elif danger_type in ['stash_drop_clear', 'stash_clear', 'stash_drop_all']:
                return self._handle_stash_clear(args, danger_type)
            elif danger_type in ['gc_prune', 'gc_prune_now', 'gc_aggressive']:
                return self._handle_aggressive_gc(args, danger_type)
            elif danger_type in ['filter_branch', 'filter_repo']:
                return self._handle_filter_operations(args, danger_type)
            elif danger_type in ['push_mirror', 'push_delete']:
                return self._handle_push_destructive(args, danger_type)
            elif danger_type in ['reflog_expire', 'reflog_expire_unreachable', 'reflog_expire_all']:
                return self._handle_reflog_expire(args, danger_type)
            elif danger_type in ['update_ref_delete']:
                return self._handle_update_ref_delete(args, danger_type)
            else:
                return self._handle_generic_dangerous(args, danger_type)
        else:
            # Safe command - pass through to git
            return self._run_git_command(args)
    
    def _handle_context_commands(self, args: List[str]) -> Optional[int]:
        """Handle SafeGit context commands."""
        if len(args) < 1:
            return None
            
        command = args[0]
        
        # Dry-run handling for context commands
        if self.dry_run and command in ['set-env', 'set-mode', 'add-restriction', 'remove-restriction']:
            print("\n🔍 DRY-RUN: Context command simulation")
            if command == 'set-env' and len(args) >= 2:
                print(f"   Would set environment to: {args[1]}")
            elif command == 'set-mode' and len(args) >= 2:
                print(f"   Would set mode to: {args[1]}")
            elif command == 'add-restriction' and len(args) >= 2:
                print(f"   Would add restriction pattern: {args[1]}")
            elif command == 'remove-restriction' and len(args) >= 2:
                print(f"   Would remove restriction pattern: {args[1]}")
            print("   Context would be saved to .git/safegit-context.json")
            return 0
        
        # Handle context commands
        if command == 'set-env':
            if len(args) < 2:
                print("Usage: safegit set-env <development|staging|production>")
                return 1
            try:
                self.context.set_environment(args[1])
                print(f"✅ Environment set to: {args[1]}")
                print(self.context.get_status())
                return 0
            except ValueError as e:
                print(f"❌ Error: {e}")
                return 1
                
        elif command == 'set-mode':
            if len(args) < 2:
                print("Usage: safegit set-mode <normal|code-freeze|maintenance|paranoid>")
                return 1
            try:
                self.context.set_mode(args[1])
                print(f"✅ Mode set to: {args[1]}")
                print(self.context.get_status())
                return 0
            except ValueError as e:
                print(f"❌ Error: {e}")
                return 1
                
        elif command == 'show-context':
            # Check for --json flag
            if '--json' in args:
                # Output context as JSON
                import json
                context_data = {
                    'environment': self.context.context['environment'],
                    'mode': self.context.context['mode'],
                    'restrictions': self.context.context['restrictions'],
                    'created_at': self.context.context.get('created_at', ''),
                    'updated_at': self.context.context.get('updated_at', '')
                }
                print(json.dumps(context_data, indent=2))
            else:
                print(self.context.get_status())
            return 0
            
        elif command == 'add-restriction':
            if len(args) < 2:
                print("Usage: safegit add-restriction <pattern>")
                return 1
            self.context.add_restriction(args[1])
            print(f"✅ Added restriction: {args[1]}")
            print(self.context.get_status())
            return 0
            
        elif command == 'remove-restriction':
            if len(args) < 2:
                print("Usage: safegit remove-restriction <pattern>")
                return 1
            self.context.remove_restriction(args[1])
            print(f"✅ Removed restriction: {args[1]}")
            print(self.context.get_status())
            return 0
            
        return None

    def _show_help(self):
        """Show SafeGIT help."""
        print("""
SafeGIT - A protective wrapper around git to prevent AI disasters

Usage:
    safegit [options] <git command>

SafeGIT intercepts dangerous git commands and provides safe alternatives,
while passing through safe commands directly to git.

Options:
    --dry-run             Simulate command without executing (shows what would happen)
    --yes, -y             Automatically confirm safe operations (medium risk)
    --force-yes           Force confirmation of dangerous operations (use with caution!)
    --non-interactive     Fail on any interactive prompt (for scripts/CI)
    --batch               Same as --non-interactive

Environment Variables:
    SAFEGIT_NONINTERACTIVE=1    Enable non-interactive mode
    SAFEGIT_ASSUME_YES=1        Auto-confirm safe operations
    SAFEGIT_FORCE_YES=1         Force all confirmations (dangerous!)
    CI=1                        Auto-detected CI environment

Intercepted Commands:
    git reset --hard        →  Creates backup before reset
    git clean -f[dx]        →  Creates backup of untracked files
    git checkout -f         →  Stashes changes before checkout
    git push --force        →  Converts to --force-with-lease by default
    git rebase             →  Warns about history rewriting
    git branch -D          →  Warns about losing commits
    ... and more

Safe Commands (passed through):
    git status, log, diff, add, commit, pull, fetch, merge, etc.

Special Commands:
    safegit help              Show this help
    safegit version           Show version info
    safegit undo              Undo last operation (use -i for interactive)
    safegit undo-history      Show undo history with recovery options
    safegit check-reset       Check reset safety
    safegit check-clean       Check clean safety
    safegit stats             Show interception statistics

Context Management:
    safegit set-env <env>            Set environment (development/staging/production)
    safegit set-mode <mode>          Set mode (normal/code-freeze/maintenance/paranoid)
    safegit show-context             Show current context settings
    safegit show-context --json      Show context in JSON format (machine-readable)
    safegit add-restriction <pattern>    Add a custom restriction pattern
    safegit remove-restriction <pattern> Remove a custom restriction pattern

Interactive Examples:
    safegit reset --hard HEAD~1              # Prompts for confirmation
    safegit clean -fdx                       # Asks to create backup
    safegit push --force                     # Converts to --force-with-lease

Non-Interactive Examples:
    safegit --yes add .                      # Auto-confirms safe operation
    safegit --yes commit -m "msg"            # Auto-confirms commit
    safegit --force-yes reset --hard         # Force confirms dangerous operation
    
CI/CD Usage:
    export SAFEGIT_NONINTERACTIVE=1
    export SAFEGIT_ASSUME_YES=1
    safegit add .                            # Runs without prompts
    safegit commit -m "Automated commit"     # Auto-confirmed
    safegit push                             # Safe, proceeds automatically
    
Dry-Run Examples:
    safegit --dry-run reset --hard HEAD~1    # See what would be reset
    safegit --dry-run clean -fdx             # See what files would be deleted
    safegit --dry-run push --force           # See force push implications

For more safety features, see: safegit safe-git-commands --help

AI AGENT USAGE:
    Configure your AI agent to ONLY use 'safegit' instead of 'git'
    This prevents catastrophic mistakes like the Replit incident.
""")
    
    def show_stats(self):
        """Show interception statistics."""
        if not self.log_file.exists():
            print("No interceptions logged yet.")
            return
        
        # Read log file with shared lock to prevent corruption
        logs = []
        try:
            with open(self.log_file, 'r') as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    for line in f:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            # Skip corrupted lines
                            continue
                finally:
                    # Release lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            print(f"Error reading log file: {e}", file=sys.stderr)
            return
        
        print(f"\nSafeGIT Interception Statistics")
        print(f"{'='*50}")
        print(f"Total interceptions: {len(logs)}")
        
        # Count by danger type
        danger_counts = {}
        for log in logs:
            danger_type = log.get('details', {}).get('danger_type', 'unknown')
            danger_counts[danger_type] = danger_counts.get(danger_type, 0) + 1
        
        print("\nBy command type:")
        for danger_type, count in sorted(danger_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {danger_type}: {count}")
        
        # Recent interceptions
        print("\nRecent interceptions:")
        for log in logs[-5:]:
            print(f"  {log['timestamp']}: {log['command']}")


def main():
    """Main entry point."""
    wrapper = SafeGitWrapper()
    
    # Special safegit commands
    if len(sys.argv) > 1:
        if sys.argv[1] == 'stats':
            wrapper.show_stats()
            return
        elif sys.argv[1] in ['check-reset', 'check-clean', 'safe-reset', 'safe-clean']:
            # Delegate to safe_git_commands.py
            from safe_git_commands import main as safe_git_main
            sys.argv[0] = 'safe_git_commands.py'
            safe_git_main()
            return
    
    # Run the wrapper
    sys.exit(wrapper.run(sys.argv[1:]))


if __name__ == '__main__':
    main()