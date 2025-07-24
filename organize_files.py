#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Organize Files Tool - Automatic file organization based on rules with enhanced safety.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import shutil
import argparse
from safe_move import SafeMover, _enhanced_atomic_move, _enhanced_atomic_copy, FileLockError, ChecksumMismatchError, FileOperationError, _retry_operation, _wait_for_file_unlock, _is_file_locked
import sys
import json
import zipfile
import tarfile
import tempfile
import threading
import time
import fcntl
import errno
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import mimetypes

# Import standard argument parser
try:
    from enhanced_standard_arg_parser import create_standard_parser as create_parser
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

# Enhanced configuration from environment variables
DEFAULT_MAX_RETRIES = int(os.getenv("ORGANIZE_FILES_MAX_RETRIES", "3"))
DEFAULT_RETRY_DELAY = float(os.getenv("ORGANIZE_FILES_RETRY_DELAY", "0.5"))
DEFAULT_OPERATION_TIMEOUT = int(os.getenv("ORGANIZE_FILES_TIMEOUT", "30"))
DEFAULT_VERIFY_CHECKSUM = os.getenv("ORGANIZE_FILES_VERIFY_CHECKSUM", "false").lower() == "true"
DEFAULT_CONCURRENT_OPERATIONS = int(os.getenv("ORGANIZE_FILES_CONCURRENT", "4"))
DEFAULT_WAIT_FOR_UNLOCK = int(os.getenv("ORGANIZE_FILES_WAIT_UNLOCK", "10"))

# Global manifest lock for thread safety
_MANIFEST_LOCK = threading.Lock()

class FileOrganizer:
    """Handles automatic file organization based on various criteria."""
    
    # Default extension mappings
    EXTENSION_MAP = {
        # Images
        '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images',
        '.bmp': 'Images', '.svg': 'Images', '.webp': 'Images', '.tiff': 'Images',
        
        # Documents
        '.pdf': 'Documents', '.doc': 'Documents', '.docx': 'Documents',
        '.txt': 'Documents', '.rtf': 'Documents', '.odt': 'Documents',
        '.xls': 'Documents', '.xlsx': 'Documents', '.ppt': 'Documents', '.pptx': 'Documents',
        
        # Code
        '.py': 'Code', '.java': 'Code', '.js': 'Code', '.html': 'Code', '.css': 'Code',
        '.cpp': 'Code', '.c': 'Code', '.h': 'Code', '.php': 'Code', '.rb': 'Code',
        '.go': 'Code', '.rs': 'Code', '.ts': 'Code', '.jsx': 'Code', '.tsx': 'Code',
        
        # Scripts
        '.sh': 'Scripts', '.bat': 'Scripts', '.ps1': 'Scripts', '.cmd': 'Scripts',
        
        # Archives
        '.zip': 'Archives', '.rar': 'Archives', '.7z': 'Archives', '.tar': 'Archives',
        '.gz': 'Archives', '.bz2': 'Archives', '.xz': 'Archives',
        
        # Audio
        '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio', '.aac': 'Audio',
        '.ogg': 'Audio', '.m4a': 'Audio',
        
        # Video
        '.mp4': 'Video', '.avi': 'Video', '.mkv': 'Video', '.mov': 'Video',
        '.wmv': 'Video', '.flv': 'Video', '.webm': 'Video',
        
        # Data
        '.json': 'Data', '.xml': 'Data', '.csv': 'Data', '.sql': 'Data',
        '.yaml': 'Data', '.yml': 'Data', '.toml': 'Data',
    }
    
    def __init__(
        self, 
        dry_run: bool = False, 
        verbose: bool = False, 
        create_manifest: bool = False,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        operation_timeout: int = DEFAULT_OPERATION_TIMEOUT,
        verify_checksum: bool = DEFAULT_VERIFY_CHECKSUM,
        wait_for_unlock: int = DEFAULT_WAIT_FOR_UNLOCK,
        concurrent_operations: int = DEFAULT_CONCURRENT_OPERATIONS
    ):
        self.dry_run = dry_run
        self.verbose = verbose
        self.create_manifest = create_manifest
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.operation_timeout = operation_timeout
        self.verify_checksum = verify_checksum
        self.wait_for_unlock = wait_for_unlock
        self.concurrent_operations = concurrent_operations
        self.operations_count = 0
        self.stats = {'moved': 0, 'skipped': 0, 'errors': 0, 'locked_files': 0, 'checksum_failures': 0}
        self.manifest = []  # Track all operations for undo capability
        self.manifest_temp = None  # Temporary manifest file for atomic updates
        
        # Use a dedicated temp history/trash for each organiser instance so
        # running in test-harness or parallel processes is side-effect free.
        self._mover = SafeMover(
            dry_run=dry_run,
            verbose=verbose,
            undo_log=Path(tempfile.mkdtemp()) / "undo.log",
            trash_dir=Path(tempfile.mkdtemp()) / "trash",
            verify_checksum=verify_checksum,
            max_retries=max_retries,
            retry_delay=retry_delay,
            operation_timeout=operation_timeout,
        )
    
    def log_operation(self, operation: str, source: Path, dest: Path = None):
        """Log operation for reporting and manifest tracking."""
        if self.verbose:
            if dest:
                print(f"  {operation}: {source.name} → {dest}")
            else:
                print(f"  {operation}: {source.name}")
        
        # Add to manifest if enabled
        if self.create_manifest and not operation.startswith("WOULD"):
            operation_record = {
                'operation': operation,
                'source': str(source.absolute()),
                'destination': str(dest.absolute()) if dest else None,
                'timestamp': datetime.now().isoformat(),
                'operation_id': self.operations_count  # Add unique ID
            }
            
            # Update manifest incrementally for progress tracking
            self.update_manifest_incrementally(operation_record)
        
        self.operations_count += 1
    
    def safe_move_file(self, source: Path, dest_dir: Path) -> bool:
        """Safely move a file to destination directory with enhanced atomic operations."""
        try:
            if not self.dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / source.name
            
            # Handle name conflicts
            counter = 1
            original_dest = dest_path
            while dest_path.exists():
                stem = original_dest.stem
                suffix = original_dest.suffix
                dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            if self.dry_run:
                self.log_operation("WOULD MOVE", source, dest_path)
                return True
            
            # Check if source file is locked and wait if necessary
            is_locked, lock_info = _is_file_locked(source)
            if is_locked:
                if self.verbose:
                    print(f"⏳ File {source.name} is locked, waiting up to {self.wait_for_unlock}s...")
                
                if not _wait_for_file_unlock(source, self.wait_for_unlock):
                    print(f"❌ File {source.name} remains locked after {self.wait_for_unlock}s: {lock_info}")
                    self.stats['locked_files'] += 1
                    self.stats['errors'] += 1
                    return False
                elif self.verbose:
                    print(f"✅ File {source.name} unlocked, proceeding...")
            
            # Use enhanced atomic move operation with retry logic
            operation_result = _enhanced_atomic_move(
                source, 
                dest_path,
                verify_checksum=self.verify_checksum,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay,
                operation_timeout=self.operation_timeout
            )
            
            if operation_result.get('success', False):
                self.log_operation("MOVED", source, dest_path)
                self.stats['moved'] += 1
                if self.verbose and operation_result.get('checksum_verified'):
                    print(f"✓ Checksum verified for {source.name}")
                return True
            else:
                self.stats['errors'] += 1
                return False
                
        except FileLockError as e:
            print(f"🔒 File lock error for {source.name}: {e}")
            self.stats['locked_files'] += 1
            self.stats['errors'] += 1
            return False
        except ChecksumMismatchError as e:
            print(f"⚠️ Checksum verification failed for {source.name}: {e}")
            self.stats['checksum_failures'] += 1
            self.stats['errors'] += 1
            return False
        except FileOperationError as e:
            print(f"❌ File operation error for {source.name}: {e}")
            self.stats['errors'] += 1
            return False
        except Exception as e:
            print(f"❌ Unexpected error moving {source.name}: {e}")
            self.stats['errors'] += 1
            return False
    
    def organize_by_extension(self, source_dir: Path, custom_map: Dict[str, str] = None) -> Dict[str, int]:
        """Organize files by their extensions."""
        ext_map = custom_map or self.EXTENSION_MAP
        results = {}
        
        print(f"📂 Organizing '{source_dir}' by file extension...")
        
        files = [f for f in source_dir.iterdir() if f.is_file()]
        
        for file_path in files:
            ext = file_path.suffix.lower()
            folder_name = ext_map.get(ext, 'Other')
            
            dest_dir = source_dir / folder_name
            
            if self.safe_move_file(file_path, dest_dir):
                results[folder_name] = results.get(folder_name, 0) + 1
            else:
                self.stats['skipped'] += 1
        
        return results
    
    def organize_by_date(self, source_dir: Path, date_format: str = "%Y-%m") -> Dict[str, int]:
        """Organize files by their modification date."""
        results = {}
        
        print(f"📅 Organizing '{source_dir}' by date (format: {date_format})...")
        
        files = [f for f in source_dir.iterdir() if f.is_file()]
        
        for file_path in files:
            try:
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                folder_name = mod_time.strftime(date_format)
                
                dest_dir = source_dir / folder_name
                
                if self.safe_move_file(file_path, dest_dir):
                    results[folder_name] = results.get(folder_name, 0) + 1
                else:
                    self.stats['skipped'] += 1
                    
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                self.stats['errors'] += 1
        
        return results
    
    def organize_by_size(self, source_dir: Path, 
                        small_mb: float = 1.0, 
                        large_mb: float = 100.0) -> Dict[str, int]:
        """Organize files by their size."""
        results = {}
        
        print(f"📏 Organizing '{source_dir}' by size (< {small_mb}MB, < {large_mb}MB, >= {large_mb}MB)...")
        
        files = [f for f in source_dir.iterdir() if f.is_file()]
        
        for file_path in files:
            try:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                
                if size_mb < small_mb:
                    folder_name = "Small"
                elif size_mb < large_mb:
                    folder_name = "Medium"
                else:
                    folder_name = "Large"
                
                dest_dir = source_dir / folder_name
                
                if self.safe_move_file(file_path, dest_dir):
                    results[folder_name] = results.get(folder_name, 0) + 1
                else:
                    self.stats['skipped'] += 1
                    
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                self.stats['errors'] += 1
        
        return results
    
    def organize_by_type(self, source_dir: Path) -> Dict[str, int]:
        """Organize files by their MIME type."""
        results = {}
        
        print(f"🔍 Organizing '{source_dir}' by file type...")
        
        files = [f for f in source_dir.iterdir() if f.is_file()]
        
        for file_path in files:
            try:
                mime_type, _ = mimetypes.guess_type(str(file_path))
                
                if mime_type:
                    main_type = mime_type.split('/')[0].title()
                    if main_type == 'Application':
                        folder_name = "Applications"
                    elif main_type == 'Text':
                        folder_name = "Text"
                    else:
                        folder_name = main_type
                else:
                    folder_name = "Unknown"
                
                dest_dir = source_dir / folder_name
                
                if self.safe_move_file(file_path, dest_dir):
                    results[folder_name] = results.get(folder_name, 0) + 1
                else:
                    self.stats['skipped'] += 1
                    
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                self.stats['errors'] += 1
        
        return results
    
    def flatten_directory(self, source_dir: Path, target_dir: Path = None) -> int:
        """Flatten directory by moving all files from subdirectories to the root."""
        if target_dir is None:
            target_dir = source_dir
            
        print(f"📋 Flattening '{source_dir}' to '{target_dir}'...")
        moved_count = 0
        
        # Walk through all files in all subdirectories
        for root, _, files in os.walk(str(source_dir)):
            current_dir = Path(root)
            if current_dir == target_dir:
                continue # Skip the target directory itself

            for filename in files:
                item_path = current_dir / filename
                dest_path = target_dir / item_path.name
                
                # Handle name conflicts
                counter = 1
                original_dest = dest_path
                while dest_path.exists():
                    stem = original_dest.stem
                    suffix = original_dest.suffix
                    dest_path = target_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

                if self.dry_run:
                    self.log_operation("WOULD FLATTEN", item_path, dest_path)
                    moved_count += 1
                else:
                    try:
                        shutil.move(str(item_path), str(dest_path))
                        self.log_operation("FLATTENED", item_path, dest_path)
                        moved_count += 1
                    except Exception as e:
                        print(f"❌ Error flattening {item_path}: {e}")
        
        # Remove now-empty subdirectories
        if not self.dry_run:
            # Walk bottom-up to safely remove directories
            for root, dirs, _ in os.walk(str(source_dir), topdown=False):
                if Path(root) == target_dir:
                    continue
                for dirname in dirs:
                    try:
                        (Path(root) / dirname).rmdir()
                        if self.verbose:
                            print(f"  REMOVED EMPTY: {Path(root) / dirname}")
                    except OSError:
                        pass  # Directory not empty
        
        return moved_count
    
    def save_manifest(self, manifest_path: Path) -> bool:
        """Save operation manifest to file for undo capability with atomic updates."""
        if not self.manifest:
            return False
            
        try:
            # Use atomic update to prevent corruption
            with _MANIFEST_LOCK:
                manifest_data = {
                    'created': datetime.now().isoformat(),
                    'total_operations': len(self.manifest),
                    'operations': self.manifest,
                    'configuration': {
                        'max_retries': self.max_retries,
                        'retry_delay': self.retry_delay,
                        'operation_timeout': self.operation_timeout,
                        'verify_checksum': self.verify_checksum,
                        'wait_for_unlock': self.wait_for_unlock
                    },
                    'stats': self.stats.copy()
                }
                
                # Write to temporary file first, then atomically move
                temp_path = manifest_path.with_suffix('.tmp')
                with open(temp_path, 'w') as f:
                    json.dump(manifest_data, f, indent=2)
                
                # Atomic replace
                temp_path.replace(manifest_path)
            
            print(f"📋 Manifest saved to: {manifest_path}")
            if self.verbose:
                print(f"   Operations: {len(self.manifest)}")
                print(f"   Stats: moved={self.stats['moved']}, errors={self.stats['errors']}")
                if self.stats.get('locked_files', 0) > 0:
                    print(f"   Locked files: {self.stats['locked_files']}")
                if self.stats.get('checksum_failures', 0) > 0:
                    print(f"   Checksum failures: {self.stats['checksum_failures']}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving manifest: {e}")
            return False
    
    def update_manifest_incrementally(self, operation: Dict) -> bool:
        """Update manifest incrementally for long-running operations."""
        if not self.create_manifest:
            return True
            
        try:
            with _MANIFEST_LOCK:
                self.manifest.append(operation)
                
                # If we have a temporary manifest file, update it
                if self.manifest_temp and self.manifest_temp.exists():
                    manifest_data = {
                        'created': datetime.now().isoformat(),
                        'total_operations': len(self.manifest),
                        'operations': self.manifest,
                        'configuration': {
                            'max_retries': self.max_retries,
                            'retry_delay': self.retry_delay,
                            'operation_timeout': self.operation_timeout,
                            'verify_checksum': self.verify_checksum,
                            'wait_for_unlock': self.wait_for_unlock
                        },
                        'stats': self.stats.copy(),
                        'in_progress': True  # Mark as in-progress
                    }
                    
                    # Update temporary manifest
                    temp_update = self.manifest_temp.with_suffix('.update')
                    with open(temp_update, 'w') as f:
                        json.dump(manifest_data, f, indent=2)
                    temp_update.replace(self.manifest_temp)
                    
            return True
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Warning: Could not update incremental manifest: {e}")
            return False
    
    def archive_old_files(self, source_dir: Path, days_old: int, archive_name: str = None, 
                         compress_format: str = 'zip') -> int:
        """Archive files older than specified days into a compressed file."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        old_files = []
        
        # Find old files
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                try:
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        old_files.append(file_path)
                except Exception:
                    continue
        
        if not old_files:
            print(f"📂 No files older than {days_old} days found.")
            return 0
        
        # Generate archive name if not provided
        if not archive_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"archived_files_{timestamp}"
        
        archive_path = source_dir / f"{archive_name}.{compress_format}"
        
        if self.dry_run:
            print(f"🔍 [DRY RUN] Would archive {len(old_files)} files to {archive_path}")
            for file_path in old_files[:10]:  # Show first 10
                self.log_operation("WOULD ARCHIVE", file_path)
            if len(old_files) > 10:
                print(f"  ... and {len(old_files) - 10} more files")
            return len(old_files)
        
        try:
            # Create archive
            if compress_format == 'zip':
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_path in old_files:
                        rel_path = file_path.relative_to(source_dir)
                        zf.write(file_path, rel_path)
                        self.log_operation("ARCHIVED", file_path)
            elif compress_format in ['tar', 'tar.gz', 'tgz']:
                mode = 'w:gz' if compress_format in ['tar.gz', 'tgz'] else 'w'
                with tarfile.open(archive_path, mode) as tf:
                    for file_path in old_files:
                        rel_path = file_path.relative_to(source_dir)
                        tf.add(file_path, rel_path)
                        self.log_operation("ARCHIVED", file_path)
            
            # Remove original files after successful archiving
            for file_path in old_files:
                file_path.unlink()
                self.stats['moved'] += 1
            
            print(f"📦 Archived {len(old_files)} files to: {archive_path}")
            return len(old_files)
            
        except Exception as e:
            print(f"❌ Error creating archive: {e}")
            return 0
    
    def _read_file_with_retry(self, file_path: Path, max_retries: int = None, retry_delay: float = None) -> str:
        """Read file content with retry logic for locked files."""
        if max_retries is None:
            max_retries = int(os.getenv('ORGANIZE_FILES_READ_MAX_RETRIES', '3'))
        if retry_delay is None:
            retry_delay = float(os.getenv('ORGANIZE_FILES_READ_RETRY_DELAY', '0.5'))
        
        last_error = None
        for attempt in range(max_retries):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except OSError as e:
                last_error = e
                if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.ETXTBSY):
                    if attempt < max_retries - 1:
                        if not os.getenv('QUIET_MODE'):
                            print(f"File {file_path} is locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                raise FileOperationError(f"Failed to read {file_path} after {max_retries} attempts: {e}")
            except Exception as e:
                raise FileOperationError(f"Failed to read {file_path}: {e}")
    
    def load_rules_from_file(self, rules_file: Path) -> Dict[str, str]:
        """Load organization rules from JSON/YAML file."""
        try:
            content = self._read_file_with_retry(rules_file)
            if rules_file.suffix.lower() in ['.yaml', '.yml']:
                try:
                    import yaml
                    rules = yaml.safe_load(content)
                except ImportError:
                    print("❌ PyYAML not installed. Use JSON format or install PyYAML.")
                    return {}
            else:
                rules = json.loads(content)
            
            # Flatten nested rules if needed
            flattened = {}
            for pattern, destination in rules.items():
                if isinstance(destination, str):
                    flattened[pattern] = destination
                elif isinstance(destination, dict):
                    for subpattern, subdest in destination.items():
                        flattened[f"{pattern}.{subpattern}"] = subdest
            
            print(f"📋 Loaded {len(flattened)} rules from {rules_file}")
            return flattened
            
        except Exception as e:
            print(f"❌ Error loading rules file: {e}")
            return {}
    
    def print_summary(self, results: Dict[str, int]):
        """Print organization summary with enhanced statistics."""
        print("\n📊 Organization Summary:")
        print("-" * 50)
        
        for folder, count in sorted(results.items()):
            print(f"  {folder}: {count} files")
        
        print(f"\n✅ Total operations: {self.operations_count}")
        print(f"📁 Files moved: {self.stats['moved']}")
        print(f"⏭️  Files skipped: {self.stats['skipped']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        # Enhanced statistics
        if self.stats.get('locked_files', 0) > 0:
            print(f"🔒 Locked files encountered: {self.stats['locked_files']}")
        if self.stats.get('checksum_failures', 0) > 0:
            print(f"⚠️ Checksum verification failures: {self.stats['checksum_failures']}")
        
        # Configuration summary if verbose
        if self.verbose:
            print(f"\n🔧 Configuration used:")
            print(f"   Max retries: {self.max_retries}")
            print(f"   Retry delay: {self.retry_delay}s")
            print(f"   Operation timeout: {self.operation_timeout}s")
            print(f"   Checksum verification: {'enabled' if self.verify_checksum else 'disabled'}")
            print(f"   Wait for unlock: {self.wait_for_unlock}s")

def parse_custom_mapping(mapping_str: str) -> Dict[str, str]:
    """Parse custom extension mapping from command line."""
    mapping = {}
    
    for pair in mapping_str.split(','):
        if ':' in pair:
            ext, folder = pair.split(':', 1)
            mapping[ext.strip().lower()] = folder.strip()
    
    return mapping

def _read_manifest_with_retry(manifest_path: Path, max_retries: int = 3, retry_delay: float = 0.5) -> dict:
    """Read manifest file with retry logic for locked files."""
    last_error = None
    for attempt in range(max_retries):
        try:
            with open(manifest_path, 'r') as f:
                return json.load(f)
        except OSError as e:
            last_error = e
            if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.ETXTBSY):
                if attempt < max_retries - 1:
                    if not os.getenv('QUIET_MODE'):
                        print(f"Manifest {manifest_path} is locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
            raise FileOperationError(f"Failed to read manifest {manifest_path} after {max_retries} attempts: {e}")
        except Exception as e:
            raise FileOperationError(f"Failed to read manifest {manifest_path}: {e}")
    
    raise FileOperationError(f"Failed to read manifest {manifest_path} after {max_retries} attempts: {last_error}")

def undo_from_manifest(manifest_path: Path, dry_run: bool = False, verbose: bool = False) -> bool:
    """Undo organization operations from a manifest file."""
    try:
        manifest_data = _read_manifest_with_retry(manifest_path)
        operations = manifest_data.get('operations', [])
        if not operations:
            print("📋 No operations found in manifest.")
            return True
        
        print(f"📋 Found {len(operations)} operations to undo from {manifest_data.get('created', 'unknown date')}")
        
        if dry_run:
            print("🔍 [DRY RUN] Would undo the following operations:")
        
        undone_count = 0
        errors = 0
        
        # Reverse the operations to undo them in reverse order
        for operation in reversed(operations):
            op_type = operation.get('operation', '')
            source = Path(operation.get('source', ''))
            dest = Path(operation.get('destination', '')) if operation.get('destination') else None
            
            if verbose or dry_run:
                print(f"  {op_type}: {dest} → {source}" if dest else f"  {op_type}: {source}")
            
            if not dry_run and dest and dest.exists():
                try:
                    # Move file back to original location
                    source.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dest), str(source))
                    undone_count += 1
                    
                    # Clean up empty directories
                    try:
                        if dest.parent.is_dir() and not any(dest.parent.iterdir()):
                            dest.parent.rmdir()
                    except OSError:
                        pass
                        
                except Exception as e:
                    if verbose:
                        print(f"    ❌ Error undoing {dest}: {e}")
                    errors += 1
            elif dry_run:
                undone_count += 1
        
        if dry_run:
            print(f"\n📊 Would undo {undone_count} operations")
        else:
            print(f"\n📊 Successfully undone {undone_count} operations")
            if errors:
                print(f"❌ {errors} errors occurred during undo")
            
            # Move manifest to .undone to prevent accidental re-use
            undone_manifest = manifest_path.with_suffix('.undone.json')
            manifest_path.rename(undone_manifest)
            print(f"📋 Manifest moved to: {undone_manifest}")
        
        return errors == 0
        
    except Exception as e:
        print(f"❌ Error reading manifest: {e}")
        return False

def main():
    # Use clean ArgumentParser to avoid confusing options from standard parser
    parser = argparse.ArgumentParser(
        description="Organize files automatically based on rules with enhanced atomic operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Enhanced Features:
- Atomic file operations with automatic retry on failure
- File lock detection and waiting with configurable timeout  
- Optional checksum verification for data integrity
- Incremental manifest updates for progress tracking
- Enhanced error reporting with detailed statistics

Environment Variables:
- ORGANIZE_FILES_MAX_RETRIES: Maximum retry attempts (default: 3)
- ORGANIZE_FILES_RETRY_DELAY: Initial retry delay in seconds (default: 0.5)
- ORGANIZE_FILES_TIMEOUT: Operation timeout in seconds (default: 30)
- ORGANIZE_FILES_VERIFY_CHECKSUM: Enable checksum verification (default: false)
- ORGANIZE_FILES_CONCURRENT: Maximum concurrent operations (default: 4)
- ORGANIZE_FILES_WAIT_UNLOCK: Maximum wait time for locked files (default: 10)

Examples:
  organize_files.py ~/Downloads --by-ext --verbose --create-manifest
  organize_files.py ~/Documents --by-date "%Y-%m" --verify-checksum
  organize_files.py /tmp --archive-by-date 30 --max-retries 5
        """
    )
    
    parser.add_argument('directory', nargs='?', help='Directory to organize')
    
    # Standard options
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose output')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying')
    
    # Organization methods (mutually exclusive)
    method_group = parser.add_mutually_exclusive_group(required=True)
    method_group.add_argument('--by-ext', action='store_true',
                             help='Organize by file extension')
    method_group.add_argument('--by-date', metavar='FORMAT',
                             help='Organize by date (e.g., "%%Y-%%m" for year-month)')
    method_group.add_argument('--by-size', nargs=2, type=float, metavar=('SMALL', 'LARGE'),
                             help='Organize by size (small and large thresholds in MB)')
    method_group.add_argument('--by-type', action='store_true',
                             help='Organize by MIME type')
    method_group.add_argument('--flatten', action='store_true',
                             help='Flatten directory structure')
    method_group.add_argument('--archive-by-date', type=int, metavar='DAYS',
                             help='Archive files older than specified days')
    method_group.add_argument('--undo-manifest', metavar='MANIFEST_FILE',
                             help='Undo operations from manifest file')
    
    # Options
    parser.add_argument('--custom', metavar='MAPPING',
                       help='Custom extension mapping (e.g., ".log:Logs,.tmp:Temp")')
    parser.add_argument('--rules-file', metavar='RULES_FILE',
                       help='Load organization rules from JSON/YAML file')
    parser.add_argument('--create-manifest', action='store_true',
                       help='Create operation manifest for undo capability')
    parser.add_argument('--archive-format', choices=['zip', 'tar', 'tar.gz', 'tgz'], 
                       default='zip', help='Archive format (default: zip)')
    parser.add_argument('--archive-name', metavar='NAME',
                       help='Custom archive name (timestamp used if not specified)')
    
    # Enhanced atomic operations and retry control options
    parser.add_argument('--max-retries', type=int, default=DEFAULT_MAX_RETRIES,
                       help=f'Maximum retry attempts for failed operations (default: {DEFAULT_MAX_RETRIES})')
    parser.add_argument('--retry-delay', type=float, default=DEFAULT_RETRY_DELAY,
                       help=f'Initial delay between retries in seconds (default: {DEFAULT_RETRY_DELAY})')
    parser.add_argument('--operation-timeout', type=int, default=DEFAULT_OPERATION_TIMEOUT,
                       help=f'Timeout for individual operations in seconds (default: {DEFAULT_OPERATION_TIMEOUT})')
    parser.add_argument('--verify-checksum', action='store_true', default=DEFAULT_VERIFY_CHECKSUM,
                       help='Enable checksum verification for moved files')
    parser.add_argument('--wait-for-unlock', type=int, default=DEFAULT_WAIT_FOR_UNLOCK,
                       help=f'Maximum time to wait for locked files in seconds (default: {DEFAULT_WAIT_FOR_UNLOCK})')
    parser.add_argument('--concurrent-operations', type=int, default=DEFAULT_CONCURRENT_OPERATIONS,
                       help=f'Maximum concurrent file operations (default: {DEFAULT_CONCURRENT_OPERATIONS})')
    parser.add_argument('--no-verify-checksum', action='store_true',
                       help='Disable checksum verification (faster but less safe)')
    
    args = parser.parse_args()
    
    # Handle conflicting checksum options
    if args.no_verify_checksum:
        verify_checksum = False
    else:
        verify_checksum = args.verify_checksum
    
    # Handle undo manifest operation separately
    if args.undo_manifest:
        manifest_path = Path(args.undo_manifest)
        if not manifest_path.exists():
            print(f"❌ Error: Manifest file '{manifest_path}' does not exist.")
            return 1
        return 0 if undo_from_manifest(manifest_path, args.dry_run, args.verbose) else 1
    
    # Validate directory for other operations
    if not args.directory:
        print("❌ Error: Directory argument is required for organization operations.")
        parser.print_help()
        return 1
    
    source_dir = Path(args.directory).resolve()
    if not source_dir.exists():
        print(f"❌ Error: Directory '{source_dir}' does not exist.")
        return 1
    
    if not source_dir.is_dir():
        print(f"❌ Error: '{source_dir}' is not a directory.")
        return 1
    
    # Initialize organizer with enhanced configuration
    organizer = FileOrganizer(
        dry_run=args.dry_run, 
        verbose=args.verbose, 
        create_manifest=args.create_manifest,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        operation_timeout=args.operation_timeout,
        verify_checksum=verify_checksum,
        wait_for_unlock=args.wait_for_unlock,
        concurrent_operations=args.concurrent_operations
    )
    
    # Show configuration summary
    if args.verbose or args.dry_run:
        print(f"🔧 Configuration:")
        print(f"   Max retries: {args.max_retries}")
        print(f"   Retry delay: {args.retry_delay}s")
        print(f"   Operation timeout: {args.operation_timeout}s")
        print(f"   Checksum verification: {'enabled' if verify_checksum else 'disabled'}")
        print(f"   Wait for unlock: {args.wait_for_unlock}s")
        print(f"   Concurrent operations: {args.concurrent_operations}")
        print("-" * 50)
    
    # Show dry run warning
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be moved")
        print("-" * 50)
    
    # Create temporary manifest for progress tracking in long operations
    if args.create_manifest and not args.dry_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        organizer.manifest_temp = source_dir / f"organization_manifest_{timestamp}.temp.json"
        if args.verbose:
            print(f"📋 Progress will be tracked in: {organizer.manifest_temp}")
            print("-" * 50)
    
    # Execute organization method
    results = {}
    
    if args.archive_by_date:
        archived_count = organizer.archive_old_files(
            source_dir, args.archive_by_date, 
            args.archive_name, args.archive_format
        )
        results = {'Archived': archived_count}
        
    elif args.rules_file:
        rules_path = Path(args.rules_file)
        if not rules_path.exists():
            print(f"❌ Error: Rules file '{rules_path}' does not exist.")
            return 1
        
        custom_map = organizer.load_rules_from_file(rules_path)
        if custom_map:
            results = organizer.organize_by_extension(source_dir, custom_map)
        else:
            return 1
    
    elif args.by_ext:
        custom_map = None
        if args.custom:
            custom_map = parse_custom_mapping(args.custom)
            # Merge with default map
            full_map = organizer.EXTENSION_MAP.copy()
            full_map.update(custom_map)
            custom_map = full_map
        
        results = organizer.organize_by_extension(source_dir, custom_map)
        
    elif args.by_date:
        results = organizer.organize_by_date(source_dir, args.by_date)
        
    elif args.by_size:
        small_mb, large_mb = args.by_size
        results = organizer.organize_by_size(source_dir, small_mb, large_mb)
        
    elif args.by_type:
        results = organizer.organize_by_type(source_dir)
        
    elif args.flatten:
        moved_count = organizer.flatten_directory(source_dir)
        results = {'Flattened': moved_count}
    
    # Save manifest if requested
    if args.create_manifest and organizer.manifest:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_path = source_dir / f"organization_manifest_{timestamp}.json"
        organizer.save_manifest(manifest_path)
        
        # Clean up temporary manifest file
        if organizer.manifest_temp and organizer.manifest_temp.exists():
            try:
                organizer.manifest_temp.unlink()
                if args.verbose:
                    print(f"🧹 Cleaned up temporary manifest: {organizer.manifest_temp}")
            except Exception as e:
                if args.verbose:
                    print(f"⚠️ Warning: Could not clean up temporary manifest: {e}")
    
    # Handle case where no operations were performed but manifest was requested
    elif args.create_manifest and not organizer.manifest:
        print("📋 No operations to save in manifest")
        # Still clean up temporary manifest if it exists
        if organizer.manifest_temp and organizer.manifest_temp.exists():
            try:
                organizer.manifest_temp.unlink()
            except Exception:
                pass
    
    # Print summary
    organizer.print_summary(results)
    
    return 0 if organizer.stats['errors'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())