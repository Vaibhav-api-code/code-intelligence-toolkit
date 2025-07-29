#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Safe File Manager Undo Integration - Deep integration with safe_file_manager's transaction system.

This module provides a hook-based approach to integrate the multi-level undo system
with safe_file_manager.py without modifying the core tool.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Import the undo system
try:
    from text_operation_history import (
        TextOperationHistory, OperationType, get_history_instance
    )
    HAS_UNDO_SYSTEM = True
except ImportError:
    HAS_UNDO_SYSTEM = False

class SafeFileManagerUndoHook:
    """Hook class that integrates with safe_file_manager's transaction system."""
    
    def __init__(self):
        self.history = get_history_instance() if HAS_UNDO_SYSTEM else None
        self.pending_operations = {}
        
    def before_operation(self, operation_type: str, file_path: Path, **kwargs) -> Optional[str]:
        """Called before a file operation begins."""
        if not self.history:
            return None
            
        operation_id = f"{operation_type}_{file_path}_{datetime.now().timestamp()}"
        
        # Capture current state for operations that modify existing files
        old_content = None
        if file_path.exists() and operation_type in ['write', 'move', 'trash', 'chmod', 'chown']:
            try:
                old_content = file_path.read_text(encoding='utf-8')
            except:
                # Binary file or permission issue
                pass
                
        self.pending_operations[operation_id] = {
            'operation_type': operation_type,
            'file_path': file_path,
            'old_content': old_content,
            'kwargs': kwargs,
            'start_time': datetime.now()
        }
        
        return operation_id
        
    def after_operation(self, operation_id: str, success: bool, new_path: Optional[Path] = None) -> None:
        """Called after a file operation completes."""
        if not self.history or operation_id not in self.pending_operations:
            return
            
        if not success:
            # Operation failed, remove from pending
            del self.pending_operations[operation_id]
            return
            
        op_data = self.pending_operations[operation_id]
        file_path = op_data['file_path']
        old_content = op_data['old_content']
        
        # Determine the operation type for undo system
        op_type_map = {
            'create': OperationType.CREATE,
            'write': OperationType.WRITE,
            'copy': OperationType.CREATE,
            'move': OperationType.RENAME,
            'trash': OperationType.DELETE,
            'chmod': OperationType.MODIFY,
            'chown': OperationType.MODIFY,
        }
        
        undo_op_type = op_type_map.get(op_data['operation_type'], OperationType.MODIFY)
        
        # Get new content for certain operations
        new_content = None
        if op_data['operation_type'] in ['create', 'write', 'copy']:
            target_path = new_path or file_path
            if target_path.exists():
                try:
                    new_content = target_path.read_text(encoding='utf-8')
                except:
                    pass
                    
        # Record the operation
        try:
            operation = self.history.record_operation(
                operation_type=undo_op_type,
                file_path=file_path,
                tool_name="safe_file_manager",
                command_args=sys.argv[1:],
                old_content=old_content,
                new_content=new_content,
                changes_count=1,
                description=f"{op_data['operation_type']} {file_path}"
            )
            
            if operation:
                print(f"✓ Undo tracking: {operation.operation_id}")
                
        except Exception as e:
            print(f"Warning: Could not track undo: {e}", file=sys.stderr)
            
        # Clean up
        del self.pending_operations[operation_id]


def create_undo_config() -> Dict[str, Any]:
    """Create configuration for safe_file_manager with undo hooks."""
    hook = SafeFileManagerUndoHook()
    
    return {
        'hooks': {
            'before_operation': hook.before_operation,
            'after_operation': hook.after_operation
        },
        'undo_enabled': HAS_UNDO_SYSTEM
    }


def inject_undo_hooks():
    """Inject undo hooks into safe_file_manager's configuration."""
    config_path = Path.home() / '.safe_file_manager' / 'undo_hooks.json'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = create_undo_config()
    
    # Write hook configuration
    with open(config_path, 'w') as f:
        json.dump({
            'undo_integration': {
                'enabled': True,
                'module': 'sfm_undo_integration',
                'class': 'SafeFileManagerUndoHook'
            }
        }, f, indent=2)
        
    print(f"✓ Undo hooks configured at: {config_path}")


if __name__ == "__main__":
    # When run directly, configure the hooks
    inject_undo_hooks()
    
    # Also provide a way to disable
    if len(sys.argv) > 1 and sys.argv[1] == 'disable':
        config_path = Path.home() / '.safe_file_manager' / 'undo_hooks.json'
        if config_path.exists():
            config_path.unlink()
            print("✓ Undo hooks disabled")
