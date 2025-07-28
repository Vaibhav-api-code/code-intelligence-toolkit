#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Text Operation History System - Multi-level undo for all text editing operations

This module provides SafeGIT-style multi-level undo capabilities for text editing tools.
It tracks all text modifications with atomic operations and full recovery support.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-28
Updated: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import json
import time
import hashlib
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import fcntl
import gzip
from enum import Enum

class OperationType(Enum):
    """Types of text operations that can be tracked"""
    REPLACE_TEXT = "replace_text"
    REPLACE_AST = "replace_ast"
    UNIFIED_REFACTOR = "unified_refactor"
    MULTI_EDIT = "multi_edit"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"

@dataclass
class TextOperation:
    """Represents a single text operation with full metadata"""
    operation_id: str
    timestamp: float
    operation_type: OperationType
    file_path: str
    tool_name: str
    command_args: List[str]
    
    # Change details
    old_content_hash: str
    new_content_hash: str
    changes_count: int
    lines_affected: int
    
    # Backup information
    backup_path: str
    compressed: bool
    
    # Context
    user: str
    cwd: str
    description: str
    
    # Recovery
    can_undo: bool
    undo_command: str
    dependencies: List[str]  # Other operations this depends on
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['operation_type'] = self.operation_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TextOperation':
        """Create from dictionary"""
        data['operation_type'] = OperationType(data['operation_type'])
        return cls(**data)

class TextOperationHistory:
    """
    Manages multi-level undo history for text operations.
    
    Features:
    - Atomic operation tracking with file locking
    - Compressed backups for space efficiency
    - Operation dependency tracking
    - Recovery script generation
    - Cross-tool operation awareness
    """
    
    def __init__(self, history_dir: Optional[Path] = None):
        """Initialize the history system"""
        self.history_dir = history_dir or Path.home() / '.text_operation_history'
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.backups_dir = self.history_dir / 'backups'
        self.backups_dir.mkdir(exist_ok=True)
        
        self.metadata_dir = self.history_dir / 'metadata'
        self.metadata_dir.mkdir(exist_ok=True)
        
        self.recovery_dir = self.history_dir / 'recovery_scripts'
        self.recovery_dir.mkdir(exist_ok=True)
        
        # Main history file
        self.history_file = self.history_dir / 'operations.jsonl'
        self.lock_file = self.history_dir / '.lock'
        
        # Configuration
        self.max_history_size = 10000  # Maximum operations to keep
        self.max_backup_age_days = 30  # Auto-cleanup old backups
        self.compression_threshold = 1024  # Compress files larger than 1KB
    
    def _acquire_lock(self, timeout: float = 5.0) -> Optional[int]:
        """Acquire exclusive lock for atomic operations"""
        lock_fd = os.open(str(self.lock_file), os.O_CREAT | os.O_WRONLY)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return lock_fd
            except IOError:
                time.sleep(0.1)
        
        os.close(lock_fd)
        return None
    
    def _release_lock(self, lock_fd: int):
        """Release the exclusive lock"""
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return "ERROR"
    
    def _create_backup(self, file_path: Path, operation_id: str) -> Tuple[str, bool]:
        """Create a backup of the file, compress if large"""
        backup_name = f"{operation_id}_{file_path.name}"
        backup_path = self.backups_dir / backup_name
        
        try:
            file_size = file_path.stat().st_size
            compressed = file_size > self.compression_threshold
            
            if compressed:
                backup_path = backup_path.with_suffix('.gz')
                with open(file_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(file_path, backup_path)
            
            return str(backup_path), compressed
        except Exception as e:
            # If backup fails, create empty marker
            backup_path.touch()
            return str(backup_path), False
    
    def _generate_recovery_script(self, operation: TextOperation) -> Path:
        """Generate a recovery script for the operation"""
        script_path = self.recovery_dir / f"recover_{operation.operation_id}.sh"
        
        script_content = f"""#!/bin/bash
# Recovery script for operation {operation.operation_id}
# Generated: {datetime.fromtimestamp(operation.timestamp).isoformat()}
# Tool: {operation.tool_name}
# File: {operation.file_path}

set -e

echo "Recovering from operation {operation.operation_id}"
echo "Original file: {operation.file_path}"
echo "Backup: {operation.backup_path}"

# Check if backup exists
if [ ! -f "{operation.backup_path}" ]; then
    echo "ERROR: Backup file not found!"
    exit 1
fi

# Create safety backup of current state
SAFETY_BACKUP="/tmp/safety_backup_$(date +%s)_{Path(operation.file_path).name}"
cp "{operation.file_path}" "$SAFETY_BACKUP" 2>/dev/null || true

# Restore from backup
"""
        
        if operation.compressed:
            script_content += f'gunzip -c "{operation.backup_path}" > "{operation.file_path}"\n'
        else:
            script_content += f'cp "{operation.backup_path}" "{operation.file_path}"\n'
        
        script_content += f"""
echo "Recovery complete!"
echo "Safety backup of previous state: $SAFETY_BACKUP"

# Verify restoration
if [ -f "{operation.file_path}" ]; then
    echo "File restored successfully"
    ls -la "{operation.file_path}"
else
    echo "ERROR: Restoration failed!"
    exit 1
fi
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        script_path.chmod(0o755)
        return script_path
    
    def record_operation(self,
                        operation_type: OperationType,
                        file_path: Path,
                        tool_name: str,
                        command_args: List[str],
                        old_content: Optional[str] = None,
                        new_content: Optional[str] = None,
                        changes_count: int = 0,
                        description: str = "") -> Optional[TextOperation]:
        """Record a new text operation with backup"""
        
        lock_fd = self._acquire_lock()
        if not lock_fd:
            return None
        
        try:
            # Generate operation ID
            operation_id = f"{int(time.time() * 1000)}_{os.getpid()}"
            
            # Create backup if file exists
            backup_path = ""
            compressed = False
            if file_path.exists():
                backup_path, compressed = self._create_backup(file_path, operation_id)
            
            # Calculate hashes
            old_hash = self._calculate_file_hash(file_path) if file_path.exists() else "NEW_FILE"
            new_hash = hashlib.sha256(new_content.encode() if new_content else b"").hexdigest()
            
            # Count affected lines
            lines_affected = 0
            if old_content and new_content:
                old_lines = set(old_content.splitlines())
                new_lines = set(new_content.splitlines())
                lines_affected = len(old_lines.symmetric_difference(new_lines))
            
            # Create operation record
            operation = TextOperation(
                operation_id=operation_id,
                timestamp=time.time(),
                operation_type=operation_type,
                file_path=str(file_path),
                tool_name=tool_name,
                command_args=command_args,
                old_content_hash=old_hash,
                new_content_hash=new_hash,
                changes_count=changes_count,
                lines_affected=lines_affected,
                backup_path=backup_path,
                compressed=compressed,
                user=os.environ.get('USER', 'unknown'),
                cwd=os.getcwd(),
                description=description,
                can_undo=backup_path != "",
                undo_command=f"text_undo.py --operation {operation_id}",
                dependencies=[]
            )
            
            # Generate recovery script
            if operation.can_undo:
                self._generate_recovery_script(operation)
            
            # Append to history
            with open(self.history_file, 'a') as f:
                f.write(json.dumps(operation.to_dict()) + '\n')
            
            # Cleanup old operations if needed
            self._cleanup_old_operations()
            
            return operation
            
        finally:
            self._release_lock(lock_fd)
    
    def get_history(self, 
                   limit: int = 50,
                   file_path: Optional[Path] = None,
                   tool_name: Optional[str] = None,
                   since: Optional[float] = None) -> List[TextOperation]:
        """Get operation history with filters"""
        operations = []
        
        if not self.history_file.exists():
            return operations
        
        with open(self.history_file, 'r') as f:
            for line in f:
                try:
                    op_data = json.loads(line.strip())
                    op = TextOperation.from_dict(op_data)
                    
                    # Apply filters
                    if file_path and op.file_path != str(file_path):
                        continue
                    if tool_name and op.tool_name != tool_name:
                        continue
                    if since and op.timestamp < since:
                        continue
                    
                    operations.append(op)
                except Exception:
                    continue
        
        # Sort by timestamp descending
        operations.sort(key=lambda x: x.timestamp, reverse=True)
        
        return operations[:limit]
    
    def undo_operation(self, operation_id: str) -> Tuple[bool, str]:
        """Undo a specific operation"""
        # Find the operation
        operation = None
        for op in self.get_history(limit=self.max_history_size):
            if op.operation_id == operation_id:
                operation = op
                break
        
        if not operation:
            return False, f"Operation {operation_id} not found"
        
        if not operation.can_undo:
            return False, f"Operation {operation_id} cannot be undone (no backup)"
        
        # Check if backup exists
        backup_path = Path(operation.backup_path)
        if not backup_path.exists():
            return False, f"Backup file {backup_path} not found"
        
        # Create a new backup of current state before undoing
        current_backup_id = f"undo_{int(time.time() * 1000)}"
        file_path = Path(operation.file_path)
        
        if file_path.exists():
            current_backup, _ = self._create_backup(file_path, current_backup_id)
        
        # Restore from backup
        try:
            if operation.compressed:
                with gzip.open(backup_path, 'rb') as f_in:
                    content = f_in.read()
                with open(file_path, 'wb') as f_out:
                    f_out.write(content)
            else:
                shutil.copy2(backup_path, file_path)
            
            # Record the undo operation
            self.record_operation(
                operation_type=OperationType.REPLACE_TEXT,
                file_path=file_path,
                tool_name="text_undo",
                command_args=["undo", "--operation", operation_id],
                changes_count=1,
                description=f"Undo operation {operation_id}"
            )
            
            return True, f"Successfully undone operation {operation_id}"
            
        except Exception as e:
            return False, f"Failed to undo: {str(e)}"
    
    def _cleanup_old_operations(self):
        """Clean up old operations and backups"""
        cutoff_time = time.time() - (self.max_backup_age_days * 24 * 3600)
        
        # Read all operations
        all_operations = self.get_history(limit=self.max_history_size)
        
        # Keep only recent operations
        recent_operations = [op for op in all_operations if op.timestamp > cutoff_time]
        
        # Find backups to delete
        old_operations = [op for op in all_operations if op.timestamp <= cutoff_time]
        for op in old_operations:
            if op.backup_path:
                backup_path = Path(op.backup_path)
                if backup_path.exists():
                    backup_path.unlink()
        
        # Rewrite history file with recent operations only
        if len(recent_operations) < len(all_operations):
            with open(self.history_file, 'w') as f:
                for op in recent_operations:
                    f.write(json.dumps(op.to_dict()) + '\n')
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the history system"""
        all_operations = self.get_history(limit=self.max_history_size)
        
        stats = {
            'total_operations': len(all_operations),
            'total_backups': sum(1 for op in all_operations if op.can_undo),
            'operations_by_type': {},
            'operations_by_tool': {},
            'total_changes': sum(op.changes_count for op in all_operations),
            'backup_size_bytes': 0,
            'can_undo_count': sum(1 for op in all_operations if op.can_undo)
        }
        
        # Count by type and tool
        for op in all_operations:
            op_type = op.operation_type.value
            stats['operations_by_type'][op_type] = stats['operations_by_type'].get(op_type, 0) + 1
            stats['operations_by_tool'][op.tool_name] = stats['operations_by_tool'].get(op.tool_name, 0) + 1
        
        # Calculate backup size
        for backup_file in self.backups_dir.iterdir():
            if backup_file.is_file():
                stats['backup_size_bytes'] += backup_file.stat().st_size
        
        return stats

def get_history_instance() -> TextOperationHistory:
    """Get singleton instance of TextOperationHistory"""
    if not hasattr(get_history_instance, '_instance'):
        get_history_instance._instance = TextOperationHistory()
    return get_history_instance._instance