#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
show_structure_ast_v4_package.py - Production version using proper package structure

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import argparse
from pathlib import Path

# Proper package import - no sys.path manipulation needed
from show_structure_ast import StructureAnalyzer, safe_analyzer_context


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced hierarchical code structure viewer (v4 - package version)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
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
        analyzer = StructureAnalyzer()
        elements = analyzer.analyze_file(filepath, args)
        
        if not elements:
            if not args.json:
                print("No code elements found or unable to parse file", file=sys.stderr)
            else:
                print("[]")
            sys.exit(1)
        
        # Format and display
        output = analyzer.format_output(elements, args)
        print(output)


if __name__ == '__main__':
    main()