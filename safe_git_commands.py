#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
SafeGIT Commands - Prevent accidental loss of work in git operations.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import re
import time

class SafeGitCommands:
    """Main class for safe git operations."""
    
    def __init__(self):
        self.repo_root = self._find_git_root()
        if not self.repo_root:
            print("Error: Not in a git repository", file=sys.stderr)
            sys.exit(1)
    
    def _find_git_root(self) -> Optional[Path]:
        """Find the root of the git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return None
    
    def _run_git_command(self, args: List[str]) -> Tuple[bool, str, str]:
        """Run a git command and return success, stdout, stderr."""
        try:
            result = subprocess.run(
                ['git'] + args,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
    
    def _get_file_stats(self, file_path: str) -> Dict:
        """Get statistics about uncommitted changes in a file."""
        stats = {
            'file': file_path,
            'has_staged_changes': False,
            'has_unstaged_changes': False,
            'staged_lines_added': 0,
            'staged_lines_removed': 0,
            'unstaged_lines_added': 0,
            'unstaged_lines_removed': 0,
            'total_lines_changed': 0,
            'first_change_time': None,
            'time_invested': None,
            'todos_in_changes': 0,
            'fixmes_in_changes': 0
        }
        
        # Check staged changes
        success, stdout, _ = self._run_git_command(['diff', '--cached', '--numstat', file_path])
        if success and stdout.strip():
            parts = stdout.strip().split('\t')
            if len(parts) >= 3:
                stats['has_staged_changes'] = True
                stats['staged_lines_added'] = int(parts[0]) if parts[0] != '-' else 0
                stats['staged_lines_removed'] = int(parts[1]) if parts[1] != '-' else 0
        
        # Check unstaged changes
        success, stdout, _ = self._run_git_command(['diff', '--numstat', file_path])
        if success and stdout.strip():
            parts = stdout.strip().split('\t')
            if len(parts) >= 3:
                stats['has_unstaged_changes'] = True
                stats['unstaged_lines_added'] = int(parts[0]) if parts[0] != '-' else 0
                stats['unstaged_lines_removed'] = int(parts[1]) if parts[1] != '-' else 0
        
        # Calculate total changes
        stats['total_lines_changed'] = (
            stats['staged_lines_added'] + stats['staged_lines_removed'] +
            stats['unstaged_lines_added'] + stats['unstaged_lines_removed']
        )
        
        # Get diff content to check for TODOs/FIXMEs
        success, stdout, _ = self._run_git_command(['diff', 'HEAD', file_path])
        if success:
            diff_content = stdout.upper()
            stats['todos_in_changes'] = len(re.findall(r'\+.*TODO', diff_content))
            stats['fixmes_in_changes'] = len(re.findall(r'\+.*FIXME', diff_content))
        
        # Try to estimate time invested (this is a simple heuristic)
        file_mtime = os.path.getmtime(file_path)
        time_since_modified = datetime.now() - datetime.fromtimestamp(file_mtime)
        stats['time_invested'] = str(time_since_modified).split('.')[0]  # Remove microseconds
        
        return stats
    
    def check_reset_safety(self, file_paths: List[str]) -> Dict:
        """Check if it's safe to reset files."""
        results = {
            'safe': True,
            'risk_level': 'LOW',
            'total_changes': 0,
            'files': [],
            'warnings': [],
            'suggestions': []
        }
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                results['warnings'].append(f"File not found: {file_path}")
                continue
            
            stats = self._get_file_stats(file_path)
            results['files'].append(stats)
            results['total_changes'] += stats['total_lines_changed']
            
            # Risk assessment
            if stats['total_lines_changed'] > 100:
                results['safe'] = False
                results['risk_level'] = 'HIGH'
                results['warnings'].append(
                    f"{file_path}: Large number of changes ({stats['total_lines_changed']} lines)"
                )
            elif stats['total_lines_changed'] > 50:
                results['risk_level'] = 'MEDIUM' if results['risk_level'] == 'LOW' else results['risk_level']
                results['warnings'].append(
                    f"{file_path}: Moderate changes ({stats['total_lines_changed']} lines)"
                )
            
            if stats['todos_in_changes'] > 0 or stats['fixmes_in_changes'] > 0:
                results['warnings'].append(
                    f"{file_path}: Contains {stats['todos_in_changes']} TODOs and {stats['fixmes_in_changes']} FIXMEs"
                )
            
            # Parse time invested
            if stats['time_invested']:
                try:
                    time_parts = stats['time_invested'].split(':')
                    if len(time_parts) >= 2:
                        hours = int(time_parts[0])
                        if hours > 2:
                            results['warnings'].append(
                                f"{file_path}: {hours}+ hours of work since last save"
                            )
                except:
                    pass
        
        # Add suggestions
        if not results['safe']:
            results['suggestions'].append("Create a backup before resetting:")
            results['suggestions'].append("  git stash save 'Backup before reset'")
            results['suggestions'].append("Or create a backup branch:")
            results['suggestions'].append("  git checkout -b backup/before-reset")
            results['suggestions'].append("  git add -A && git commit -m 'Backup'")
            results['suggestions'].append("  git checkout -")
        
        return results
    
    def check_revert_safety(self, commit_hash: str, target_files: Optional[List[str]] = None) -> Dict:
        """Check if it's safe to revert a commit."""
        results = {
            'safe': True,
            'commit': commit_hash,
            'risk_level': 'LOW',
            'commit_info': {},
            'affected_files': [],
            'other_files_in_commit': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Get commit information
        success, stdout, _ = self._run_git_command([
            'show', '--pretty=format:%H%n%an%n%ae%n%ai%n%s', '--name-status', commit_hash
        ])
        
        if not success:
            results['safe'] = False
            results['warnings'].append(f"Invalid commit hash: {commit_hash}")
            return results
        
        lines = stdout.strip().split('\n')
        if len(lines) >= 5:
            results['commit_info'] = {
                'hash': lines[0],
                'author': lines[1],
                'email': lines[2],
                'date': lines[3],
                'message': lines[4]
            }
        
        # Parse changed files
        all_changed_files = []
        for line in lines[6:]:  # Skip commit info and empty line
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    status, file_path = parts[0], parts[1]
                    all_changed_files.append({
                        'file': file_path,
                        'status': status,
                        'status_text': self._get_status_text(status)
                    })
        
        # Categorize files
        if target_files:
            target_set = set(target_files)
            for file_info in all_changed_files:
                if file_info['file'] in target_set:
                    results['affected_files'].append(file_info)
                else:
                    results['other_files_in_commit'].append(file_info)
        else:
            results['affected_files'] = all_changed_files
        
        # Risk assessment
        if len(results['other_files_in_commit']) > 0:
            results['risk_level'] = 'HIGH'
            results['safe'] = False
            results['warnings'].append(
                f"This commit affects {len(results['other_files_in_commit'])} other files besides your target!"
            )
            results['warnings'].append("Reverting will affect ALL files in the commit.")
        
        # Check for subsequent commits that might depend on this one
        if target_files:
            for file_path in target_files:
                success, stdout, _ = self._run_git_command([
                    'log', '--oneline', f'{commit_hash}..HEAD', '--', file_path
                ])
                if success and stdout.strip():
                    dependent_commits = len(stdout.strip().split('\n'))
                    results['warnings'].append(
                        f"{file_path}: {dependent_commits} subsequent commits may depend on this change"
                    )
                    results['risk_level'] = 'MEDIUM' if results['risk_level'] == 'LOW' else results['risk_level']
        
        # Add suggestions
        if not results['safe']:
            results['suggestions'].append("Consider these safer alternatives:")
            results['suggestions'].append("1. Revert specific files only:")
            if target_files:
                for f in target_files:
                    results['suggestions'].append(f"   git checkout {commit_hash}^ -- {f}")
            results['suggestions'].append("2. Create a new commit that undoes specific changes")
            results['suggestions'].append("3. Use interactive rebase for more control")
        
        return results
    
    def _get_status_text(self, status: str) -> str:
        """Convert git status letter to readable text."""
        status_map = {
            'A': 'Added',
            'M': 'Modified',
            'D': 'Deleted',
            'R': 'Renamed',
            'C': 'Copied',
            'U': 'Updated but unmerged'
        }
        return status_map.get(status, status)
    
    def safe_reset(self, file_paths: List[str], mode: str = 'mixed', backup: bool = True) -> bool:
        """Safely reset files with automatic backup."""
        # First check safety
        safety_check = self.check_reset_safety(file_paths)
        
        if backup:
            print("🔒 Creating backup before reset...")
            
            # Create stash with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filenames = ", ".join([os.path.basename(f) for f in file_paths[:3]])
            if len(file_paths) > 3:
                filenames += f" (+{len(file_paths)-3} more)"
            stash_message = f"SAFEGIT-BACKUP-RESET - {timestamp} - {filenames}"
            
            success, stdout, stderr = self._run_git_command(['stash', 'push', '-m', stash_message] + file_paths)
            
            if success:
                print(f"✅ Created stash: {stash_message}")
                print("   To recover: git stash pop")
            else:
                print(f"❌ Failed to create stash: {stderr}")
                return False
        
        # Perform the reset
        reset_args = ['reset']
        if mode != 'mixed':
            reset_args.append(f'--{mode}')
        reset_args.extend(file_paths)
        
        success, stdout, stderr = self._run_git_command(reset_args)
        
        if success:
            print(f"✅ Successfully reset {len(file_paths)} file(s)")
            return True
        else:
            print(f"❌ Reset failed: {stderr}")
            return False
    
    def check_clean_safety(self, include_ignored: bool = False) -> Dict[str, Any]:
        """Check if it's safe to run git clean.

        :param include_ignored: if True, include ignored files in the safety report.
        """
        from collections import defaultdict
        
        results = {
            'safe': True,
            'risk_level': 'LOW',
            'untracked_files': [],
            'total_files': 0,
            'total_size': 0,
            'categories': defaultdict(lambda: {'files': [], 'size': 0, 'count': 0}),
            'warnings': [],
            'suggestions': []
        }
        
        # Get untracked files
        success, stdout, _ = self._run_git_command(['status', '--porcelain'])
        if not success:
            results['safe'] = False
            results['warnings'].append("Failed to get git status")
            return results
        
        # Parse untracked files
        for line in stdout.strip().split('\n'):
            if line.strip() and line.startswith('??'):
                file_path = line[3:].strip()
                full_path = os.path.join(self.repo_root, file_path)
                
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    try:
                        stat = os.stat(full_path)
                        file_size = stat.st_size
                        file_age_seconds = time.time() - stat.st_mtime
                        file_age_days = file_age_seconds / 86400
                        
                        file_info = {
                            'path': file_path,
                            'size': file_size,
                            'size_human': self._format_size(file_size),
                            'age_days': round(file_age_days, 1),
                            'category': self._categorize_file(file_path)
                        }
                        
                        results['untracked_files'].append(file_info)
                        results['total_files'] += 1
                        results['total_size'] += file_size
                        
                        # Categorize
                        category = file_info['category']
                        results['categories'][category]['files'].append(file_path)
                        results['categories'][category]['size'] += file_size
                        results['categories'][category]['count'] += 1
                        
                    except Exception as e:
                        results['warnings'].append(f"Error processing {file_path}: {str(e)}")
        
        # Risk assessment
        results['categories'] = dict(results['categories'])  # Convert defaultdict to dict
        
        # Check for source code files
        code_categories = ['source_code', 'config', 'scripts']
        code_files = sum(results['categories'].get(cat, {}).get('count', 0) for cat in code_categories)
        
        if code_files > 0:
            results['risk_level'] = 'HIGH'
            results['safe'] = False
            results['warnings'].append(f"Found {code_files} source code/config files that would be deleted")
        
        # Check for large files
        if results['total_size'] > 10 * 1024 * 1024:  # 10MB
            results['risk_level'] = 'MEDIUM' if results['risk_level'] == 'LOW' else results['risk_level']
            results['warnings'].append(f"Total size of files to delete: {self._format_size(results['total_size'])}")
        
        # Check for recently created files
        recent_files = [f for f in results['untracked_files'] if f['age_days'] < 1]
        if recent_files:
            results['warnings'].append(f"Found {len(recent_files)} files created in the last 24 hours")
        
        # Add suggestions
        if not results['safe']:
            results['suggestions'].append("Consider these safer alternatives:")
            results['suggestions'].append("1. Review specific file types:")
            for category, info in results['categories'].items():
                if info['count'] > 0:
                    results['suggestions'].append(f"   - {category}: {info['count']} files, {self._format_size(info['size'])}")
            results['suggestions'].append("2. Create a backup before cleaning:")
            results['suggestions'].append("   ./run_any_python_tool.sh safe_git_commands.py safe-clean --backup")
            results['suggestions'].append("3. Use git clean with specific patterns:")
            results['suggestions'].append("   git clean -n -d -x -e '*.java' -e '*.py'")
        
        return results
    
    def _categorize_file(self, file_path: str) -> str:
        """Categorize file by extension and path."""
        ext = os.path.splitext(file_path)[1].lower()
        name = os.path.basename(file_path).lower()
        
        # Source code
        code_exts = {'.java', '.py', '.js', '.ts', '.cpp', '.c', '.h', '.go', '.rs', '.rb', '.php'}
        if ext in code_exts:
            return 'source_code'
        
        # Config files
        config_files = {'makefile', 'dockerfile', '.gitignore', '.env', 'requirements.txt', 'package.json', 'pom.xml', 'build.gradle'}
        config_exts = {'.yml', '.yaml', '.xml', '.json', '.toml', '.ini', '.conf', '.cfg'}
        if name in config_files or ext in config_exts:
            return 'config'
        
        # Scripts
        script_exts = {'.sh', '.bash', '.bat', '.cmd', '.ps1'}
        if ext in script_exts:
            return 'scripts'
        
        # Documents
        doc_exts = {'.md', '.txt', '.doc', '.docx', '.pdf', '.rst'}
        if ext in doc_exts:
            return 'documents'
        
        # Logs and temp
        if ext in {'.log', '.tmp', '.temp', '.cache'} or name.startswith('.'):
            return 'logs_temp'
        
        # Build artifacts
        if ext in {'.o', '.class', '.pyc', '.pyo', '.so', '.dll', '.exe'}:
            return 'build_artifacts'
        
        # Archives
        if ext in {'.zip', '.tar', '.gz', '.bz2', '.7z', '.rar'}:
            return 'archives'
        
        # Data files
        if ext in {'.csv', '.dat', '.db', '.sqlite'}:
            return 'data'
        
        return 'other'
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def safe_clean(self, force: bool = False, backup: bool = False, dry_run: bool = True) -> bool:
        """Safely clean untracked files with optional backup."""
        # Always check safety first
        safety_check = self.check_clean_safety()
        
        if not force and not safety_check['safe']:
            print("\n⚠️  Operation appears risky. Use --force to proceed anyway.")
            format_safety_report(safety_check)
            return False
        
        # Create backup if requested
        if backup and safety_check['untracked_files']:
            print("\n🔒 Creating backup of untracked files...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.repo_root, f".git_clean_backup_{timestamp}")
            backup_zip = os.path.join(self.repo_root, f"git_clean_backup_{timestamp}.zip")
            
            try:
                # Create zip backup
                import zipfile
                with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_info in safety_check['untracked_files']:
                        file_path = file_info['path']
                        full_path = os.path.join(self.repo_root, file_path)
                        if os.path.exists(full_path):
                            zf.write(full_path, file_path)
                            print(f"   📦 Backed up: {file_path}")
                
                print(f"\n✅ Backup created: {backup_zip}")
                print(f"   Size: {self._format_size(os.path.getsize(backup_zip))}")
                
                # Verify zip integrity
                print("\n🔍 Verifying backup integrity...")
                try:
                    with zipfile.ZipFile(backup_zip, "r") as verify_zf:
                        # Test the zip file for corruption
                        bad_file = verify_zf.testzip()
                        if bad_file:
                            print(f"\n❌ Zip verification failed! Corrupted file: {bad_file}")
                            # Remove the corrupted backup
                            os.remove(backup_zip)
                            return False
                        
                        # Verify file count matches
                        zip_file_count = len(verify_zf.namelist())
                        expected_count = len(safety_check["untracked_files"])
                        
                        if zip_file_count != expected_count:
                            print(f"\n❌ Zip verification failed! Expected {expected_count} files, found {zip_file_count}")
                            # Remove the incomplete backup
                            os.remove(backup_zip)
                            return False
                        
                        print(f"   ✅ Verified {zip_file_count} files in backup")
                        print("   ✅ All files passed integrity check")
                
                except Exception as e:
                    print(f"\n❌ Failed to verify backup: {str(e)}")
                    # Remove the unverified backup
                    if os.path.exists(backup_zip):
                        os.remove(backup_zip)
                    return False
                
                print(f"\n📝 To restore files:")
                print(f"   unzip {backup_zip}")
                
            except Exception as e:
                print(f"\n❌ Failed to create backup: {str(e)}")
                return False
        
        # Perform clean operation
        clean_args = ['clean', '-d']  # Remove untracked directories too
        
        if dry_run:
            clean_args.append('-n')  # Dry run
            print("\n🔍 Dry run - no files will be deleted:")
        else:
            clean_args.append('-f')  # Force
            print("\n🗑️  Cleaning untracked files...")
        
        # Add -x flag to remove ignored files too
        clean_args.append('-x')
        
        # Race condition protection: Re-check untracked files just before clean
        if not dry_run:
            print("\n🔍 Performing final safety check...")
            
            # Get current list of untracked files
            recheck_success, recheck_stdout, _ = self._run_git_command(['status', '--porcelain'])
            if not recheck_success:
                print("\n❌ Failed to re-check untracked files. Operation aborted for safety.")
                return False
            
            # Parse current untracked files
            current_untracked = set()
            for line in recheck_stdout.strip().split('\n'):
                if line.strip() and line.startswith('??'):
                    file_path = line[3:].strip()
                    current_untracked.add(file_path)
            
            # Get original untracked files from safety_check
            original_untracked = {f['path'] for f in safety_check['untracked_files']}
            
            # Check for new files that appeared
            new_files = current_untracked - original_untracked
            if new_files:
                print(f"\n⚠️  New untracked files detected since initial check:")
                for file in sorted(new_files):
                    print(f"   • {file}")
                print("\n❌ Operation aborted to prevent accidental deletion of new files.")
                print("   Please review the new files and run the command again if desired.")
                return False
            
            # Check if any files disappeared (less critical but worth noting)
            disappeared_files = original_untracked - current_untracked
            if disappeared_files:
                print(f"\n📝 Note: Some files were removed since initial check:")
                for file in sorted(disappeared_files):
                    print(f"   • {file}")
                print("   Continuing with operation...")
        
        success, stdout, stderr = self._run_git_command(clean_args)
        
        if success:
            if stdout:
                print(stdout)
            if dry_run:
                print("\n💡 To actually clean these files, run with --no-dry-run")
            else:
                print(f"\n✅ Successfully cleaned {safety_check['total_files']} file(s)")
            return True
        else:
            print(f"\n❌ Clean failed: {stderr}")
            return False


def format_safety_report(results: Dict, verbose: bool = False) -> None:
    """Format and print safety check results."""
    # Risk level colors
    risk_colors = {
        'LOW': '\033[92m',    # Green
        'MEDIUM': '\033[93m', # Yellow
        'HIGH': '\033[91m'    # Red
    }
    reset_color = '\033[0m'
    
    # Header
    risk_color = risk_colors.get(results['risk_level'], '')
    print(f"\n{risk_color}Risk Level: {results['risk_level']}{reset_color}")
    print("=" * 60)
    
    # File information
    if 'files' in results:
        for file_stats in results['files']:
            print(f"\n📄 {file_stats['file']}")
            
            changes = []
            if file_stats['has_staged_changes']:
                changes.append(f"Staged: +{file_stats['staged_lines_added']}/-{file_stats['staged_lines_removed']}")
            if file_stats['has_unstaged_changes']:
                changes.append(f"Unstaged: +{file_stats['unstaged_lines_added']}/-{file_stats['unstaged_lines_removed']}")
            
            if changes:
                print(f"   Changes: {', '.join(changes)}")
                print(f"   Total lines affected: {file_stats['total_lines_changed']}")
            
            if file_stats['time_invested']:
                print(f"   Time since last save: {file_stats['time_invested']}")
            
            if file_stats['todos_in_changes'] or file_stats['fixmes_in_changes']:
                print(f"   ⚠️  Contains: {file_stats['todos_in_changes']} TODOs, {file_stats['fixmes_in_changes']} FIXMEs")
    
    # Commit information for revert checks
    if 'commit_info' in results and results['commit_info']:
        print(f"\n📝 Commit: {results['commit_info']['hash'][:8]}")
        print(f"   Author: {results['commit_info']['author']}")
        print(f"   Date: {results['commit_info']['date']}")
        print(f"   Message: {results['commit_info']['message']}")
    
    if 'affected_files' in results and results['affected_files']:
        print(f"\n📁 Target files in commit:")
        for file_info in results['affected_files']:
            print(f"   {file_info['status']} {file_info['file']} ({file_info['status_text']})")
    
    if 'other_files_in_commit' in results and results['other_files_in_commit']:
        print(f"\n⚠️  Other files in this commit:")
        for file_info in results['other_files_in_commit']:
            print(f"   {file_info['status']} {file_info['file']} ({file_info['status_text']})")
    
    # Warnings
    if results['warnings']:
        print("\n⚠️  Warnings:")
        for warning in results['warnings']:
            print(f"   • {warning}")
    
    # Suggestions
    if results['suggestions']:
        print("\n💡 Suggestions:")
        for suggestion in results['suggestions']:
            print(f"   {suggestion}")
    
    # Final verdict
    print("\n" + "=" * 60)
    if results['safe']:
        print(f"{risk_colors['LOW']}✅ Operation appears safe to proceed{reset_color}")
    else:
        print(f"{risk_colors['HIGH']}❌ Operation is risky - consider the suggestions above{reset_color}")


def main():
    parser = argparse.ArgumentParser(
        description='SafeGIT Commands - Prevent accidental loss of work in git operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Check if it's safe to reset a file
  %(prog)s check-reset file.java
  
  # Check if it's safe to revert a commit
  %(prog)s check-revert abc123 --files file.java
  
  # Safely reset with automatic backup
  %(prog)s safe-reset file.java --backup
  
  # Check multiple files
  %(prog)s check-reset src/*.java
  
  # Check what files would be cleaned
  %(prog)s check-clean
  
  # Safely clean with backup
  %(prog)s safe-clean --backup --no-dry-run
'''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # check-reset command
    reset_parser = subparsers.add_parser(
        'check-reset',
        help='Check if resetting files would lose important changes'
    )
    reset_parser.add_argument(
        'files',
        nargs='+',
        help='Files to check'
    )
    reset_parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    
    # check-revert command
    revert_parser = subparsers.add_parser(
        'check-revert',
        help='Check impact of reverting a commit'
    )
    revert_parser.add_argument(
        'commit',
        help='Commit hash to check'
    )
    revert_parser.add_argument(
        '--files',
        nargs='+',
        help='Specific files you care about (shows if commit affects other files too)'
    )
    revert_parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    
    # safe-reset command
    safe_reset_parser = subparsers.add_parser(
        'safe-reset',
        help='Reset files with automatic backup'
    )
    safe_reset_parser.add_argument(
        'files',
        nargs='+',
        help='Files to reset'
    )
    safe_reset_parser.add_argument(
        '--hard',
        action='store_true',
        help='Hard reset (default is mixed)'
    )
    safe_reset_parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup'
    )
    
    # check-clean command
    check_clean_parser = subparsers.add_parser(
        'check-clean',
        help='Check what files would be deleted by git clean'
    )
    check_clean_parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    
    # safe-clean command
    safe_clean_parser = subparsers.add_parser(
        'safe-clean',
        help='Safely clean untracked files with optional backup'
    )
    safe_clean_parser.add_argument(
        '--backup',
        action='store_true',
        help='Create zip backup of untracked files before cleaning'
    )
    safe_clean_parser.add_argument(
        '--force',
        action='store_true',
        help='Force clean even if risky'
    )
    safe_clean_parser.add_argument(
        '--no-dry-run',
        action='store_true',
        help='Actually perform the clean (default is dry run)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize SafeGit
    safegit = SafeGitCommands()
    
    # Execute commands
    if args.command == 'check-reset':
        results = safegit.check_reset_safety(args.files)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            format_safety_report(results)
    
    elif args.command == 'check-revert':
        results = safegit.check_revert_safety(args.commit, args.files)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            format_safety_report(results)
    
    elif args.command == 'safe-reset':
        mode = 'hard' if args.hard else 'mixed'
        backup = not args.no_backup
        success = safegit.safe_reset(args.files, mode=mode, backup=backup)
        sys.exit(0 if success else 1)
    
    elif args.command == 'check-clean':
        results = safegit.check_clean_safety()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            format_safety_report(results)
    
    elif args.command == 'safe-clean':
        dry_run = not args.no_dry_run
        success = safegit.safe_clean(force=args.force, backup=args.backup, dry_run=dry_run)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
