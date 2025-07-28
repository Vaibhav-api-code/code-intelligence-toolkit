#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Unified refactoring tool that works with both Java and Python codebases.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import re

# Try to import rope for Python refactoring
try:
    from rope.base.project import Project
    from rope.refactor.rename import Rename
    from rope.base import libutils
    from rope.base.exceptions import RopeError
    ROPE_AVAILABLE = True
except ImportError:
    ROPE_AVAILABLE = False

# Import our existing Python AST refactoring
try:
    from ast_refactor import ASTRefactoring
    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False


class LanguageDetector:
    """Detect programming language from file extension."""
    
    LANGUAGE_MAP = {
        '.py': 'python',
        '.pyw': 'python',
        '.pyi': 'python',
        '.java': 'java',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.groovy': 'groovy',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.swift': 'swift',
        '.m': 'objective-c',
        '.mm': 'objective-c++',
    }
    
    @classmethod
    def detect(cls, file_path: Path) -> str:
        """Detect language from file extension."""
        suffix = file_path.suffix.lower()
        return cls.LANGUAGE_MAP.get(suffix, 'unknown')
    
    @classmethod
    def get_files_by_language(cls, files: List[Path]) -> Dict[str, List[Path]]:
        """Group files by detected language."""
        grouped = {}
        for file in files:
            lang = cls.detect(file)
            if lang not in grouped:
                grouped[lang] = []
            grouped[lang].append(file)
        return grouped


class JavaRefactorer:
    """Handle Java refactoring using JavaRefactorCLI."""
    
    def __init__(self):
        self.java_cli_path = self._find_java_cli()
    
    def _find_java_cli(self) -> Optional[str]:
        """Find the JavaRefactorCLI in the classpath."""
        # Try gradle first
        gradle_wrapper = Path('./gradlew')
        if gradle_wrapper.exists():
            return str(gradle_wrapper)
        
        # Try regular gradle
        result = subprocess.run(['which', 'gradle'], capture_output=True, text=True)
        if result.returncode == 0:
            return 'gradle'
        
        return None
    
    def _run_java_cli(self, args: List[str]) -> Tuple[int, str, str]:
        """Run JavaRefactorCLI with given arguments."""
        if not self.java_cli_path:
            return 1, "", "JavaRefactorCLI not found. Please ensure gradle is available."
        
        # Build the command
        cmd = [
            self.java_cli_path, '-q', 'runMain',
            '-PmainClass=com.example.tools.JavaRefactorCLI',
            '--args=' + ' '.join(f'"{arg}"' for arg in args)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    
    def rename_symbol(self, file_path: Path, old_name: str, new_name: str, 
                     symbol_type: str = 'all') -> Dict:
        """Rename a symbol in Java code."""
        results = {
            'file': str(file_path),
            'language': 'java',
            'backend': 'JavaRefactorCLI',
            'changes': 0,
            'success': False,
            'error': None,
            'preview': []
        }
        
        # Map our symbol types to JavaRefactorCLI commands
        type_mapping = {
            'method': 'rename-method',
            'class': 'rename-class',
            'function': 'rename-method',  # Java methods
            'variable': None,  # JavaRefactorCLI doesn't support variable renaming yet
        }
        
        command = type_mapping.get(symbol_type)
        if not command:
            if symbol_type == 'variable':
                results['error'] = "Variable renaming not yet supported for Java. Consider using IntelliJ IDEA or Eclipse."
            else:
                results['error'] = f"Unsupported symbol type for Java: {symbol_type}"
            return results
        
        # Store original content for comparison
        original_content = file_path.read_text()
        
        # Run the refactoring
        returncode, stdout, stderr = self._run_java_cli([
            command, str(file_path), old_name, new_name
        ])
        
        if returncode == 0:
            # Read new content
            new_content = file_path.read_text()
            
            # Count changes
            if new_content != original_content:
                results['success'] = True
                results['changes'] = new_content.count(new_name) - original_content.count(new_name)
                
                # Generate preview
                import difflib
                diff = list(difflib.unified_diff(
                    original_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    n=1
                ))
                results['preview'] = [line.rstrip() for line in diff[3:10]]  # Skip header
        else:
            results['error'] = stderr or "Refactoring failed"
        
        return results
    
    def list_symbols(self, file_path: Path, symbol_type: str = 'all') -> List[str]:
        """List symbols of given type in Java file."""
        type_mapping = {
            'method': 'list-methods',
            'class': 'list-classes',
            'field': 'list-fields',
            'all': None  # Would need multiple calls
        }
        
        command = type_mapping.get(symbol_type)
        if not command:
            return []
        
        returncode, stdout, stderr = self._run_java_cli([command, str(file_path)])
        
        if returncode == 0:
            return [line.strip() for line in stdout.splitlines() if line.strip()]
        return []


class PythonRefactorer:
    """Handle Python refactoring using rope or AST."""
    
    def __init__(self):
        self.rope_available = ROPE_AVAILABLE
        self.ast_available = AST_AVAILABLE
        self.project = None
    
    def _init_rope_project(self, file_path: Path) -> Optional[Project]:
        """Initialize rope project for the file."""
        if not self.rope_available:
            return None
        
        # Find project root
        project_root = file_path.parent
        for parent in file_path.parents:
            if (parent / '.git').exists() or (parent / 'setup.py').exists():
                project_root = parent
                break
        
        try:
            return Project(str(project_root))
        except Exception:
            return None
    
    def rename_symbol(self, file_path: Path, old_name: str, new_name: str, 
                     symbol_type: str = 'all') -> Dict:
        """Rename a symbol in Python code."""
        results = {
            'file': str(file_path),
            'language': 'python',
            'backend': 'none',
            'changes': 0,
            'success': False,
            'error': None,
            'preview': []
        }
        
        original_content = file_path.read_text()
        
        # Try rope first
        if self.rope_available:
            project = self._init_rope_project(file_path)
            if project:
                try:
                    resource = libutils.path_to_resource(project, str(file_path))
                    
                    # Find offset based on symbol type
                    offset = self._find_symbol_offset(original_content, old_name, symbol_type)
                    
                    if offset >= 0:
                        rename = Rename(project, resource, offset)
                        changes = rename.get_changes(new_name)
                        
                        # Get new content without applying
                        new_content = changes.changes[0].get_new_contents()
                        
                        results['backend'] = 'rope (scope-aware)'
                        results['success'] = True
                        results['changes'] = new_content.count(new_name) - original_content.count(new_name)
                        
                        # Generate preview
                        import difflib
                        diff = list(difflib.unified_diff(
                            original_content.splitlines(keepends=True),
                            new_content.splitlines(keepends=True),
                            n=1
                        ))
                        results['preview'] = [line.rstrip() for line in diff[3:10]]
                        
                        # Actually apply the changes
                        project.do(changes)
                        
                    project.close()
                    return results
                    
                except Exception as e:
                    if project:
                        project.close()
                    results['error'] = f"Rope error: {str(e)}"
        
        # Fall back to AST refactoring
        if self.ast_available and not results['success']:
            try:
                refactorer = ASTRefactoring()
                new_content, changes = refactorer.refactor_python_file(
                    file_path, old_name, new_name, symbol_type, dry_run=False
                )
                
                results['backend'] = 'ast (type-aware)'
                results['success'] = True
                results['changes'] = changes
                
                # Generate preview
                import difflib
                diff = list(difflib.unified_diff(
                    original_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    n=1
                ))
                results['preview'] = [line.rstrip() for line in diff[3:10]]
                
            except Exception as e:
                results['error'] = f"AST error: {str(e)}"
        
        if not results['success'] and not results['error']:
            results['error'] = "No refactoring backend available for Python"
        
        return results
    
    def _find_symbol_offset(self, content: str, name: str, symbol_type: str) -> int:
        """Find offset of symbol definition based on type."""
        if symbol_type == 'function':
            pattern = rf'^def\s+{re.escape(name)}\s*\('
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.start() + 4  # After 'def '
        
        elif symbol_type == 'class':
            pattern = rf'^class\s+{re.escape(name)}[\s\(:]'
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.start() + 6  # After 'class '
        
        elif symbol_type == 'variable':
            # Look for module-level assignment
            pattern = rf'^{re.escape(name)}\s*='
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.start()
        
        # Default: find first occurrence
        return content.find(name)


class UnifiedRefactorer:
    """Main refactoring interface that handles multiple languages."""
    
    def __init__(self):
        self.java_refactorer = JavaRefactorer()
        self.python_refactorer = PythonRefactorer()
        self.refactorers = {
            'java': self.java_refactorer,
            'python': self.python_refactorer,
        }
    
    def refactor_files(self, files: List[Path], old_name: str, new_name: str,
                      symbol_type: str = 'all', dry_run: bool = False) -> Dict:
        """Refactor symbols across multiple files of different languages."""
        
        # Group files by language
        files_by_language = LanguageDetector.get_files_by_language(files)
        
        results = {
            'total_files': len(files),
            'total_changes': 0,
            'languages_processed': list(files_by_language.keys()),
            'results_by_language': {},
            'errors': []
        }
        
        for language, lang_files in files_by_language.items():
            if language == 'unknown':
                results['errors'].append(f"Unknown language for files: {[str(f) for f in lang_files]}")
                continue
            
            refactorer = self.refactorers.get(language)
            if not refactorer:
                results['errors'].append(f"No refactorer available for {language}")
                continue
            
            lang_results = {
                'files_processed': 0,
                'files_changed': 0,
                'total_changes': 0,
                'file_results': []
            }
            
            for file in lang_files:
                if dry_run:
                    # For dry run, create a copy
                    import tempfile
                    import shutil
                    with tempfile.NamedTemporaryFile(mode='w', suffix=file.suffix, delete=False) as tmp:
                        tmp.write(file.read_text())
                        tmp_path = Path(tmp.name)
                    
                    file_result = refactorer.rename_symbol(tmp_path, old_name, new_name, symbol_type)
                    file_result['file'] = str(file)  # Show original file name
                    tmp_path.unlink()
                else:
                    file_result = refactorer.rename_symbol(file, old_name, new_name, symbol_type)
                
                lang_results['files_processed'] += 1
                if file_result.get('success') and file_result.get('changes', 0) > 0:
                    lang_results['files_changed'] += 1
                    lang_results['total_changes'] += file_result['changes']
                    results['total_changes'] += file_result['changes']
                
                lang_results['file_results'].append(file_result)
            
            results['results_by_language'][language] = lang_results
        
        return results
    
    def print_results(self, results: Dict):
        """Pretty print refactoring results."""
        print("\nREFACTORING RESULTS")
        print("=" * 80)
        print(f"Total files processed: {results['total_files']}")
        print(f"Total changes made: {results['total_changes']}")
        print(f"Languages: {', '.join(results['languages_processed'])}")
        
        if results['errors']:
            print("\nERRORS:")
            for error in results['errors']:
                print(f"  ❌ {error}")
        
        for language, lang_results in results['results_by_language'].items():
            print(f"\n{language.upper()} FILES:")
            print(f"  Files processed: {lang_results['files_processed']}")
            print(f"  Files changed: {lang_results['files_changed']}")
            print(f"  Total changes: {lang_results['total_changes']}")
            
            for file_result in lang_results['file_results']:
                if file_result['success']:
                    print(f"\n  ✅ {file_result['file']}")
                    print(f"     Backend: {file_result['backend']}")
                    print(f"     Changes: {file_result['changes']}")
                    if file_result.get('preview'):
                        print("     Preview:")
                        for line in file_result['preview'][:3]:
                            print(f"       {line}")
                else:
                    print(f"\n  ❌ {file_result['file']}")
                    print(f"     Error: {file_result.get('error', 'Unknown error')}")


def main():
    parser = argparse.ArgumentParser(
        description='Unified refactoring tool for multiple programming languages',
        epilog='''
EXAMPLES:
  # Rename across mixed Java/Python codebase
  %(prog)s rename --old calculatePrice --new computePrice src/

  # Rename only methods/functions
  %(prog)s rename --old processData --new handleData --type method *.java *.py

  # Dry run to preview changes
  %(prog)s rename --old Config --new Settings --dry-run **/*.java

  # Language-specific refactoring
  %(prog)s rename --old userName --new username --lang java src/main/

SUPPORTED LANGUAGES:
  • Python: Full scope-aware refactoring with rope
  • Java: Method and class renaming with JavaRefactorCLI
  • More languages coming soon!

SYMBOL TYPES:
  • all: Rename all occurrences (default)
  • function/method: Rename functions/methods only
  • class: Rename classes only
  • variable: Rename variables (Python only)
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Rename command
    rename_parser = subparsers.add_parser('rename', help='Rename symbols')
    rename_parser.add_argument('files', nargs='+', help='Files or patterns to process')
    rename_parser.add_argument('--old', '--old-name', required=True, help='Current name')
    rename_parser.add_argument('--new', '--new-name', required=True, help='New name')
    rename_parser.add_argument('--type', choices=['all', 'function', 'method', 'class', 'variable'],
                              default='all', help='Type of symbol to rename')
    rename_parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    rename_parser.add_argument('--lang', '--language', help='Process only files of this language')
    
    # Check command
    parser.add_argument('--check', action='store_true', help='Check available refactoring backends')
    
    args = parser.parse_args()
    
    if args.check:
        print("REFACTORING BACKENDS STATUS")
        print("=" * 50)
        print("\nPython:")
        print(f"  Rope (scope-aware): {'✅ Available' if ROPE_AVAILABLE else '❌ Not installed'}")
        print(f"  AST (type-aware): {'✅ Available' if AST_AVAILABLE else '❌ Not found'}")
        print("\nJava:")
        java_ref = JavaRefactorer()
        print(f"  JavaRefactorCLI: {'✅ Available' if java_ref.java_cli_path else '❌ Not found'}")
        print("\nTo install missing backends:")
        if not ROPE_AVAILABLE:
            print("  Python rope: pip install rope")
        if not java_ref.java_cli_path:
            print("  Java: Ensure gradle is in PATH")
        return
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'rename':
        # Collect files
        from glob import glob
        all_files = []
        for pattern in args.files:
            path = Path(pattern)
            if path.is_file():
                all_files.append(path)
            elif path.is_dir():
                # Recursively find all source files
                for ext in ['.java', '.py']:
                    all_files.extend(path.rglob(f'*{ext}'))
            else:
                # Treat as glob pattern
                matches = glob(pattern, recursive=True)
                all_files.extend(Path(m) for m in matches if Path(m).is_file())
        
        if not all_files:
            print("No files found to process")
            return
        
        # Filter by language if specified
        if args.lang:
            lang_lower = args.lang.lower()
            all_files = [f for f in all_files if LanguageDetector.detect(f) == lang_lower]
        
        # Remove duplicates
        all_files = list(set(all_files))
        
        print(f"Processing {len(all_files)} files...")
        
        # Perform refactoring
        refactorer = UnifiedRefactorer()
        results = refactorer.refactor_files(
            all_files, args.old, args.new, args.type, args.dry_run
        )
        
        refactorer.print_results(results)
        
        if args.dry_run and results['total_changes'] > 0:
            print("\nDry run complete. Use without --dry-run to apply changes.")


if __name__ == '__main__':
    main()