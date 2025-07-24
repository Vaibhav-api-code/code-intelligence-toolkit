#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Analyze test timing output from gradle test runs.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from collections import defaultdict

def parse_test_output(filename):
    """Parse test output and extract timing information."""
    test_timings = []
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Pattern to match test end and duration
    # TEST END: ClassName.methodName
    # Duration: X ms (Xs)
    test_pattern = r'TEST END: ([^\n]+)\n.*?Duration: (\d+) ms'
    
    matches = re.findall(test_pattern, content, re.DOTALL)
    
    for test_name, duration_ms in matches:
        duration = int(duration_ms)
        test_timings.append((test_name, duration))
    
    return test_timings

def analyze_timings(test_timings):
    """Analyze test timings and print summary."""
    if not test_timings:
        print("No test timing data found.")
        return
    
    # Sort by duration (slowest first)
    sorted_timings = sorted(test_timings, key=lambda x: x[1], reverse=True)
    
    # Calculate statistics
    total_time = sum(duration for _, duration in sorted_timings)
    avg_time = total_time / len(sorted_timings)
    
    print(f"\nTest Timing Analysis")
    print("=" * 80)
    print(f"Total tests analyzed: {len(sorted_timings)}")
    print(f"Total execution time: {total_time}ms ({total_time/1000:.2f}s)")
    print(f"Average test time: {avg_time:.2f}ms")
    print()
    
    # Show tests over 5 seconds
    slow_tests = [(name, duration) for name, duration in sorted_timings if duration >= 5000]
    if slow_tests:
        print(f"Tests over 5 seconds ({len(slow_tests)} tests):")
        print("-" * 80)
        for name, duration in slow_tests:
            print(f"{name:<60} {duration:>10}ms ({duration/1000:>6.2f}s)")
        print()
    
    # Show tests over 1 second
    medium_tests = [(name, duration) for name, duration in sorted_timings if 1000 <= duration < 5000]
    if medium_tests:
        print(f"Tests between 1-5 seconds ({len(medium_tests)} tests):")
        print("-" * 80)
        for name, duration in medium_tests[:20]:  # Show top 20
            print(f"{name:<60} {duration:>10}ms ({duration/1000:>6.2f}s)")
        if len(medium_tests) > 20:
            print(f"... and {len(medium_tests) - 20} more tests")
        print()
    
    # Show top 20 slowest tests overall
    print("Top 20 Slowest Tests:")
    print("-" * 80)
    for i, (name, duration) in enumerate(sorted_timings[:20], 1):
        print(f"{i:2d}. {name:<57} {duration:>10}ms ({duration/1000:>6.2f}s)")
    
    # Group by test class
    class_timings = defaultdict(list)
    for name, duration in test_timings:
        class_name = name.split('.')[0] if '.' in name else name
        class_timings[class_name].append(duration)
    
    # Calculate total time per test class
    class_totals = []
    for class_name, durations in class_timings.items():
        total = sum(durations)
        count = len(durations)
        avg = total / count
        class_totals.append((class_name, total, count, avg))
    
    # Sort by total time
    class_totals.sort(key=lambda x: x[1], reverse=True)
    
    print("\n\nSlowest Test Classes by Total Time:")
    print("-" * 80)
    print(f"{'Class Name':<40} {'Total Time':>15} {'Test Count':>10} {'Avg Time':>15}")
    print("-" * 80)
    for class_name, total, count, avg in class_totals[:20]:
        print(f"{class_name:<40} {total:>10}ms ({total/1000:>4.1f}s) {count:>10} {avg:>10.0f}ms")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "test_output.txt"
    
    test_timings = parse_test_output(filename)
    analyze_timings(test_timings)