#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script for semantic diff scoring system.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import tempfile
import os
import subprocess
import sys
from pathlib import Path

def create_test_files():
    """Create test files to demonstrate the scoring system."""
    
    # Original file with simple logic
    original_content = '''
public class Calculator {
    private int value;
    
    public Calculator(int initialValue) {
        this.value = initialValue;
    }
    
    // Simple addition method
    public int add(int number) {
        return value + number;
    }
    
    // Simple multiplication  
    public int multiply(int factor) {
        return value * factor;
    }
    
    public int getValue() {
        return value;
    }
}
'''
    
    # Modified file with logic changes, new methods, formatting changes
    modified_content = '''
public class Calculator {
    private int value;
    private boolean debugMode = false;  // New field
    
    public Calculator(int initialValue) {
        this.value = initialValue;
        this.debugMode = false;  // Logic change in constructor
    }
    
    // Enhanced addition with validation - LOGIC CHANGE
    public int add(int number) {
        if (number < 0) {
            throw new IllegalArgumentException("Negative numbers not allowed");
        }
        
        if (debugMode) {
            System.out.println("Adding " + number + " to " + value);
        }
        
        return value + number;
    }
    
    // Multiplication with overflow protection - LOGIC CHANGE  
    public int multiply(int factor) {
        if (factor == 0) {
            return 0;
        }
        
        long result = (long) value * factor;
        if (result > Integer.MAX_VALUE || result < Integer.MIN_VALUE) {
            throw new ArithmeticException("Integer overflow");
        }
        
        return (int) result;
    }
    
    // NEW METHOD
    public void setDebugMode(boolean debug) {
        this.debugMode = debug;
    }
    
    // NEW METHOD  
    public boolean isDebugMode() {
        return debugMode;
    }
    
    public int getValue() {
        return value;  // Unchanged
    }
    
    // NEW METHOD with complex logic
    public double calculateAverage(int[] numbers) {
        if (numbers == null || numbers.length == 0) {
            return 0.0;
        }
        
        long sum = 0;
        for (int num : numbers) {
            sum += num;
        }
        
        return (double) sum / numbers.length;
    }
}
'''
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='_original.java', delete=False) as f1:
        f1.write(original_content)
        original_file = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_modified.java', delete=False) as f2:
        f2.write(modified_content)
        modified_file = f2.name
    
    return original_file, modified_file

def run_scoring_test(script_path, original_file, modified_file):
    """Run the semantic diff scoring test."""
    
    print("🧪 Testing Semantic Diff Scoring System")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Basic Scoring Analysis',
            'args': ['--score'],
            'description': 'Shows comprehensive impact analysis with recommendations'
        },
        {
            'name': 'JSON Output',
            'args': ['--score-json'],
            'description': 'Machine-readable scoring for automation'
        },
        {
            'name': 'Logic Changes Only + Score',
            'args': ['--logic-only', '--score'],
            'description': 'Focus on logic changes with impact scoring'
        },
        {
            'name': 'High Risk Threshold',
            'args': ['--score', '--risk-threshold', 'HIGH'],
            'description': 'Only show if risk is HIGH or CRITICAL'
        },
        {
            'name': 'Medium Risk Threshold',
            'args': ['--score', '--risk-threshold', 'MEDIUM'],
            'description': 'Show if risk is MEDIUM, HIGH, or CRITICAL'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print("-" * 40)
        
        cmd = [sys.executable, script_path, original_file, modified_file] + test_case['args']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ SUCCESS")
                print("Output:")
                print(result.stdout)
            else:
                print("❌ FAILED")
                print("Error:")
                print(result.stderr)
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("\n" + "=" * 50)

def main():
    # Path to the semantic diff script
    script_path = Path(__file__).parent / "semantic_diff_ast.py"
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        sys.exit(1)
    
    print("🚀 Semantic Diff Scoring System Test")
    print(f"Testing script: {script_path}")
    
    # Create test files
    original_file, modified_file = create_test_files()
    
    try:
        print(f"\n📁 Test files created:")
        print(f"  Original: {original_file}")
        print(f"  Modified: {modified_file}")
        
        # Run tests
        run_scoring_test(str(script_path), original_file, modified_file)
        
        print("\n✨ All tests completed!")
        print("\nKey Features Demonstrated:")
        print("• Risk assessment (LOW/MEDIUM/HIGH/CRITICAL)")
        print("• Impact scoring (0-100 scale)")
        print("• Change distribution analysis")
        print("• Automated recommendations")
        print("• JSON output for CI/CD integration")
        print("• Risk threshold filtering")
        
    finally:
        # Clean up temporary files
        try:
            os.unlink(original_file)
            os.unlink(modified_file)
            print(f"\n🧹 Cleaned up temporary files")
        except:
            pass

if __name__ == "__main__":
    main()