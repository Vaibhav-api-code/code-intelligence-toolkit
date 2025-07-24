#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Git Commit Analyzer - Analyzes staged changes and generates commit messages.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import sys
import re
import json
import shutil
import logging
import os
import shlex
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import argparse

# Optional imports for enhanced functionality
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

class GitCommitAnalyzer:
    DEFAULT_TIMEOUT = int(os.environ.get("GCA_GIT_TIMEOUT", "15"))
    
    def __init__(self, verbose: bool = False, detailed: bool = False,
                 timeout: int = None):
        self.verbose = verbose
        self.detailed = detailed
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Minimal logger—helpful during `--verbose`
        self.logger = logging.getLogger(self.__class__.__name__)
        if self.verbose and not self.logger.handlers:
            _h = logging.StreamHandler()
            _h.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
            self.logger.addHandler(_h)
            self.logger.setLevel(logging.DEBUG)
        self.commit_types = {
            'feat': 'New feature or capability',
            'fix': 'Bug fix',
            'refactor': 'Code restructuring without changing behavior',
            'docs': 'Documentation only changes',
            'test': 'Adding or modifying tests',
            'perf': 'Performance improvements',
            'style': 'Code style changes (formatting, naming)',
            'chore': 'Maintenance tasks, dependencies',
            'build': 'Build system or configuration changes'
        }
        
    def run_git_command(self, cmd: List[str], timeout: int = None) -> Tuple[bool, str]:
        """Run a git command and return success status and output."""
        try:
            if self.verbose:
                self.logger.debug(f"Running git command: git {' '.join(cmd)}")
            
            result = subprocess.run(
                ['git'] + cmd,
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8',
                timeout=timeout or self.timeout
            )
            
            if result.returncode == 0:
                return True, result.stdout
            return False, (result.stderr or result.stdout)
        except FileNotFoundError:
            return False, "Error: 'git' command not found. Is Git installed and in your PATH?"
        except subprocess.TimeoutExpired:
            return False, f"Error: git command {' '.join(cmd)} timed out after {timeout or self.timeout}s"
    
    def verify_git_environment(self) -> bool:
        """Verify that Git is installed and we are in a Git repository."""
        if not shutil.which('git'):
            print("Error: 'git' command not found. Is Git installed and in your PATH?", file=sys.stderr)
            return False
        
        success, output = self.run_git_command(['rev-parse', '--is-inside-work-tree'])
        if not success or 'true' not in output.strip().lower():
            print("Error: Not a git repository. Please run this script from within a git project.", file=sys.stderr)
            return False
            
        return True
    
    def get_staged_files(self) -> List[Dict[str, str]]:
        """Get list of staged files with their status."""
        success, output = self.run_git_command(['diff', '--cached', '--name-status'])
        if not success:
            print(f"Error getting staged files: {output}")
            return []
        
        files = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                status, filepath = parts[0], parts[1]
                files.append({
                    'status': status,
                    'path': filepath,
                    'type': self._get_file_type(filepath)
                })
        return files
    
    def _get_file_type(self, filepath: str) -> str:
        """Determine file type from path."""
        path = Path(filepath)
        ext = path.suffix.lower()
        
        # Test files
        if 'test' in filepath.lower() or filepath.endswith('Test.java'):
            return 'test'
        
        # Documentation
        if ext in ['.md', '.txt', '.rst', '.adoc']:
            return 'docs'
        
        # Build/config files
        if path.name in ['build.gradle', 'pom.xml', 'package.json', 'Makefile'] or \
           ext in ['.gradle', '.yml', '.yaml', '.json', '.xml', '.properties']:
            return 'build'
        
        # Code files
        if ext in ['.java', '.py', '.js', '.ts', '.cpp', '.c', '.go', '.rs']:
            return 'code'
        
        return 'other'
    
    def get_diff_stats(self) -> Dict[str, any]:
        """Get statistics about the staged changes."""
        success, output = self.run_git_command(['diff', '--cached', '--stat'])
        if not success:
            return {}
        
        stats = {
            'files_changed': 0,
            'insertions': 0,
            'deletions': 0,
            'files_by_type': defaultdict(int)
        }
        
        # Parse the stat line
        if 'changed' in output:
            match = re.search(r'(\d+) files? changed', output)
            if match:
                stats['files_changed'] = int(match.group(1))
            
            match = re.search(r'(\d+) insertions?\(\+\)', output)
            if match:
                stats['insertions'] = int(match.group(1))
            
            match = re.search(r'(\d+) deletions?\(-\)', output)
            if match:
                stats['deletions'] = int(match.group(1))
        
        return stats
    
    def analyze_changes(self) -> Dict[str, any]:
        """Analyze staged changes and categorize them."""
        files = self.get_staged_files()
        if not files:
            return {'error': 'No staged changes found'}
        
        analysis = {
            'total_files': len(files),
            'added': [],
            'modified': [],
            'deleted': [],
            'renamed': [],
            'file_types': defaultdict(list),
            'suggested_type': None,
            'main_changes': []
        }
        
        # Categorize files
        for file in files:
            if file['status'] == 'A':
                analysis['added'].append(file['path'])
            elif file['status'] == 'M':
                analysis['modified'].append(file['path'])
            elif file['status'] == 'D':
                analysis['deleted'].append(file['path'])
            elif file['status'].startswith('R'):
                analysis['renamed'].append(file['path'])
            
            analysis['file_types'][file['type']].append(file['path'])
        
        # Determine commit type
        analysis['suggested_type'] = self._suggest_commit_type(analysis)
        
        # Get main changes
        analysis['main_changes'] = self._get_main_changes(files)
        
        return analysis
    
    def _suggest_commit_type(self, analysis: Dict) -> str:
        """Suggest a commit type based on the changes."""
        # Priority order for determining commit type
        if analysis['file_types']['test']:
            # If only test files, it's a test commit
            if len(analysis['file_types']['test']) == analysis['total_files']:
                return 'test'
        
        if analysis['file_types']['docs']:
            # If only docs files, it's a docs commit
            if len(analysis['file_types']['docs']) == analysis['total_files']:
                return 'docs'
        
        if analysis['file_types']['build']:
            # If mainly build files
            if len(analysis['file_types']['build']) > analysis['total_files'] / 2:
                return 'build'
        
        # Check for new features vs fixes
        if analysis['added'] and len(analysis['added']) > len(analysis['modified']):
            return 'feat'
        
        # If modifying existing code without adding much
        if analysis['modified'] and not analysis['added']:
            # Try to detect if it's a fix or refactor
            # This is a heuristic - could be improved with diff content analysis
            return 'refactor'
        
        # Default to feat for mixed changes
        return 'feat'
    
    def _get_main_changes(self, files: List[Dict]) -> List[str]:
        """Extract main changes from file list."""
        changes = []
        
        # Group by directory
        by_dir = defaultdict(list)
        for file in files:
            dir_path = Path(file['path']).parent
            by_dir[str(dir_path)].append(file['path'])
        
        # Summarize by directory
        for dir_path, file_list in by_dir.items():
            if len(file_list) > 3:
                changes.append(f"Multiple changes in {dir_path}/ ({len(file_list)} files)")
            else:
                for filepath in file_list[:3]:  # Limit to 3 files per dir
                    changes.append(Path(filepath).name)
        
        return changes[:5]  # Limit total to 5 main changes
    
    def generate_commit_message(self, analysis: Dict) -> str:
        """Generate a commit message based on the analysis."""
        commit_type = analysis.get('suggested_type', 'feat')
        
        # Generate summary based on changes
        if analysis.get('error'):
            return f"{commit_type}: <add summary of changes>"
        
        # Build the summary
        parts = []
        
        if analysis['added']:
            if len(analysis['added']) == 1:
                parts.append(f"add {Path(analysis['added'][0]).stem}")
            else:
                parts.append(f"add {len(analysis['added'])} new files")
        
        if analysis['modified']:
            if len(analysis['modified']) == 1:
                parts.append(f"update {Path(analysis['modified'][0]).stem}")
            else:
                parts.append(f"update {len(analysis['modified'])} files")
        
        if analysis['deleted']:
            parts.append(f"remove {len(analysis['deleted'])} files")
        
        if analysis['renamed']:
            parts.append(f"rename {len(analysis['renamed'])} files")
        
        # Create the message
        if parts:
            summary = " and ".join(parts[:2])  # Use first two actions
        else:
            summary = "update project files"
        
        return f"{commit_type}: {summary}"
    
    def generate_detailed_commit_message(self, analysis: Dict, diff_analysis: Dict) -> str:
        """Generate a detailed commit message with body."""
        # Generate the subject line
        subject = self.generate_commit_message(analysis)
        
        # Build the body
        body_parts = []
        
        # List files by change type
        if analysis.get('added'):
            body_parts.append(f"Added files ({len(analysis['added'])}):")
            for f in analysis['added'][:3]:
                body_parts.append(f"  - {f}")
            if len(analysis['added']) > 3:
                body_parts.append(f"  ... and {len(analysis['added']) - 3} more")
        
        if analysis.get('modified'):
            body_parts.append(f"\nModified files ({len(analysis['modified'])}):")
            for f in analysis['modified'][:3]:
                body_parts.append(f"  - {f}")
            if len(analysis['modified']) > 3:
                body_parts.append(f"  ... and {len(analysis['modified']) - 3} more")
        
        # Add insights from diff analysis
        if diff_analysis:
            insights = []
            if diff_analysis.get('features_added'):
                insights.append(f"• Added {len(diff_analysis['features_added'])} new methods/functions")
            if diff_analysis.get('error_handling'):
                insights.append(f"• Enhanced error handling in {len(diff_analysis['error_handling'])} places")
            if diff_analysis.get('security_changes'):
                insights.append(f"• Security-related changes in {len(diff_analysis['security_changes'])} files")
            if diff_analysis.get('todos_added'):
                insights.append(f"• Added {len(diff_analysis['todos_added'])} TODOs")
            
            if insights:
                body_parts.append("\nKey changes:")
                body_parts.extend(insights)
        
        # Try to detect ticket number from branch
        success, branch_output = self.run_git_command(['branch', '--show-current'])
        if success and branch_output:
            branch = branch_output.strip()
            # Look for common ticket patterns
            ticket_match = re.search(r'([A-Z]+-\d+)', branch)
            if ticket_match:
                body_parts.append(f"\nTicket: {ticket_match.group(1)}")
        
        # Combine subject and body
        if body_parts:
            return f"{subject}\n\n" + "\n".join(body_parts)
        return subject
    
    def show_detailed_diff(self):
        """Show detailed diff for review."""
        print("\n=== DETAILED CHANGES ===")
        success, output = self.run_git_command(['diff', '--cached', '--stat'])
        if success:
            print(output)
        
        if self.verbose:
            print("\n=== FILE CONTENTS PREVIEW ===")
            success, output = self.run_git_command(['diff', '--cached', '--unified=3'])
            if success:
                # Limit output for readability
                lines = output.split('\n')[:100]
                print('\n'.join(lines))
                if len(output.split('\n')) > 100:
                    print("\n... (truncated, use git diff --cached for full diff)")
    
    def get_full_diff(self, context_lines: int = 3) -> str:
        """Get the full diff of all staged changes."""
        success, output = self.run_git_command(['diff', '--cached', f'--unified={context_lines}'])
        if success:
            return output
        return ""
    
    def analyze_diff_content(self, diff_content: str) -> Dict[str, any]:
        """Analyze the actual diff content to understand changes better."""
        analysis = {
            'features_added': [],
            'bugs_fixed': [],
            'refactorings': [],
            'test_changes': [],
            'doc_changes': [],
            'todos_added': [],
            'todos_removed': [],
            'error_handling': [],
            'security_changes': []
        }
        
        lines = diff_content.split('\n')
        current_file = None
        
        for line in lines:
            # Track current file
            if line.startswith('diff --git'):
                match = re.search(r'b/(.+)$', line)
                if match:
                    current_file = match.group(1)
            
            # Skip non-content lines
            if not line.startswith('+') or line.startswith('+++'):
                continue
            
            # Remove the + prefix
            content = line[1:]
            
            # Analyze the content
            if current_file:
                # New features/methods
                if re.match(r'\s*(def|function|public|private|protected)\s+\w+', content):
                    analysis['features_added'].append(f"New method in {current_file}")
                
                # Error handling
                if re.search(r'(try|catch|except|finally|raise|throw)', content):
                    analysis['error_handling'].append(f"Error handling in {current_file}")
                
                # TODOs
                if re.search(r'TODO|FIXME|XXX|HACK', content):
                    analysis['todos_added'].append(content.strip())
                
                # Security patterns
                if re.search(r'(password|token|secret|key|auth|security)', content, re.I):
                    analysis['security_changes'].append(f"Security-related change in {current_file}")
                
                # Test patterns
                if current_file.endswith(('test.py', 'Test.java', '_test.go')) or 'test' in current_file:
                    analysis['test_changes'].append(f"Test change in {current_file}")
        
        return analysis
    
    def get_unstaged_files(self) -> List[Dict[str, str]]:
        """Get list of modified but unstaged files."""
        success, output = self.run_git_command(['status', '--porcelain'])
        if not success:
            return []
        
        unstaged = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            # Look for modified but not staged files
            if line.startswith(' M') or line.startswith('??'):
                status = line[:2]
                filepath = line[3:]
                unstaged.append({
                    'status': status.strip(),
                    'path': filepath,
                    'type': self._get_file_type(filepath)
                })
        return unstaged
    
    def smart_stage_suggestions(self) -> Dict[str, List[str]]:
        """Suggest files to stage based on patterns (GIT SEQ STAGE)."""
        unstaged = self.get_unstaged_files()
        staged = self.get_staged_files()
        
        suggestions = {
            'related_to_staged': [],
            'same_directory': [],
            'same_type': [],
            'test_files': [],
            'doc_files': []
        }
        
        if not staged or not unstaged:
            return suggestions
        
        # Get directories and types of staged files
        staged_dirs = set(Path(f['path']).parent for f in staged)
        staged_types = set(f['type'] for f in staged)
        staged_names = set(Path(f['path']).stem for f in staged)
        
        for file in unstaged:
            file_path = Path(file['path'])
            file_dir = file_path.parent
            file_stem = file_path.stem
            
            # Related by directory
            if file_dir in staged_dirs:
                suggestions['same_directory'].append(file['path'])
            
            # Related by type
            if file['type'] in staged_types:
                suggestions['same_type'].append(file['path'])
            
            # Related by name (e.g., MyClass.java and MyClassTest.java)
            for staged_name in staged_names:
                if staged_name in file_stem or file_stem in staged_name:
                    suggestions['related_to_staged'].append(file['path'])
                    break
            
            # Separate test and doc files
            if file['type'] == 'test':
                suggestions['test_files'].append(file['path'])
            elif file['type'] == 'docs':
                suggestions['doc_files'].append(file['path'])
        
        # Remove duplicates
        for key in suggestions:
            suggestions[key] = list(set(suggestions[key]))
        
        return suggestions
    
    def check_claude_md_status(self) -> Dict[str, any]:
        """Check if CLAUDE.md has been modified (SYNC CHECK)."""
        # Check if CLAUDE.md exists
        claude_path = Path('CLAUDE.md')
        if not claude_path.exists():
            return {'exists': False}
        
        result = {'exists': True, 'modified': False, 'staged': False}
        
        # Check git status for CLAUDE.md
        success, output = self.run_git_command(['status', '--porcelain', 'CLAUDE.md'])
        if success and output:
            status = output[:2]
            if 'M' in status:
                result['modified'] = True
            if status[0] != ' ':
                result['staged'] = True
        
        # Get diff if modified
        if result['modified'] and not result['staged']:
            success, diff = self.run_git_command(['diff', 'CLAUDE.md'])
            if success:
                result['diff_preview'] = diff[:1000]  # First 1000 chars
                result['diff_lines'] = len(diff.split('\n'))
        
        return result
    
    def run(self):
        """Main entry point for the analyzer."""
        # Perform environment sanity checks first
        if not self.verify_git_environment():
            return 1

        print("🔍 Git Commit Analyzer")
        print("=" * 50)
        
        # Check if there are staged changes
        success, output = self.run_git_command(['diff', '--cached', '--name-only'])
        if not success or not output.strip():
            print("❌ No staged changes found!")
            print("\nTo stage changes (using SafeGIT):")
            print("  safegit add <files>      # Stage specific files")
            print("  safegit add -u          # Stage all modified files")
            print("  safegit add .           # Stage all changes")
            return 1
        
        # Analyze changes
        analysis = self.analyze_changes()
        stats = self.get_diff_stats()
        
        # Get diff content analysis for better insights
        diff_content = self.get_full_diff()
        diff_analysis = self.analyze_diff_content(diff_content) if diff_content else {}
        
        # Display analysis
        print(f"\n📊 CHANGE SUMMARY")
        print(f"Files changed: {analysis['total_files']}")
        if stats:
            print(f"Insertions: +{stats['insertions']}")
            print(f"Deletions: -{stats['deletions']}")
        
        print(f"\n📁 FILES BY STATUS")
        if analysis['added']:
            print(f"Added ({len(analysis['added'])}):")
            for f in analysis['added'][:5]:
                print(f"  + {f}")
            if len(analysis['added']) > 5:
                print(f"  ... and {len(analysis['added']) - 5} more")
        
        if analysis['modified']:
            print(f"Modified ({len(analysis['modified'])}):")
            for f in analysis['modified'][:5]:
                print(f"  ~ {f}")
            if len(analysis['modified']) > 5:
                print(f"  ... and {len(analysis['modified']) - 5} more")
        
        if analysis['deleted']:
            print(f"Deleted ({len(analysis['deleted'])}):")
            for f in analysis['deleted'][:5]:
                print(f"  - {f}")
        
        # Show insights from diff analysis
        if diff_analysis:
            print(f"\n🔎 CHANGE INSIGHTS")
            if diff_analysis.get('features_added'):
                print(f"  • New features: {len(diff_analysis['features_added'])} methods/functions")
            if diff_analysis.get('error_handling'):
                print(f"  • Error handling: {len(diff_analysis['error_handling'])} changes")
            if diff_analysis.get('security_changes'):
                print(f"  • Security-related: {len(diff_analysis['security_changes'])} changes")
            if diff_analysis.get('todos_added'):
                print(f"  • TODOs added: {len(diff_analysis['todos_added'])}")
        
        print(f"\n🏷️  SUGGESTED COMMIT TYPE: {analysis['suggested_type']}")
        print(f"   ({self.commit_types[analysis['suggested_type']]})")
        
        # Generate commit message
        if self.detailed:
            commit_msg = self.generate_detailed_commit_message(analysis, diff_analysis)
        else:
            commit_msg = self.generate_commit_message(analysis)
        
        # Escape for safe shell execution using shlex
        safe_commit_msg = shlex.quote(commit_msg)
        
        print(f"\n💬 SUGGESTED COMMIT MESSAGE:")
        if self.detailed and '\n\n' in commit_msg:
            # For detailed messages, show formatted output
            parts = commit_msg.split('\n\n', 1)
            print(f"   {parts[0]}")
            print("\n   " + "\n   ".join(parts[1].split('\n')))
        else:
            print(f"   {commit_msg}")
        
        # Show alternative types
        print(f"\n📝 ALTERNATIVE COMMIT TYPES:")
        for ctype, desc in self.commit_types.items():
            if ctype != analysis['suggested_type']:
                print(f"   {ctype}: {desc}")
        
        # Show detailed diff if requested
        if self.verbose:
            self.show_detailed_diff()
        
        print(f"\n✅ TO COMMIT WITH SUGGESTED MESSAGE (using SafeGIT):")
        print(f'   safegit commit -m "{safe_commit_msg}"')
        
        print(f"\n📋 TO COMMIT WITH CUSTOM MESSAGE (using SafeGIT):")
        print(f'   safegit commit -m "<type>: <your description>"')
        
        print(f"\n🔍 FOR FULL DIFF ANALYSIS:")
        print(f'   ./run_any_python_tool.sh git_commit_analyzer.py --full-diff')
        
        # Check for unstaged files and suggest staging
        unstaged = self.get_unstaged_files()
        if unstaged:
            print(f"\n⚠️  UNSTAGED FILES ({len(unstaged)})")
            suggestions = self.smart_stage_suggestions()
            
            if suggestions['related_to_staged']:
                print(f"\n📎 RELATED TO STAGED FILES:")
                for f in suggestions['related_to_staged'][:5]:
                    print(f"   safegit add {f}")
            
            if suggestions['same_directory'] and not suggestions['related_to_staged']:
                print(f"\n📁 SAME DIRECTORY AS STAGED FILES:")
                for f in suggestions['same_directory'][:3]:
                    print(f"   safegit add {f}")
        
        # Check CLAUDE.md status
        claude_status = self.check_claude_md_status()
        if claude_status.get('exists') and claude_status.get('modified'):
            print(f"\n⚡ SYNC CHECK: CLAUDE.md has been modified!")
            if not claude_status.get('staged'):
                print(f"   Review changes: git diff CLAUDE.md")
                print(f"   Stage if needed: safegit add CLAUDE.md")
            else:
                print(f"   ✓ Already staged for commit")
        
        return 0

def main():
    parser = argparse.ArgumentParser(description='Analyze staged git changes and suggest commit messages')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--json', action='store_true',
                        help='Output in JSON format')
    parser.add_argument('--full-diff', action='store_true',
                        help='Output full diff content for external analysis')
    parser.add_argument('--stage-suggestions', action='store_true',
                        help='Show smart staging suggestions (GIT SEQ STAGE)')
    parser.add_argument('--sync-check', action='store_true',
                        help='Check CLAUDE.md status (SYNC CHECK)')
    parser.add_argument('--seq1', action='store_true',
                        help='Execute GIT SEQ 1 workflow (stage + analyze + message)')
    parser.add_argument('--detailed', action='store_true',
                        help='Generate detailed commit message with body')
    parser.add_argument('--timeout', type=int, default=None,
                        help=f'Git command timeout in seconds (default: {GitCommitAnalyzer.DEFAULT_TIMEOUT})')
    
    args = parser.parse_args()
    
    # Set verbose based on whether --verbose is provided
    verbose = getattr(args, 'verbose', False)
    detailed = getattr(args, 'detailed', False) 
    timeout = getattr(args, 'timeout', None)
    
    analyzer = GitCommitAnalyzer(verbose=verbose, detailed=detailed, timeout=timeout)
    
    # Set json mode
    json_mode = getattr(args, 'json', False)
    
    # Run environment check for most commands (skip for json/full-diff as they might be piped)
    if not (json_mode or args.full_diff):
        if not analyzer.verify_git_environment():
            return 1
    
    # Handle special commands
    if args.sync_check:
        # Just do SYNC CHECK
        claude_status = analyzer.check_claude_md_status()
        if not claude_status.get('exists'):
            print("❌ CLAUDE.md not found in this repository")
            return 1
        
        print("🔍 SYNC CHECK - CLAUDE.md Status")
        print("=" * 50)
        
        if claude_status.get('modified'):
            print("⚡ CLAUDE.md has been MODIFIED!")
            print(f"   Lines changed: ~{claude_status.get('diff_lines', 'unknown')}")
            if claude_status.get('staged'):
                print("   ✓ Already staged for commit")
            else:
                print("\n📋 To review changes:")
                print("   git diff CLAUDE.md | head -200")
                print("\n📝 To stage:")
                print("   safegit add CLAUDE.md")
        else:
            print("✅ CLAUDE.md is up to date")
        return 0
    
    if args.stage_suggestions:
        # Show staging suggestions
        print("🔍 GIT SEQ STAGE - Smart Staging Suggestions")
        print("=" * 50)
        
        unstaged = analyzer.get_unstaged_files()
        if not unstaged:
            print("✅ No unstaged files found!")
            return 0
        
        staged = analyzer.get_staged_files()
        if not staged:
            print("ℹ️  No files currently staged. Showing all unstaged files:")
            for file in unstaged[:10]:
                print(f"   safegit add {file['path']}")
            return 0
        
        suggestions = analyzer.smart_stage_suggestions()
        
        print(f"\n📊 CURRENT STATUS")
        print(f"Staged files: {len(staged)}")
        print(f"Unstaged files: {len(unstaged)}")
        
        if suggestions['related_to_staged']:
            print(f"\n📎 RELATED TO STAGED FILES (likely should be staged):")
            for f in suggestions['related_to_staged']:
                print(f"   git add {f}")
        
        if suggestions['same_directory']:
            print(f"\n📁 SAME DIRECTORY AS STAGED FILES:")
            for f in suggestions['same_directory'][:5]:
                print(f"   git add {f}")
        
        if suggestions['test_files']:
            print(f"\n🧪 TEST FILES:")
            for f in suggestions['test_files'][:5]:
                print(f"   git add {f}")
        
        print(f"\n💡 TO STAGE ALL MODIFIED FILES:")
        print(f"   safegit add -u")
        
        return 0
    
    if args.seq1:
        # Execute GIT SEQ 1 workflow
        print("🔍 GIT SEQ 1 - Auto-commit Workflow")
        print("=" * 50)
        
        # Analyze current state
        analysis = analyzer.analyze_changes()
        if analysis.get('error'):
            print("❌ No staged changes found!")
            print("\n📝 Suggested workflow:")
            print("1. Stage your changes: safegit add <files>")
            print("2. Run again: ./run_any_python_tool.sh git_commit_analyzer.py --seq1")
            return 1
        
        # Generate commit message
        commit_msg = analyzer.generate_commit_message(analysis)
        
        print(f"\n📊 CHANGES TO COMMIT")
        print(f"Files: {analysis['total_files']}")
        print(f"Type: {analysis['suggested_type']}")
        
        print(f"\n💬 GENERATED COMMIT MESSAGE:")
        print(f"   {commit_msg}")
        
        print(f"\n⚡ READY FOR GIT SEQ 1")
        print(f"This will commit with the message above.")
        print(f"\n📋 TO PROCEED:")
        print(f'   safegit commit -m "{commit_msg}"')
        
        return 0
    
    if args.full_diff:
        # Just output the full diff for external analysis
        diff_content = analyzer.get_full_diff(3)  # Default 3 lines of context
        if diff_content:
            print(diff_content)
            return 0
        else:
            print("No staged changes found", file=sys.stderr)
            return 1
    
    if json_mode:
        analysis = analyzer.analyze_changes()
        stats = analyzer.get_diff_stats()
        commit_msg = analyzer.generate_commit_message(analysis)
        
        # Add diff content analysis if requested
        diff_content = analyzer.get_full_diff()
        diff_analysis = analyzer.analyze_diff_content(diff_content) if diff_content else {}
        
        output = {
            'analysis': analysis,
            'stats': stats,
            'suggested_message': commit_msg,
            'commit_types': analyzer.commit_types,
            'diff_analysis': diff_analysis
        }
        
        print(json.dumps(output, indent=2, default=str))
        return 0
    
    return analyzer.run()

if __name__ == '__main__':
    sys.exit(main())