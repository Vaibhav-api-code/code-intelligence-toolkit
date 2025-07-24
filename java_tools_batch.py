#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Java Tools Batch Processor - Run tools on multiple files with structure validation.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import os
import glob
import json
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from safe_java_tools import SafeJavaTools

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

class BatchProcessor:
    def __init__(self, max_workers=4):
        self.safe_tools = SafeJavaTools()
        self.max_workers = max_workers
    
    def find_java_files(self, patterns):
        """Find all Java files matching the patterns."""
        files = set()
        
        for pattern in patterns:
            if os.path.isfile(pattern) and pattern.endswith('.java'):
                files.add(pattern)
            elif os.path.isdir(pattern):
                # Recursively find Java files
                for java_file in Path(pattern).rglob('*.java'):
                    files.add(str(java_file))
            else:
                # Treat as glob pattern
                for match in glob.glob(pattern, recursive=True):
                    if match.endswith('.java'):
                        files.add(match)
        
        return sorted(files)
    
    def validate_files(self, files):
        """Validate structure of multiple files."""
        results = {}
        valid_files = []
        invalid_files = []
        
        print(f"Validating {len(files)} Java files...")
        print("=" * 80)
        
        for file_path in files:
            result = self.safe_tools.check_structure(file_path)
            results[file_path] = result
            
            if result['valid']:
                valid_files.append(file_path)
                if result['warning_count'] > 0:
                    print(f"✓ {file_path} - OK ({result['warning_count']} warnings)")
                else:
                    print(f"✓ {file_path} - OK")
            else:
                invalid_files.append(file_path)
                print(f"✗ {file_path} - {result['error_count']} errors")
        
        print("\n" + "=" * 80)
        print(f"VALIDATION SUMMARY:")
        print(f"  Total files: {len(files)}")
        print(f"  Valid: {len(valid_files)}")
        print(f"  Invalid: {len(invalid_files)}")
        
        return results, valid_files, invalid_files
    
    def process_file(self, file_path, tool_name, tool_args):
        """Process a single file with a tool."""
        try:
            # Run the tool
            full_args = [file_path] + tool_args
            ret = self.safe_tools.run_tool(tool_name, full_args, force=True)
            
            return {
                'file': file_path,
                'tool': tool_name,
                'success': ret == 0,
                'return_code': ret
            }
        except Exception as e:
            return {
                'file': file_path,
                'tool': tool_name,
                'success': False,
                'error': str(e)
            }
    
    def run_batch(self, files, tool_name, tool_args, validate_first=True, 
                  skip_invalid=True, parallel=True):
        """Run a tool on multiple files."""
        # Validate files first if requested
        valid_files = files
        if validate_first:
            _, valid_files, invalid_files = self.validate_files(files)
            
            if invalid_files and skip_invalid:
                print(f"\nSkipping {len(invalid_files)} files with structural issues")
                print("-" * 60)
        
        if not valid_files:
            print("No valid files to process")
            return []
        
        print(f"\nProcessing {len(valid_files)} files with '{tool_name}'...")
        print("=" * 80)
        
        results = []
        
        if parallel and len(valid_files) > 1:
            # Process files in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.process_file, file_path, tool_name, tool_args): file_path
                    for file_path in valid_files
                }
                
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        print(f"✓ {result['file']}")
                    else:
                        print(f"✗ {result['file']} - error")
        else:
            # Process files sequentially
            for file_path in valid_files:
                result = self.process_file(file_path, tool_name, tool_args)
                results.append(result)
                
                if result['success']:
                    print(f"✓ {result['file']}")
                else:
                    print(f"✗ {result['file']} - error")
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        print("\n" + "=" * 80)
        print(f"BATCH PROCESSING SUMMARY:")
        print(f"  Processed: {len(results)} files")
        print(f"  Successful: {successful}")
        print(f"  Failed: {len(results) - successful}")
        
        return results
    
    def generate_report(self, results, output_file=None):
        """Generate a detailed report of batch processing."""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_files': len(results),
                'successful': sum(1 for r in results if r.get('success', False)),
                'failed': sum(1 for r in results if not r.get('success', False))
            },
            'results': results
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to: {output_file}")
        
        return report

def main():
    # Don't use standard parser - this tool has custom argument structure
    parser = argparse.ArgumentParser(description='Java Tools Batch Processor - Run tools on multiple files')
    
    parser.add_argument('tool', help='Tool to run')
    parser.add_argument('patterns', nargs='+', 
                       help='File patterns, directories, or glob expressions')
    parser.add_argument('--args', nargs='*', default=[],
                       help='Arguments to pass to the tool')
    parser.add_argument('--no-validate', action='store_true',
                       help='Skip structure validation')
    parser.add_argument('--include-invalid', action='store_true',
                       help='Process files even with structure errors')
    parser.add_argument('--sequential', action='store_true',
                       help='Process files sequentially instead of parallel')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--report', help='Save report to JSON file')
    
    args = parser.parse_args()
    
    # Find all matching files
    processor = BatchProcessor(max_workers=args.workers)
    files = processor.find_java_files(args.patterns)
    
    if not files:
        print("No Java files found matching the patterns")
        return 1
    
    print(f"Found {len(files)} Java files")
    
    # Special handling for structure check
    if args.tool == 'check-structure':
        results, valid_files, invalid_files = processor.validate_files(files)
        
        if args.report:
            report_data = []
            for file_path, result in results.items():
                report_data.append({
                    'file': file_path,
                    'valid': result['valid'],
                    'errors': result['error_count'],
                    'warnings': result['warning_count']
                })
            processor.generate_report(report_data, args.report)
        
        return 0 if not invalid_files else 1
    
    # Run batch processing
    results = processor.run_batch(
        files,
        args.tool,
        args.args,
        validate_first=not args.no_validate,
        skip_invalid=not args.include_invalid,
        parallel=not args.sequential
    )
    
    # Generate report if requested
    if args.report:
        processor.generate_report(results, args.report)
    
    # Return success if all files processed successfully
    return 0 if all(r.get('success', False) for r in results) else 1

if __name__ == "__main__":
    sys.exit(main())