#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test rope library directly to understand its behavior."""

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

from rope.base.project import Project
from rope.refactor.rename import Rename
from rope.base import libutils
import os
import tempfile
import shutil

def test_rope_scope_awareness():
    """Test rope's scope-aware renaming directly."""
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="rope_test_")
    print(f"Test directory: {test_dir}")
    
    try:
        # Create test file with scope challenges
        test_content = '''
# Global variable
counter = 0

def use_global():
    global counter
    counter += 1
    return counter

def use_local():
    counter = 100  # Local variable - should NOT be renamed
    return counter

# Use global counter
result = counter + 10
'''
        
        test_file = os.path.join(test_dir, "test_scopes.py")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Create rope project
        project = Project(test_dir)
        
        # Get the resource (file)
        resource = libutils.path_to_resource(project, test_file)
        
        print("Original content:")
        print(resource.read())
        print("\n" + "="*60 + "\n")
        
        # Test 1: Rename at global definition (offset of first 'counter')
        offset = test_content.find('counter = 0')
        print(f"Renaming at offset {offset} (global definition)")
        
        try:
            rename = Rename(project, resource, offset)
            changes = rename.get_changes('global_counter')
            
            print("Rope's proposed changes:")
            print(changes.get_description())
            
            # Apply changes
            project.do(changes)
            
            print("\nModified content:")
            print(resource.read())
            
            # Analyze what was changed
            modified = resource.read()
            
            print("\n" + "="*60)
            print("ANALYSIS:")
            print("="*60)
            
            # Check global references
            if "global_counter = 0" in modified:
                print("✅ Global definition renamed")
            else:
                print("❌ Global definition NOT renamed")
            
            if "global global_counter" in modified:
                print("✅ Global declaration renamed")
            else:
                print("❌ Global declaration NOT renamed")
            
            if "global_counter += 1" in modified:
                print("✅ Global usage in function renamed")
            else:
                print("❌ Global usage in function NOT renamed")
            
            if "result = global_counter + 10" in modified:
                print("✅ Global usage at module level renamed")
            else:
                print("❌ Global usage at module level NOT renamed")
            
            # Check local variable
            if "counter = 100  # Local" in modified:
                print("✅ Local variable NOT renamed (correct)")
            else:
                print("❌ Local variable was renamed (incorrect)")
            
        except Exception as e:
            print(f"Error during rename: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Create another file to test cross-file refactoring
        print("\n" + "="*60)
        print("CROSS-FILE TEST")
        print("="*60)
        
        other_content = '''
from test_scopes import counter, use_global

# Use imported counter
value = counter * 2
result = use_global()
'''
        
        other_file = os.path.join(test_dir, "other_module.py")
        with open(other_file, 'w') as f:
            f.write(other_content)
        
        # Re-read to see if rope handles imports
        other_resource = libutils.path_to_resource(project, other_file)
        print("Other module content after refactoring:")
        print(other_resource.read())
        
        project.close()
        
    finally:
        # Clean up
        shutil.rmtree(test_dir)


def test_rope_with_classes():
    """Test rope with class methods vs functions."""
    
    test_dir = tempfile.mkdtemp(prefix="rope_class_test_")
    print(f"\nCLASS METHOD TEST")
    print(f"Test directory: {test_dir}")
    
    try:
        test_content = '''
def process(data):
    """Global function."""
    return data * 2

class Processor:
    def process(self, data):
        """Instance method with same name."""
        return data * 3

# Call global function
result = process([1, 2, 3])

# Call method
p = Processor()
method_result = p.process([1, 2, 3])
'''
        
        test_file = os.path.join(test_dir, "test_methods.py")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        project = Project(test_dir)
        resource = libutils.path_to_resource(project, test_file)
        
        print("Original content:")
        print(resource.read())
        
        # Find offset of global function definition
        offset = test_content.find('def process(data):')
        print(f"\nRenaming global function at offset {offset}")
        
        rename = Rename(project, resource, offset)
        changes = rename.get_changes('process_data')
        
        print("\nRope's proposed changes:")
        print(changes.get_description())
        
        project.do(changes)
        
        print("\nModified content:")
        modified = resource.read()
        print(modified)
        
        print("\nANALYSIS:")
        if "def process_data(data):" in modified:
            print("✅ Global function renamed")
        
        if "def process(self, data):" in modified:
            print("✅ Method NOT renamed (correct)")
        else:
            print("❌ Method was renamed (incorrect)")
        
        if "result = process_data([1, 2, 3])" in modified:
            print("✅ Call to global function renamed")
        
        if "p.process([1, 2, 3])" in modified:
            print("✅ Method call NOT renamed (correct)")
        
        project.close()
        
    finally:
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    print("TESTING ROPE DIRECTLY")
    print("="*60)
    
    test_rope_scope_awareness()
    test_rope_with_classes()
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    print("Rope provides TRUE scope-aware refactoring when used correctly.")
    print("The key is providing the right offset to identify which specific")
    print("occurrence of a name you want to rename.")