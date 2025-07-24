#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Wrapper for analyze_unused_methods_rg.py that adds timeout and truncation functionality.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import sys
import signal
import time
import os

# Timeout in seconds (configurable via environment variable)

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

TIMEOUT = int(os.environ.get('UNUSED_METHODS_TIMEOUT', '60'))  # Default 60s for this extensive search

def run_with_timeout(cmd, timeout):
    """Run command with timeout, capturing output progressively."""
    
    # Start the process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    output_lines = []
    start_time = time.time()
    methods_found = 0
    last_method = ""
    
    try:
        # Read output line by line
        while True:
            # Check if timeout exceeded
            if time.time() - start_time > timeout:
                print(f"\n{'='*80}")
                print(f"WARNING: Analysis truncated after {timeout} seconds")
                print(f"Analyzed {methods_found} methods, last was: {last_method}")
                print(f"")
                print(f"Solutions to prevent timeout:")
                print(f"")
                print(f"  # Analyze a smaller file or specific class")
                print(f"  ./run_any_python_tool.sh analyze_unused_methods.py src/main/java/com/example/smaller/Class.java")
                print(f"")
                print(f"  # Split analysis by using grep to find specific methods first")
                print(f"  rg 'public.*methodName' -t java | head -20")
                print(f"")
                print(f"  # Or increase timeout for large files")
                print(f"  UNUSED_METHODS_TIMEOUT=120 ./run_any_python_tool.sh analyze_unused_methods.py {' '.join(sys.argv[1:])}")
                print(f"")
                print(f"  # Pro tip: Large files like DataProcessorControllerV2.java may need 2-3 minutes")
                print(f"{'='*80}")
                process.terminate()
                break
            
            # Try to read a line
            line = process.stdout.readline()
            if line:
                print(line, end='')
                output_lines.append(line)
                
                # Track progress
                if "Checking method:" in line:
                    methods_found += 1
                    last_method = line.strip()
                    
            elif process.poll() is not None:
                # Process finished
                break
            else:
                # No output available, sleep briefly
                time.sleep(0.01)
                
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        process.terminate()
        
    # Get any remaining output
    try:
        remaining, _ = process.communicate(timeout=1)
        if remaining:
            print(remaining, end='')
            output_lines.append(remaining)
    except subprocess.TimeoutExpired:
        process.kill()
    
    return process.returncode, output_lines

def main():
    # Pass all arguments to the original script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    original_script = os.path.join(script_dir, 'analyze_unused_methods_actual.py')
    
    cmd = [sys.executable, original_script] + sys.argv[1:]
    
    print(f"Analyzing unused methods with {TIMEOUT}s timeout...")
    print("-" * 80)
    
    returncode, output = run_with_timeout(cmd, TIMEOUT)
    
    if returncode != 0 and returncode is not None:
        sys.exit(returncode)

if __name__ == "__main__":
    main()