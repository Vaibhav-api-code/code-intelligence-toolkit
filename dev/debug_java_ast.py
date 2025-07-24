#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Debug script to understand why Java AST parsing isn't working.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import javalang
import sys
from pathlib import Path

def debug_java_ast():
    test_file = "test_data/NestedClassExample.java"
    
    print(f"🔍 Debugging Java AST parsing for {test_file}")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print("✓ File read successfully")
        print(f"File length: {len(code)} characters")
        
        # Try to parse
        tree = javalang.parse.parse(code)
        print("✓ AST parsing successful")
        
        # Walk the tree and show what we find
        print("\n📋 AST nodes found:")
        
        for path, node in tree:
            node_type = type(node).__name__
            line = getattr(node, 'position', None)
            line_num = line.line if line else "unknown"
            
            if isinstance(node, (javalang.tree.ClassDeclaration, 
                               javalang.tree.MethodDeclaration,
                               javalang.tree.ConstructorDeclaration)):
                name = getattr(node, 'name', 'unnamed')
                print(f"  Line {line_num:2}: {node_type:20} '{name}'")
                
                # Show path structure
                print(f"         Path: {[type(p).__name__ if hasattr(p, '__name__') else str(p) for p in path]}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_java_ast()