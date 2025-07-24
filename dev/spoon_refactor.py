#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Easy-to-use wrapper for Spoon-based Java refactoring.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path
import sys
import difflib


class SpoonRefactorer:
    """Wrapper for Spoon refactoring operations."""
    
    def __init__(self):
        self.spoon_jar = Path("lib/spoon-core-10.4.0-jar-with-dependencies.jar")
        self.processors_dir = Path("spoon_processors")
        
        if not self.spoon_jar.exists():
            raise FileNotFoundError(f"Spoon JAR not found at {self.spoon_jar}")
        
        if not self.processors_dir.exists():
            raise FileNotFoundError(f"Spoon processors not found at {self.processors_dir}")
    
    def rename_variable(self, input_file: Path, old_name: str, new_name: str,
                       variable_type: str = "all", target_class: str = None,
                       target_method: str = None) -> tuple[bool, str, str]:
        """
        Rename a variable with full scope awareness.
        
        Returns: (success, new_content, error_message)
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as tmp_out:
            output_file = tmp_out.name
        
        try:
            # Build classpath
            classpath = f"{self.spoon_jar}:{self.processors_dir}"
            
            # Build command
            cmd = [
                "java", "-cp", classpath,
                "SpoonRefactorLauncher",
                str(input_file),
                output_file,
                old_name,
                new_name,
                variable_type,
                target_class or "null",
                target_method or "null"
            ]
            
            # Run Spoon
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_file).exists():
                new_content = Path(output_file).read_text()
                return True, new_content, None
            else:
                error = result.stderr or "Unknown error"
                return False, None, error
                
        finally:
            # Cleanup
            if Path(output_file).exists():
                Path(output_file).unlink()


def create_demo_file():
    """Create a demo Java file showing scope challenges."""
    
    content = '''public class SpoonDemo {
    private int value = 10;  // Instance field
    
    public void processA() {
        value++;  // Uses instance field
        System.out.println("Instance value: " + value);
    }
    
    public void processB() {
        int value = 100;  // Local variable
        value++;  // Uses local variable
        System.out.println("Local value: " + value);
    }
    
    public void processC(int value) {
        // Parameter 'value' shadows instance field
        System.out.println("Parameter value: " + value);
        System.out.println("Instance value: " + this.value);
    }
    
    class Inner {
        private int value = 1000;  // Inner class field
        
        public void process() {
            value++;  // Uses inner class field
            System.out.println("Inner value: " + value);
        }
    }
}'''
    
    return content


def main():
    parser = argparse.ArgumentParser(
        description='Spoon-based Java refactoring with scope awareness',
        epilog='''
EXAMPLES:
  # Rename all variables named 'value'
  %(prog)s rename Demo.java value newValue
  
  # Rename only instance fields named 'value'
  %(prog)s rename Demo.java value newValue --type field
  
  # Rename variable only in specific method
  %(prog)s rename Demo.java value localValue --class SpoonDemo --method processB
  
  # Demo mode - shows scope-aware refactoring
  %(prog)s demo

VARIABLE TYPES:
  all       - Rename all variables with the name
  field     - Only instance/static fields
  local     - Only local variables
  parameter - Only method parameters
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Rename command
    rename_parser = subparsers.add_parser('rename', help='Rename a variable')
    rename_parser.add_argument('file', help='Java file to refactor')
    rename_parser.add_argument('old_name', help='Current variable name')
    rename_parser.add_argument('new_name', help='New variable name')
    rename_parser.add_argument('--type', choices=['all', 'field', 'local', 'parameter'],
                              default='all', help='Type of variable to rename')
    rename_parser.add_argument('--class', dest='target_class', help='Target specific class')
    rename_parser.add_argument('--method', dest='target_method', help='Target specific method')
    rename_parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run interactive demo')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    refactorer = SpoonRefactorer()
    
    if args.command == 'demo':
        print("SPOON SCOPE-AWARE REFACTORING DEMO")
        print("=" * 80)
        
        # Create demo file
        demo_file = Path("SpoonDemo.java")
        demo_content = create_demo_file()
        demo_file.write_text(demo_content)
        
        try:
            print("\nOriginal file has multiple 'value' variables:")
            print("- Instance field (line 2)")
            print("- Local variable in processB (line 11)")
            print("- Parameter in processC (line 16)")
            print("- Inner class field (line 22)")
            
            # Demo 1: Rename only fields
            print("\n1. Renaming only fields from 'value' to 'fieldValue':")
            print("-" * 60)
            
            success, new_content, error = refactorer.rename_variable(
                demo_file, "value", "fieldValue", "field"
            )
            
            if success:
                diff = difflib.unified_diff(
                    demo_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile="Original",
                    tofile="After renaming fields"
                )
                print(''.join(diff))
                
                # Reset file
                demo_file.write_text(demo_content)
            
            # Demo 2: Rename only in specific method
            print("\n2. Renaming 'value' to 'localValue' only in processB method:")
            print("-" * 60)
            
            success, new_content, error = refactorer.rename_variable(
                demo_file, "value", "localValue", "local", "SpoonDemo", "processB"
            )
            
            if success:
                diff = difflib.unified_diff(
                    demo_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile="Original",
                    tofile="After renaming in processB"
                )
                print(''.join(diff))
                
        finally:
            # Cleanup
            if demo_file.exists():
                demo_file.unlink()
                
        print("\n✅ Spoon provides true scope-aware refactoring for Java!")
        
    elif args.command == 'rename':
        input_file = Path(args.file)
        
        if not input_file.exists():
            print(f"Error: File '{args.file}' not found")
            sys.exit(1)
        
        # Store original content
        original_content = input_file.read_text()
        
        # Perform refactoring
        success, new_content, error = refactorer.rename_variable(
            input_file, args.old_name, args.new_name,
            args.type, args.target_class, args.target_method
        )
        
        if success:
            print(f"✅ Successfully renamed '{args.old_name}' to '{args.new_name}'")
            
            # Show diff
            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"{args.file} (original)",
                tofile=f"{args.file} (modified)"
            )
            diff_text = ''.join(diff)
            
            if diff_text:
                print("\nChanges:")
                print(diff_text)
            else:
                print("\nNo changes made (variable not found in specified scope)")
            
            # Apply changes if not dry-run
            if not args.dry_run and diff_text:
                input_file.write_text(new_content)
                print(f"\n✅ File updated: {args.file}")
            elif args.dry_run:
                print("\nDry run - no changes applied")
                
        else:
            print(f"❌ Refactoring failed: {error}")
            sys.exit(1)


if __name__ == '__main__':
    main()