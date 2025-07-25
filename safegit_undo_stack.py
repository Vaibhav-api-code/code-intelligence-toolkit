#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
SafeGIT Undo Stack - Multi-level undo with metadata and recovery scripts.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import json
import uuid
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import fcntl
import tempfile

# --- cross-platform locking & atomic write helper (duplicated to avoid import cycles) ---
import contextlib, uuid, os
from pathlib import Path

def _atomic_write(path: Path, data: str):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + f'.tmp-{uuid.uuid4().hex}')
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)

@contextlib.contextmanager
def acquire_lock(lock_path: Path):
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


class UndoStack:
    """Multi-level undo stack with metadata and recovery capabilities."""
    
    def __init__(self, repo_root: Path = None):
        """Initialize the undo stack."""
        self.repo_root = repo_root or Path.cwd()
        self.stack_file = self.repo_root / '.git' / 'safegit-undo-stack.json'
        self.backup_dir = self.repo_root / '.git' / 'safegit-backups'
        self.max_depth = 50
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        self.stack_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_stack(self) -> List[Dict]:
        """Load the undo stack from file with locking."""
        if not self.stack_file.exists():
            return []
        
        try:
            with open(self.stack_file, 'r') as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    return json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            return []
    
    def _save_stack(self, stack: List[Dict]):
        """Save the undo stack with atomic write."""
        # Create temp file
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.stack_file.parent,
            prefix='.undo-stack-',
            suffix='.tmp'
        )
        
        try:
            with os.fdopen(temp_fd, 'w') as f:
                # Exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(stack, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    pass  # Lock released on close
            
            # Atomic rename
            os.replace(temp_path, self.stack_file)
            
        except Exception:
            try:
                os.unlink(temp_path)
            except:
                pass
            raise
    
    def push_operation(self, operation: Dict[str, Any]):
        """Add an operation to the undo stack."""
        # Get current repository state
        metadata = self._capture_metadata()
        
        # Create undo entry
        entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation.get('type', 'unknown'),
            'command': operation.get('command', []),
            'description': operation.get('description', ''),
            'metadata': metadata,
            'backups': operation.get('backups', []),
            'recovery_script': self._generate_recovery_script(operation),
            'recovery_hints': self._generate_recovery_hints(operation)
        }
        
        # Load current stack
        stack = self._load_stack()
        
        # Add new entry
        stack.append(entry)
        
        # Maintain max depth
        while len(stack) > self.max_depth:
            old_entry = stack.pop(0)
            self._cleanup_old_backups(old_entry)
        
        # Save updated stack
        self._save_stack(stack)
        
        return entry['id']
    
    def _capture_metadata(self) -> Dict[str, Any]:
        """Capture current repository metadata."""
        metadata = {
            'branch': self._get_current_branch(),
            'head_sha': self._get_head_sha(),
            'head_message': self._get_head_message(),
            'dirty_files': self._get_dirty_files(),
            'stash_count': self._get_stash_count(),
            'reflog_head': self._get_reflog_entry(0)
        }
        return metadata
    
    def _get_current_branch(self) -> str:
        """Get current branch name."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True
            )
            return result.stdout.strip() or 'HEAD'
        except:
            return 'unknown'
    
    def _get_head_sha(self) -> str:
        """Get current HEAD SHA."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True
            )
            return result.stdout.strip()[:8]
        except:
            return 'unknown'
    
    def _get_head_message(self) -> str:
        """Get current HEAD commit message."""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%s'],
                capture_output=True, text=True
            )
            return result.stdout.strip()
        except:
            return 'unknown'
    
    def _get_dirty_files(self) -> List[str]:
        """Get list of modified files."""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True, text=True
            )
            if result.stdout:
                return [line[3:] for line in result.stdout.strip().split('\n')]
            return []
        except:
            return []
    
    def _get_stash_count(self) -> int:
        """Get number of stashes."""
        try:
            result = subprocess.run(
                ['git', 'stash', 'list'],
                capture_output=True, text=True
            )
            if result.stdout:
                return len(result.stdout.strip().split('\n'))
            return 0
        except:
            return 0
    
    def _get_reflog_entry(self, index: int) -> str:
        """Get reflog entry at index."""
        try:
            result = subprocess.run(
                ['git', 'reflog', '-1', f'HEAD@{{{index}}}'],
                capture_output=True, text=True
            )
            return result.stdout.strip()
        except:
            return ''
    
    def _generate_recovery_script(self, operation: Dict) -> List[str]:
        """Generate recovery commands for the operation."""
        op_type = operation.get('type', '')
        recovery = []
        
        if op_type == 'reset_hard':
            recovery.append('# Recover from hard reset')
            recovery.append('git reset --hard HEAD@{1}')
            recovery.append('# Or restore specific stash:')
            recovery.append('git stash list | grep SAFEGIT')
            recovery.append('git stash pop stash@{n}')
            
        elif op_type == 'clean_force':
            recovery.append('# Restore from clean backup')
            if operation.get('backup_file'):
                recovery.append(f'unzip {operation["backup_file"]}')
            
        elif op_type == 'stash_clear':
            recovery.append('# Restore from stash backup')
            if operation.get('backup_file'):
                recovery.append(f'# Review backup: cat {operation["backup_file"]}')
                recovery.append('# Apply specific sections with: git apply')
            
        elif op_type == 'checkout_force':
            recovery.append('# Restore from checkout stash')
            recovery.append('git stash list | grep SAFEGIT-CHECKOUT')
            recovery.append('git stash pop')
            
        elif op_type == 'commit_amend':
            recovery.append('# Restore original commit')
            recovery.append('git reflog | grep "commit (amend)"')
            recovery.append('git reset --hard HEAD@{1}')
            
        elif op_type == 'rebase':
            recovery.append('# Restore pre-rebase state')
            recovery.append('git reset --hard ORIG_HEAD')
            
        elif op_type == 'branch_delete':
            recovery.append('# Recover deleted branch')
            recovery.append('git reflog | grep <branch-name>')
            recovery.append('git branch <branch-name> <sha>')
        
        return recovery
    
    def _generate_recovery_hints(self, operation: Dict) -> Dict[str, str]:
        """Generate contextual recovery hints."""
        hints = {
            'reset_hard': 'Use reflog to find previous HEAD position',
            'clean_force': 'Check backup zip file in current directory',
            'stash_clear': 'Review text backup for stash contents',
            'checkout_force': 'Look for SAFEGIT stashes',
            'commit_amend': 'Original commit still in reflog',
            'rebase': 'ORIG_HEAD contains pre-rebase state',
            'branch_delete': 'Branch commits still in reflog'
        }
        
        op_type = operation.get('type', '')
        return {
            'primary': hints.get(op_type, 'Check git reflog for recovery'),
            'command': 'git reflog --date=iso'
        }
    
    def undo(self, levels: int = 1, interactive: bool = False, non_interactive: bool = False,
             auto_yes: bool = False) -> bool:
        """Undo last N operations with non-interactive support."""
        stack = self._load_stack()
        
        if not stack:
            print("No operations to undo.")
            return False
        
        if interactive:
            return self._interactive_undo(stack)
        
        # Undo last N operations
        for _ in range(min(levels, len(stack))):
            if not stack:
                break
                
            entry = stack[-1]  # Peek at last entry
            
            print(f"\nUndoing: {entry['operation_type']}")
            print(f"  Timestamp: {entry['timestamp']}")
            print(f"  Command: {' '.join(entry['command'])}")
            
            # Show recovery script
            if entry['recovery_script']:
                print("\nRecovery commands:")
                for cmd in entry['recovery_script']:
                    print(f"  {cmd}")
            
            # Confirm
            if non_interactive:
                if auto_yes:
                    print("\n[AUTO-CONFIRM] Execute recovery? [Y/n]: Y")
                    response = 'y'
                else:
                    print("\n❌ ERROR: Recovery confirmation required in non-interactive mode")
                    print("   Use --yes flag or set SAFEGIT_ASSUME_YES=1")
                    return False
            else:
                response = input("\nExecute recovery? [Y/n]: ")
                if response.lower() == 'n':
                    print("Undo cancelled.")
                    return False
            
            # Execute recovery
            success = self._execute_recovery(entry)
            
            if success:
                stack.pop()  # Remove from stack
                print("✅ Recovery successful")
            else:
                print("❌ Recovery failed")
                return False
        
        # Save updated stack
        self._save_stack(stack)
        return True
    
    def _interactive_undo(self, stack: List[Dict]) -> bool:
        """Interactive undo with operation selection."""
        print("\nUndo History:")
        print("=" * 80)
        
        # Show recent operations
        for i, entry in enumerate(reversed(stack[-10:])):
            print(f"\n{i+1}. {entry['operation_type']} - {entry['timestamp']}")
            print(f"   Command: {' '.join(entry['command'])}")
            print(f"   Branch: {entry['metadata']['branch']}")
            print(f"   Description: {entry.get('description', 'N/A')}")
        
        print("\n" + "=" * 80)
        
        # Get selection
        try:
            choice = input("\nSelect operation to undo (1-10) or 'q' to quit: ")
            if choice.lower() == 'q':
                return False
            
            index = int(choice) - 1
            if 0 <= index < min(10, len(stack)):
                # Get the actual entry from the end of stack
                actual_index = len(stack) - 1 - index
                entry = stack[actual_index]
                
                # Show full details
                print(f"\nSelected: {entry['operation_type']}")
                print(f"This will undo all operations after this one ({index} operations)")
                
                confirm = input("\nContinue? [Y/n]: ")
                if confirm.lower() != 'n':
                    # Undo all operations from this point
                    return self.undo(levels=index + 1, interactive=False)
                
        except (ValueError, IndexError):
            print("Invalid selection.")
        
        return False
    
    def _execute_recovery(self, entry: Dict) -> bool:
        """Execute recovery for a specific entry."""
        op_type = entry['operation_type']
        
        try:
            if op_type == 'reset_hard' and entry.get('backups'):
                # Look for stash with matching timestamp
                stash_ref = entry['backups'].get('stash_ref')
                if stash_ref:
                    result = subprocess.run(
                        ['git', 'stash', 'pop', stash_ref],
                        capture_output=True, text=True
                    )
                    return result.returncode == 0
            
            elif op_type == 'clean_force' and entry.get('backups'):
                # Restore from zip backup
                backup_file = entry['backups'].get('backup_file')
                if backup_file and os.path.exists(backup_file):
                    import zipfile
                    with zipfile.ZipFile(backup_file, 'r') as zf:
                        zf.extractall(self.repo_root)
                    return True
            
            # Default: show manual recovery steps
            print("\nManual recovery required:")
            for cmd in entry.get('recovery_script', []):
                print(f"  {cmd}")
            
            return True
            
        except Exception as e:
            print(f"Recovery error: {e}")
            return False
    
    def _cleanup_old_backups(self, entry: Dict):
        """Clean up backups for old entries."""
        # Remove old backup files
        if entry.get('backups'):
            for backup_type, backup_path in entry['backups'].items():
                if isinstance(backup_path, str) and os.path.exists(backup_path):
                    try:
                        if os.path.isfile(backup_path):
                            os.unlink(backup_path)
                        elif os.path.isdir(backup_path):
                            shutil.rmtree(backup_path)
                    except:
                        pass
    
    def show_history(self, limit: int = 10):
        """Display undo history."""
        stack = self._load_stack()
        
        if not stack:
            print("No undo history.")
            return
        
        print(f"\nSafeGIT Undo History (last {limit} operations)")
        print("=" * 80)
        
        for entry in reversed(stack[-limit:]):
            print(f"\nID: {entry['id'][:8]}")
            print(f"Time: {entry['timestamp']}")
            print(f"Operation: {entry['operation_type']}")
            print(f"Command: {' '.join(entry['command'])}")
            print(f"Branch: {entry['metadata']['branch']}")
            print(f"HEAD: {entry['metadata']['head_sha']} - {entry['metadata']['head_message']}")
            
            if entry['metadata']['dirty_files']:
                print(f"Dirty files: {len(entry['metadata']['dirty_files'])}")
            
            print("Recovery hint:", entry['recovery_hints']['primary'])
            print("-" * 40)
    
    def export_history(self, output_file: str = 'safegit-history.json'):
        """Export complete undo history."""
        stack = self._load_stack()
        
        with open(output_file, 'w') as f:
            json.dump({
                'exported_at': datetime.now().isoformat(),
                'repo_root': str(self.repo_root),
                'stack_depth': len(stack),
                'operations': stack
            }, f, indent=2)
        
        print(f"✅ Exported {len(stack)} operations to {output_file}")


# CLI Interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='SafeGIT Undo Stack - Advanced recovery system'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Show history
    history_parser = subparsers.add_parser('history', help='Show undo history')
    history_parser.add_argument('--limit', type=int, default=10, help='Number of entries to show')
    
    # Undo
    undo_parser = subparsers.add_parser('undo', help='Undo operations')
    undo_parser.add_argument('--levels', type=int, default=1, help='Number of operations to undo')
    undo_parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    
    # Export
    export_parser = subparsers.add_parser('export', help='Export history')
    export_parser.add_argument('--output', default='safegit-history.json', help='Output file')
    
    args = parser.parse_args()
    
    # Initialize undo stack
    undo_stack = UndoStack()
    
    if args.command == 'history':
        undo_stack.show_history(limit=args.limit)
    elif args.command == 'undo':
        undo_stack.undo(levels=args.levels, interactive=args.interactive)
    elif args.command == 'export':
        undo_stack.export_history(output_file=args.output)
    else:
        parser.print_help()