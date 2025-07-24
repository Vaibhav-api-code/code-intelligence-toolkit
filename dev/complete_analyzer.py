#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Complete Java Analyzer - Populates Neo4j with full structure including CALLS relationships

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import os
from pathlib import Path
from neo4j import GraphDatabase

class CompleteJavaAnalyzer:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear the entire database"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Cleared database")
    
    def extract_java_elements(self, java_content, file_path):
        """Extract package, class, and methods from Java content"""
        # Extract package
        package_match = re.search(r'package\s+([^;]+);', java_content)
        package_name = package_match.group(1) if package_match else None
        
        # Extract class name
        class_match = re.search(r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)', java_content)
        if not class_match:
            return None
        
        class_name = class_match.group(1)
        full_class_name = f"{package_name}.{class_name}" if package_name else class_name
        
        # Extract imports
        imports = {}
        import_matches = re.finditer(r'import\s+(?:static\s+)?([^;]+);', java_content)
        for match in import_matches:
            import_path = match.group(1)
            if '.' in import_path:
                simple_name = import_path.split('.')[-1]
                imports[simple_name] = import_path
        
        # Extract methods
        methods = []
        # Pattern to match method declarations
        method_pattern = r'((?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(?:abstract)?\s*(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)(?:\s*throws\s+[^{]+)?)\s*\{'
        
        for match in re.finditer(method_pattern, java_content, re.MULTILINE):
            signature = match.group(1).strip()
            method_name = match.group(2)
            
            # Extract method body
            start_pos = match.end() - 1
            brace_count = 1
            pos = start_pos + 1
            
            while pos < len(java_content) and brace_count > 0:
                if java_content