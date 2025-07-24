#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
show_structure_ast_v4_enhanced.py - Enhanced version with better error reporting and fallback options

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List

# Use proper package imports - no sys.path manipulation needed
from show_structure_ast import (
    StructureAnalyzer, FilterContext, CodeElement, 
    PythonParser, JavaParser, JavaScriptParser,
    ContentPreprocessor, safe_analyzer_context
)

class EnhancedStructureAnalyzer(StructureAnalyzer):
    """Enhanced analyzer with better error reporting and fallback options"""
    
    def analyze_file(self, filepath: Path, options: argparse.Namespace) -> List[CodeElement]:
        """Analyze a file with enhanced error reporting"""
        
        # Basic file validation
        if not filepath.exists():
            print(f"❌ File not found: {filepath}", file=sys.stderr)
            return []
        
        suffix = filepath.suffix.lower()
        if suffix not in self.parsers:
            print(f"❌ Unsupported file type: {suffix}", file=sys.stderr)
            print(f"   Supported types: {', '.join(self.parsers.keys())}", file=sys.stderr)
            return []
        
        # File size check
        size = filepath.stat().st_size
        if size > 10 * 1024 * 1024:  # 10MB
            print(f"⚠️  Large file detected: {size:,} bytes ({size/1024/1024:.1f} MB)", file=sys.stderr)
            print(f"   Consider using --no-preprocess flag for faster parsing", file=sys.stderr)
        
        try:
            content = filepath.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            print(f"❌ Unicode decode error: {e}", file=sys.stderr)
            print(f"   File may have encoding issues", file=sys.stderr)
            return []
        except Exception as e:
            print(f"❌ Error reading file: {e}", file=sys.stderr)
            return []
        
        # Content validation
        if not content.strip():
            print(f"❌ File is empty or contains only whitespace", file=sys.stderr)
            return []
        
        # Basic syntax check for Java files
        if suffix == '.java':
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                print(f"⚠️  Brace mismatch detected: {open_braces} open, {close_braces} close", file=sys.stderr)
                print(f"   This may cause parsing issues", file=sys.stderr)
        
        # Parsing with detailed error reporting
        parser = self.parsers[suffix]
        filter_context = FilterContext(options)
        
        try:
            if hasattr(parser, 'parse'):
                if 'filter_context' in parser.parse.__code__.co_varnames:
                    # Enhanced Java parser with fallback
                    if suffix == '.java':
                        return self._parse_java_with_fallback(
                            parser, content, str(filepath), filter_context, options
                        )
                    else:
                        # Other parsers
                        if 'skip_preprocessing' in parser.parse.__code__.co_varnames:
                            elements = parser.parse(content, str(filepath), filter_context,
                                                  options.include_variables, 
                                                  skip_preprocessing=options.no_preprocess)
                        else:
                            elements = parser.parse(content, str(filepath), filter_context,
                                                  options.include_variables)
                else:
                    # Legacy parser interface
                    elements = parser.parse(content, str(filepath), options.include_variables)
                    elements = self._apply_filters_smart(elements, options)
            else:
                elements = []
            
            # Post-processing
            if (options.filter_decorator or 
                (hasattr(options, 'filter_annotation') and options.filter_annotation)):
                elements = self._apply_filters_smart(elements, options)
            
            # Sort elements
            if options.sort_by == 'name':
                elements.sort(key=lambda e: e.name.lower())
            elif options.sort_by == 'size':
                elements.sort(key=lambda e: e.size, reverse=True)
            else:  # default: line
                elements.sort(key=lambda e: e.line_start)
            
            return elements
            
        except Exception as e:
            print(f"❌ Parsing error: {e}", file=sys.stderr)
            if options.verbose:
                import traceback
                print(f"   Full traceback:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
            return []
    
    def _parse_java_with_fallback(self, parser, content, filepath, filter_context, options):
        """Parse Java with multiple fallback strategies"""
        
        # Strategy 1: Try javalang parser
        if hasattr(parser, '_parse_with_javalang'):
            try:
                print(f"🔍 Trying javalang parser...", file=sys.stderr)
                elements = parser._parse_with_javalang(content, filepath, filter_context, options.include_variables)
                if elements:
                    print(f"✅ javalang parser succeeded: {len(elements)} elements", file=sys.stderr)
                    return elements
                else:
                    print(f"⚠️  javalang parser returned no elements", file=sys.stderr)
            except Exception as e:
                print(f"❌ javalang parser failed: {e}", file=sys.stderr)
                if options.verbose:
                    import traceback
                    traceback.print_exc(file=sys.stderr)
        
        # Strategy 2: Try regex parser with preprocessing
        try:
            print(f"🔍 Trying regex parser with preprocessing...", file=sys.stderr)
            elements = parser._parse_with_regex(content, filepath, filter_context, 
                                               options.include_variables, skip_preprocessing=False)
            if elements:
                print(f"✅ Regex parser with preprocessing succeeded: {len(elements)} elements", file=sys.stderr)
                return elements
            else:
                print(f"⚠️  Regex parser with preprocessing returned no elements", file=sys.stderr)
        except Exception as e:
            print(f"❌ Regex parser with preprocessing failed: {e}", file=sys.stderr)
            if options.verbose:
                import traceback
                traceback.print_exc(file=sys.stderr)
        
        # Strategy 3: Try regex parser without preprocessing
        try:
            print(f"🔍 Trying regex parser without preprocessing...", file=sys.stderr)
            elements = parser._parse_with_regex(content, filepath, filter_context, 
                                               options.include_variables, skip_preprocessing=True)
            if elements:
                print(f"✅ Regex parser without preprocessing succeeded: {len(elements)} elements", file=sys.stderr)
                return elements
            else:
                print(f"⚠️  Regex parser without preprocessing returned no elements", file=sys.stderr)
        except Exception as e:
            print(f"❌ Regex parser without preprocessing failed: {e}", file=sys.stderr)
            if options.verbose:
                import traceback
                traceback.print_exc(file=sys.stderr)
        
        # Strategy 4: Minimal regex parser (last resort)
        try:
            print(f"🔍 Trying minimal regex parser (last resort)...", file=sys.stderr)
            elements = self._minimal_java_parser(content, filepath)
            if elements:
                print(f"✅ Minimal parser succeeded: {len(elements)} elements", file=sys.stderr)
                return elements
            else:
                print(f"⚠️  Minimal parser returned no elements", file=sys.stderr)
        except Exception as e:
            print(f"❌ Minimal parser failed: {e}", file=sys.stderr)
            if options.verbose:
                import traceback
                traceback.print_exc(file=sys.stderr)
        
        print(f"❌ All parsing strategies failed", file=sys.stderr)
        return []
    
    def _minimal_java_parser(self, content, filepath):
        """Minimal Java parser as last resort"""
        import re
        
        elements = []
        lines = content.split('\n')
        
        # Very basic patterns
        package_pattern = re.compile(r'^\s*package\s+([\w.]+)\s*;')
        class_pattern = re.compile(r'^\s*(?:public\s+)?(?:abstract\s+)?class\s+(\w+)')
        method_pattern = re.compile(r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:synchronized\s+)?(?:[a-zA-Z_][a-zA-Z0-9_<>\[\]]*\s+)?(\w+)\s*\(')
        
        for i, line in enumerate(lines, 1):
            try:
                # Package
                package_match = package_pattern.match(line)
                if package_match:
                    elements.append(CodeElement(
                        type='package',
                        name=f"package {package_match.group(1)}",
                        line_start=i,
                        line_end=i
                    ))
                    continue
                
                # Class
                class_match = class_pattern.match(line)
                if class_match:
                    elements.append(CodeElement(
                        type='class',
                        name=class_match.group(1),
                        line_start=i,
                        line_end=i + 50,  # Rough estimate
                        visibility='public'
                    ))
                    continue
                
                # Method (very basic)
                method_match = method_pattern.match(line)
                if method_match and '=' not in line:
                    method_name = method_match.group(1)
                    if method_name not in ['if', 'while', 'for', 'switch', 'catch']:
                        elements.append(CodeElement(
                            type='method',
                            name=method_name,
                            line_start=i,
                            line_end=i + 10,  # Rough estimate
                            visibility='public'
                        ))
                
            except Exception:
                continue
        
        return elements


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced hierarchical code structure viewer with better error reporting',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('file', help='File to analyze')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--include-fields', action='store_true', help='Include field/attribute definitions')
    parser.add_argument('--include-imports', action='store_true', help='Include import statements')
    parser.add_argument('--include-variables', action='store_true', help='Include variable declarations')
    parser.add_argument('--max-depth', type=int, help='Maximum nesting depth to display')
    parser.add_argument('--filter-visibility', nargs='+', 
                        choices=['public', 'private', 'protected', 'package-private'],
                        help='Filter by visibility')
    parser.add_argument('--filter-name', help='Filter elements by name using regex')
    parser.add_argument('--filter-decorator', help='Filter Python elements by decorator')
    parser.add_argument('--filter-annotation', help='Filter Java elements by annotation (e.g., @Override, @Test)')
    parser.add_argument('--sort-by', choices=['line', 'name', 'size'], default='line',
                        help='Sort elements by criteria')
    parser.add_argument('--no-preprocess', action='store_true', 
                        help='Skip preprocessing (faster but less accurate)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.INFO)
    
    with safe_analyzer_context():
        # Analyze file
        filepath = Path(args.file)
        analyzer = EnhancedStructureAnalyzer()
        elements = analyzer.analyze_file(filepath, args)
        
        if not elements:
            if not args.json:
                print("No code elements found or unable to parse file", file=sys.stderr)
                print("\n💡 Troubleshooting suggestions:", file=sys.stderr)
                print("   1. Check file syntax and encoding", file=sys.stderr)
                print("   2. Try with --no-preprocess flag", file=sys.stderr)
                print("   3. Use --verbose for detailed error information", file=sys.stderr)
                print("   4. For large files, consider using --max-depth to limit output", file=sys.stderr)
            else:
                print("[]")
            sys.exit(1)
        
        # Format and display
        output = analyzer.format_output(elements, args)
        print(output)


if __name__ == '__main__':
    main()