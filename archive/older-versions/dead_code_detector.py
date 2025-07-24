#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Dead Code Detector - Multi-language unused code finder.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import sys
import argparse
import re
import json
import ast
import os
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import AST context finder

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

try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

# Try to import javalang for better Java parsing
try:
    import javalang
    HAS_JAVALANG = True
except ImportError:
    HAS_JAVALANG = False

class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class DeadCodeItem:
    name: str
    type: str  # class, method, function, import, variable
    file: Path
    line: int
    confidence: Confidence
    reason: str
    code_snippet: str
    language: str

class DeadCodeDetector:
    def __init__(self, verbose: bool = False, timeout: int = 30, show_ast_context: bool = False):
        self.verbose = verbose
        self.timeout = timeout
        self.show_ast_context = show_ast_context
        self.logger = self._setup_logger()
        self.ripgrep_available = shutil.which('rg') is not None
        self.ast_context_finder = ASTContextFinder() if HAS_AST_CONTEXT and show_ast_context else None
        
        # Language configurations
        self.language_patterns = {
            'python': {
                'file_extensions': {'.py', '.pyw'},
                'declaration_patterns': [
                    (r'(?:^|\n)(?:async\s+)?def\s+(\w+)\s*\(', 'function'),
                    (r'(?:^|\n)class\s+(\w+)\s*(?:\(|:)', 'class'),
                    (r'(?:^|\n)(\w+)\s*=\s*(?:lambda|type\()', 'variable')
                ],
                'import_patterns': [
                    r'from\s+[\w.]+\s+import\s+(?:\w+\s+as\s+)?(\w+)',
                    r'import\s+[\w.]+\s+as\s+(\w+)',
                    r'import\s+([\w.]+)'
                ],
                'entry_points': {
                    '__init__', '__enter__', '__exit__', '__del__',
                    '__getattr__', '__setattr__', '__getitem__', '__setitem__',
                    '__call__', '__str__', '__repr__', '__hash__', '__eq__'
                },
                'dynamic_patterns': [
                    r'getattr\([^,]+,\s*["\']({name})["\']',
                    r'hasattr\([^,]+,\s*["\']({name})["\']',
                    r'__dict__\[["\']({name})["\']',
                    r'globals\(\)\[["\']({name})["\']',
                    r'locals\(\)\[["\']({name})["\']'
                ]
            },
            'java': {
                'file_extensions': {'.java'},
                'declaration_patterns': [
                    (r'(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?class\s+(\w+)', 'class'),
                    (r'(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?interface\s+(\w+)', 'interface'),
                    (r'(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?enum\s+(\w+)', 'enum'),
                    (r'(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:<[\w\s,?]+>\s+)?(\w+)\s+(\w+)\s*\(', 'method')
                ],
                'import_patterns': [
                    r'import\s+(?:static\s+)?[\w.]+\.(\w+);'
                ],
                'entry_points': {
                    'main', 'readObject', 'writeObject', 'readResolve', 'writeReplace',
                    'finalize', 'clone', 'equals', 'hashCode', 'toString'
                },
                'dynamic_patterns': [
                    r'Class\.forName\(["\'][\w.]+\.({name})["\']',
                    r'getMethod\(["\']({name})["\']',
                    r'getDeclaredMethod\(["\']({name})["\']'
                ]
            },
            'javascript': {
                'file_extensions': {'.js', '.jsx', '.ts', '.tsx', '.mjs'},
                'declaration_patterns': [
                    (r'(?:export\s+)?(?:default\s+)?class\s+(\w+)', 'class'),
                    (r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', 'function'),
                    (r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\()', 'function'),
                    (r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=', 'variable')
                ],
                'import_patterns': [
                    r'import\s+(\w+)\s+from',
                    r'import\s+\{\s*([^}]+)\s*\}\s+from',
                    r'const\s+(\w+)\s*=\s*require\(',
                    r'const\s+\{\s*([^}]+)\s*\}\s*=\s*require\('
                ],
                'entry_points': {
                    'constructor', 'render', 'componentDidMount', 'componentWillUnmount',
                    'ngOnInit', 'ngOnDestroy', 'mounted', 'destroyed', 'created'
                },
                'dynamic_patterns': [
                    r'\[["\'`]({name})["\'`]\]',
                    r'window\[["\'`]({name})["\'`]\]',
                    r'global\[["\'`]({name})["\'`]\]'
                ]
            }
        }
        
        # Framework-specific patterns
        self.framework_annotations = {
            # Java annotations
            '@Test', '@Before', '@After', '@BeforeClass', '@AfterClass',
            '@GetMapping', '@PostMapping', '@PutMapping', '@DeleteMapping',
            '@RequestMapping', '@Bean', '@Component', '@Service',
            '@Repository', '@Controller', '@RestController', '@Entity',
            '@Autowired', '@Value', '@Scheduled', '@EventListener',
            # Python decorators
            '@pytest.fixture', '@pytest.mark', '@unittest.skip',
            '@app.route', '@login_required', '@cache', '@property',
            '@staticmethod', '@classmethod', '@abstractmethod',
            # JavaScript/TypeScript decorators
            '@Injectable', '@Component', '@Directive', '@Pipe',
            '@Input', '@Output', '@ViewChild', '@HostListener'
        }
        
        # Cache for expensive operations
        self._file_cache = {}
        self._ast_cache = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for verbose output."""
        logger = logging.getLogger('DeadCodeDetector')
        if self.verbose:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.WARNING)
        return logger
    
    def _check_dependencies(self) -> None:
        """Check for required dependencies."""
        if not self.ripgrep_available:
            self.logger.warning("ripgrep not found – falling back to pure-Python scanning "
                                "(slower, but works).")
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect language from file extension."""
        suffix = file_path.suffix.lower()
        for lang, config in self.language_patterns.items():
            if suffix in config['file_extensions']:
                return lang
        return None
    
    def _read_file_cached(self, file_path: Path) -> Optional[str]:
        """Read file with caching."""
        if file_path in self._file_cache:
            return self._file_cache[file_path]
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                self._file_cache[file_path] = content
                return content
        except Exception as e:
            self.logger.debug(f"Error reading {file_path}: {e}")
            return None
    
    def _parse_python_ast(self, file_path: Path) -> Optional[ast.AST]:
        """Parse Python file to AST with caching."""
        if file_path in self._ast_cache:
            return self._ast_cache[file_path]
        
        content = self._read_file_cached(file_path)
        if not content:
            return None
        
        try:
            tree = ast.parse(content, filename=str(file_path))
            self._ast_cache[file_path] = tree
            return tree
        except Exception as e:
            self.logger.debug(f"AST parsing failed for {file_path}: {e}")
            return None
    
    def _find_declarations_ast_python(self, file_path: Path) -> List[Tuple[str, str, int, str]]:
        """Use AST parsing for Python declarations."""
        declarations = []
        tree = self._parse_python_ast(file_path)
        if not tree:
            return declarations
        
        content_lines = self._read_file_cached(file_path).splitlines()
        
        for node in ast.walk(tree):
            snippet = ""
            if hasattr(node, 'lineno') and node.lineno <= len(content_lines):
                snippet = content_lines[node.lineno - 1].strip()
            
            if isinstance(node, ast.ClassDef):
                declarations.append((node.name, 'class', node.lineno, snippet))
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                declarations.append((node.name, 'function', node.lineno, snippet))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[-1]
                    declarations.append((name, 'import', node.lineno, snippet))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != '*':  # Skip wildcard imports
                        name = alias.asname or alias.name
                        declarations.append((name, 'import', node.lineno, snippet))
        
        return declarations
    
    def _find_declarations_ripgrep(self, file_path: Path, language: str) -> List[Tuple[str, str, int, str]]:
        """Use ripgrep for declaration finding as fallback."""
        declarations = []
        config = self.language_patterns[language]
        
        for pattern, decl_type in config['declaration_patterns']:
            try:
                # Special handling for Java methods (capture second group)
                if language == 'java' and decl_type == 'method':
                    cmd = ['rg', '--multiline', '--no-heading', '--line-number', '-o', pattern, str(file_path)]
                else:
                    cmd = ['rg', '--multiline', '--no-heading', '--line-number', pattern, str(file_path)]
                
                self.logger.debug(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
                self.logger.debug(f"Result code: {result.returncode}, stdout: {result.stdout[:200]}")
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if not line:
                            continue
                        parts = line.split(':', 1)
                        if len(parts) >= 2:
                            line_num = int(parts[0])
                            match_text = parts[1]
                            
                            # Extract the actual name from the match
                            match = re.search(pattern, match_text)
                            if match:
                                # For Java methods, use the second capture group
                                if language == 'java' and decl_type == 'method' and len(match.groups()) > 1:
                                    name = match.group(2)
                                    self.logger.debug(f"Java method: {name} from {match_text}")
                                else:
                                    name = match.group(1)
                                    self.logger.debug(f"{decl_type}: {name} from {match_text}")
                                declarations.append((name, decl_type, line_num, match_text.strip()))
                                
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Timeout finding {decl_type} in {file_path}")
            except Exception as e:
                self.logger.debug(f"Error finding {decl_type} in {file_path}: {e}")
        
        return declarations
    
    def _find_declarations_regex(self, file_path: Path, language: str) -> List[Tuple[str, str, int, str]]:
        """Fallback declaration finder when ripgrep is unavailable."""
        declarations = []
        content = self._read_file_cached(file_path)
        if not content:
            return declarations

        config = self.language_patterns[language]
        for pattern, decl_type in config['declaration_patterns']:
            for m in re.finditer(pattern, content, flags=re.MULTILINE):
                if decl_type == 'method' and len(m.groups()) >= 2:
                    name = m.group(2)
                else:
                    name = m.group(1)
                line = content.count('\n', 0, m.start()) + 1
                snippet = m.group(0)[:120]
                declarations.append((name, decl_type, line, snippet))
        return declarations
    
    def _find_all_declarations(self, scope: Path, language: Optional[str] = None) -> Dict[str, List[DeadCodeItem]]:
        """Find all declarations in the given scope."""
        declarations_by_file = defaultdict(list)
        
        # Collect all files to analyze
        files_to_analyze = []
        if scope.is_file():
            files_to_analyze = [scope]
        else:
            for lang, config in self.language_patterns.items():
                if language and lang != language:
                    continue
                for ext in config['file_extensions']:
                    # Use glob pattern to find files
                    pattern = f'**/*{ext}'
                    files_to_analyze.extend(scope.glob(pattern))
        
        # Debug: log files found
        self.logger.debug(f"Files to analyze: {len(files_to_analyze)}")
        for f in files_to_analyze[:5]:  # Log first 5
            self.logger.debug(f"  - {f}")
        
        # Clear result tracking
        found_items = 0
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=min(8, len(files_to_analyze) or 1)) as executor:
            future_to_file = {}
            
            for file_path in files_to_analyze:
                if file_path.is_file():
                    lang = self._detect_language(file_path)
                    self.logger.debug(f"Processing {file_path} as {lang}")
                    if lang:
                        future = executor.submit(self._process_file_declarations, file_path, lang)
                        future_to_file[future] = file_path
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    items = future.result()
                    if items:
                        declarations_by_file[str(file_path)] = items
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
        
        return declarations_by_file
    
    def _process_file_declarations(self, file_path: Path, language: str) -> List[DeadCodeItem]:
        """Process a single file for declarations."""
        items = []
        
        # Try AST parsing for Python
        if language == 'python':
            declarations = self._find_declarations_ast_python(file_path)
        else:
            if self.ripgrep_available:
                declarations = self._find_declarations_ripgrep(file_path, language)
            else:
                declarations = self._find_declarations_regex(file_path, language)
        
        self.logger.debug(f"Found {len(declarations)} declarations in {file_path}")
        
        for name, decl_type, line, snippet in declarations:
            item = DeadCodeItem(
                name=name,
                type=decl_type,
                file=file_path,
                line=line,
                confidence=Confidence.LOW,  # Will be updated later
                reason="",  # Will be updated later
                code_snippet=snippet,
                language=language
            )
            items.append(item)
            self.logger.debug(f"Added item: {name} ({decl_type})")
        
        return items
    
    def _count_usages(self, name: str, scope: Path, language: str, exclude_file: Optional[Path] = None) -> int:
        """Count usages of a name in the codebase."""
        total_count = 0
        
        # Direct usage pattern
        direct_pattern = rf'\b{re.escape(name)}\b'
        
        if not self.ripgrep_available:
            # fallback – naive in-memory count
            # First populate cache if needed
            config = self.language_patterns[language]
            if scope.is_file():
                files_to_check = [scope]
            else:
                files_to_check = []
                for ext in config['file_extensions']:
                    pattern = f'**/*{ext}'
                    files_to_check.extend(scope.glob(pattern))
            
            # Read files into cache if not already there
            for file_path in files_to_check:
                if file_path not in self._file_cache:
                    self._read_file_cached(file_path)
            
            # Now count in cached files
            count = 0
            for file_path, content in self._file_cache.items():
                if exclude_file and str(file_path) == str(exclude_file):
                    continue
                if content:
                    count += len(re.findall(direct_pattern, content))
            return count

        # ripgrep fast-path
        cmd = ['rg', '-c', '--no-messages', f'--threads={getattr(self, "threads", 4)}', direct_pattern]
        
        # Add file type filters
        config = self.language_patterns[language]
        for ext in config['file_extensions']:
            cmd.extend(['-g', f'*{ext}'])
        
        # Exclude the declaration file to avoid self-references
        if exclude_file:
            cmd.extend(['--glob', f'!{exclude_file}'])
        
        cmd.append(str(scope))
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line and line.strip():
                        count = int(line.split(':')[-1])
                        total_count += count
        except Exception as e:
            self.logger.debug(f"Error counting usages of {name}: {e}")
        
        # Check dynamic patterns
        if total_count == 0:
            for pattern_template in config.get('dynamic_patterns', []):
                pattern = pattern_template.format(name=re.escape(name))
                try:
                    cmd = ['rg', '-c', '--no-messages', pattern]
                    for ext in config['file_extensions']:
                        cmd.extend(['-g', f'*{ext}'])
                    cmd.append(str(scope))
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
                    if result.returncode == 0:
                        for line in result.stdout.strip().split('\n'):
                            if ':' in line and line.strip():
                                total_count += int(line.split(':')[-1])
                                if total_count > 0:
                                    break
                except Exception:
                    pass
        
        return total_count
    
    def _is_entry_point(self, item: DeadCodeItem) -> bool:
        """Check if an item is a known entry point."""
        # Check language-specific entry points
        config = self.language_patterns[item.language]
        if item.name in config['entry_points']:
            return True
        
        # Check if it's a test function (pytest/unittest pattern)
        if item.language == 'python' and item.name.startswith('test_'):
            return True
        
        # Check for framework annotations/decorators
        content = self._read_file_cached(item.file)
        if not content:
            return False
        
        # Look for annotations/decorators before the declaration
        lines = content.splitlines()
        if item.line > 1 and item.line <= len(lines):
            # Check previous lines for annotations
            for i in range(max(0, item.line - 6), item.line):
                line = lines[i].strip()
                for annotation in self.framework_annotations:
                    if annotation in line:
                        return True
        
        # Special checks for main methods
        if item.name == 'main':
            if item.language == 'java' and 'public static void main' in item.code_snippet:
                return True
            elif item.language == 'python' and '__name__' in content and '__main__' in content:
                return True
        
        return False
    
    def _calculate_confidence(self, item: DeadCodeItem, usage_count: int) -> Tuple[Confidence, str]:
        """Calculate confidence level and reason for dead code detection."""
        # Entry points are not dead code
        if self._is_entry_point(item):
            return Confidence.LOW, "Entry point or framework method"
        
        # No usage at all
        if usage_count == 0:
            # Imports are definitely dead if unused
            if item.type == 'import':
                return Confidence.HIGH, "Unused import"
            
            # Private methods/variables might be used dynamically
            if item.name.startswith('_') and not item.name.startswith('__'):
                return Confidence.MEDIUM, "Private member with no usage found"
            
            # Constants might be imported elsewhere
            if item.name.isupper():
                return Confidence.MEDIUM, "Constant with no usage found"
            
            # Test files have different rules
            if 'test' in str(item.file).lower():
                return Confidence.MEDIUM, "Test code with no usage found"
            
            return Confidence.HIGH, "No usage found in codebase"
        
        # Low usage might be self-reference
        elif usage_count <= 1:
            return Confidence.LOW, f"Very low usage ({usage_count} reference)"
        
        # Multiple usages means it's likely not dead
        return Confidence.LOW, f"Multiple usages found ({usage_count} references)"
    
    def _filter_by_gitignore(self, files: List[Path], scope: Path) -> List[Path]:
        """Filter files respecting .gitignore if in a git repository."""
        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ['git', '-C', str(scope), 'rev-parse', '--is-inside-work-tree'],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                return files
            
            # Use git ls-files to get tracked files
            result = subprocess.run(
                ['git', '-C', str(scope), 'ls-files'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                tracked_files = set(Path(scope) / f for f in result.stdout.strip().split('\n') if f)
                return [f for f in files if f in tracked_files]
                
        except Exception:
            pass
        
        return files
    
    def analyze(
        self,
        scope: Path,
        language: Optional[str] = None,
        min_confidence: Confidence = Confidence.LOW,
        ignore_patterns: List[str] = None,
        use_git: bool = True
    ) -> List[DeadCodeItem]:
        """Analyze codebase for dead code."""
        self._check_dependencies()
        
        print(f"🔍 Analyzing {scope} for dead code...")
        start_time = time.time()
        
        # Find all declarations
        print("  📋 Finding all declarations...")
        declarations_by_file = self._find_all_declarations(scope, language)
        
        total_declarations = sum(len(items) for items in declarations_by_file.values())
        print(f"  ✓ Found {total_declarations} declarations in {len(declarations_by_file)} files")
        
        # Analyze each declaration for usage
        print("  🔎 Analyzing usage patterns...")
        dead_items = []
        
        # Flatten declarations for processing
        all_items = []
        for file_items in declarations_by_file.values():
            all_items.extend(file_items)
        
        # Process items with progress indication
        for i, item in enumerate(all_items):
            if i % 10 == 0:
                progress = (i / len(all_items)) * 100
                print(f"\r  🔎 Analyzing usage patterns... {progress:.1f}%", end='', flush=True)
            
            # Skip ignored patterns
            if ignore_patterns:
                skip = False
                for pattern in ignore_patterns:
                    if re.search(pattern, item.name) or re.search(pattern, str(item.file)):
                        skip = True
                        break
                if skip:
                    continue
            
            # Count usages - when analyzing single file, search in parent directory
            search_scope = scope.parent if scope.is_file() else scope
            usage_count = self._count_usages(item.name, search_scope, item.language, exclude_file=item.file)
            
            # Calculate confidence
            confidence, reason = self._calculate_confidence(item, usage_count)
            item.confidence = confidence
            item.reason = reason
            
            # Filter by minimum confidence
            if confidence.value >= min_confidence.value:
                dead_items.append(item)
        
        print(f"\n  ✓ Analysis complete in {time.time() - start_time:.1f}s")
        
        # Sort by confidence and type
        dead_items.sort(key=lambda x: (x.confidence.value, x.type, x.name))
        
        return dead_items
    
    def generate_report(self, items: List[DeadCodeItem], format: str = 'text') -> str:
        """Generate report in specified format."""
        if format == 'json':
            return json.dumps([asdict(item) for item in items], indent=2, default=str)
        
        elif format == 'markdown':
            report = ["# Dead Code Analysis Report\n"]
            report.append(f"**Total items found:** {len(items)}\n")
            
            # Summary by confidence
            confidence_counts = defaultdict(int)
            for item in items:
                confidence_counts[item.confidence.value] += 1
            
            report.append("## Summary by Confidence Level\n")
            for level in ['high', 'medium', 'low']:
                count = confidence_counts.get(level, 0)
                report.append(f"- **{level.title()}**: {count} items")
            report.append("")
            
            # Group by type
            by_type = defaultdict(list)
            for item in items:
                by_type[item.type].append(item)
            
            for type_name, type_items in sorted(by_type.items()):
                report.append(f"## {type_name.title()}s ({len(type_items)} items)\n")
                
                # Further group by confidence
                by_conf = defaultdict(list)
                for item in type_items:
                    by_conf[item.confidence].append(item)
                
                for conf in [Confidence.HIGH, Confidence.MEDIUM, Confidence.LOW]:
                    conf_items = by_conf.get(conf, [])
                    if conf_items:
                        report.append(f"### {conf.value.title()} Confidence\n")
                        for item in sorted(conf_items, key=lambda x: x.name):
                            # Get AST context if available
                            context_str = ""
                            if self.ast_context_finder:
                                context = self.ast_context_finder._format_context_parts(
                                    self.ast_context_finder.get_context_for_line(item.file, item.line)
                                )
                                if context:
                                    context_str = f" [{context}]"
                            
                            report.append(f"- **{item.name}** (`{item.file}:{item.line}{context_str}`)")
                            report.append(f"  - Language: {item.language}")
                            report.append(f"  - Reason: {item.reason}")
                            report.append(f"  - Code: `{item.code_snippet}`")
                            report.append("")
            
            return '\n'.join(report)
        
        else:  # text format
            report = ["=" * 80]
            report.append("DEAD CODE ANALYSIS REPORT")
            report.append("=" * 80)
            report.append("")
            
            # Summary
            report.append(f"Total items found: {len(items)}")
            
            # By confidence
            confidence_counts = defaultdict(int)
            for item in items:
                confidence_counts[item.confidence.value] += 1
            
            report.append("\nConfidence levels:")
            for level in ['high', 'medium', 'low']:
                count = confidence_counts.get(level, 0)
                emoji = "🔴" if level == 'high' else "🟡" if level == 'medium' else "🟢"
                report.append(f"  {emoji} {level.upper()}: {count}")
            
            # By type
            type_counts = defaultdict(int)
            for item in items:
                type_counts[item.type] += 1
            
            report.append("\nBy type:")
            for type_name, count in sorted(type_counts.items()):
                report.append(f"  - {type_name}: {count}")
            
            # Detailed list
            report.append("\n" + "-" * 80)
            report.append("DETAILED FINDINGS")
            report.append("-" * 80)
            
            current_confidence = None
            for item in items:
                if item.confidence != current_confidence:
                    current_confidence = item.confidence
                    emoji = "🔴" if item.confidence == Confidence.HIGH else "🟡" if item.confidence == Confidence.MEDIUM else "🟢"
                    report.append(f"\n{emoji} {item.confidence.value.upper()} CONFIDENCE:")
                
                # Get AST context if available
                context_str = ""
                if self.ast_context_finder:
                    context = self.ast_context_finder._format_context_parts(
                        self.ast_context_finder.get_context_for_line(item.file, item.line)
                    )
                    if context:
                        context_str = f" [{context}]"
                
                report.append(f"\n  {item.type}: {item.name}")
                report.append(f"    File: {item.file}:{item.line}{context_str}")
                report.append(f"    Language: {item.language}")
                report.append(f"    Reason: {item.reason}")
                report.append(f"    Code: {item.code_snippet}")
            
            report.append("\n" + "=" * 80)
            
            return '\n'.join(report)
    
    def generate_ignore_file(self, items: List[DeadCodeItem], output_path: Path) -> None:
        """Generate a .deadcodeignore file from current findings."""
        ignore_patterns = set()
        
        # Group by file for file-specific patterns
        by_file = defaultdict(list)
        for item in items:
            by_file[item.file].append(item)
        
        # Generate patterns
        for file_path, file_items in by_file.items():
            # If many items in a file, consider ignoring the whole file
            if len(file_items) > 10:
                ignore_patterns.add(f"# Many items in {file_path}")
                ignore_patterns.add(str(file_path))
            else:
                for item in file_items:
                    if item.confidence == Confidence.LOW:
                        ignore_patterns.add(f"# {item.reason}")
                        ignore_patterns.add(f"{item.name}")
        
        # Write ignore file
        with open(output_path, 'w') as f:
            f.write("# Dead Code Ignore File\n")
            f.write("# Generated by dead_code_detector.py\n")
            f.write("# Add patterns to ignore (one per line)\n")
            f.write("# Supports regex patterns\n\n")
            
            for pattern in sorted(ignore_patterns):
                f.write(f"{pattern}\n")

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Find dead code across multiple programming languages.')
    else:
        parser = argparse.ArgumentParser(description='Find dead code across multiple programming languages.')
    
    parser.add_argument('path', nargs='?', default='.',
                        help='Path to analyze (default: current directory)')
    parser.add_argument('--language',                        choices=['auto', 'python', 'java', 'javascript'],
                        default='auto',
                        help='Language to analyze (default: auto-detect)')
    parser.add_argument('--format', '-f',
                        choices=['text', 'json', 'markdown'],
                        default='text',
                        help='Output format (default: text)')
    parser.add_argument('--confidence', '-c',
                        choices=['all', 'high', 'medium', 'low'],
                        default='all',
                        help='Minimum confidence level to report (default: all)')
    parser.add_argument('--threads', type=int, default=4, help='rg worker threads')
    parser.add_argument('--ignore-pattern',                        action='append',
                        default=[],
                        help='Regex patterns to ignore (can be used multiple times)')
    parser.add_argument('--no-git', action='store_true',
                        help='Don\'t use git to filter files')
    parser.add_argument('--timeout', type=int, default=30,
                        help='Timeout for subprocess commands in seconds (default: 30)')
    parser.add_argument('--generate-ignore', action='store_true',
                        help='Generate .deadcodeignore file from findings')
    parser.add_argument('--ast-context', action='store_true', default=True,
                        help='Show AST context (class/method) for each finding (default: enabled)')
    parser.add_argument('--no-ast-context', action='store_true',
                        help='Disable AST context display')
    
    args = parser.parse_args()
    
    # Handle AST context flag logic
    if args.no_ast_context:
        args.ast_context = False
    
    # Map confidence argument to enum
    confidence_map = {
        'all': Confidence.LOW,
        'low': Confidence.LOW,
        'medium': Confidence.MEDIUM,
        'high': Confidence.HIGH
    }
    min_confidence = confidence_map[args.confidence]
    
    # Create detector
    detector = DeadCodeDetector(verbose=args.verbose, timeout=args.timeout, show_ast_context=args.ast_context)
    detector.threads = args.threads
    
    # Convert path to Path object
    scope = Path(args.path).resolve()
    if not scope.exists():
        print(f"Error: Path '{scope}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Determine language if auto
    language = None if args.language == 'auto' else args.language
    
    try:
        # Run analysis
        dead_items = detector.analyze(
            scope=scope,
            language=language,
            min_confidence=min_confidence,
            ignore_patterns=args.ignore_pattern,
            use_git=not args.no_git
        )
        
        # Generate report
        report = detector.generate_report(dead_items, format=args.format)
        print(report)
        
        # Generate ignore file if requested
        if args.generate_ignore and dead_items:
            ignore_path = scope / '.deadcodeignore'
            detector.generate_ignore_file(dead_items, ignore_path)
            print(f"\n✓ Generated {ignore_path}", file=sys.stderr)
        
        # Exit with appropriate code
        if dead_items and any(item.confidence == Confidence.HIGH for item in dead_items):
            sys.exit(1)  # Found high-confidence dead code
        else:
            sys.exit(0)  # No significant dead code found
            
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nError during analysis: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()