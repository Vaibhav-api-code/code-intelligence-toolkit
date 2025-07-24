#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Improved Java Analyzer - Creates CALLS relationships in Neo4j

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

class ImprovedJavaAnalyzer:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.method_patterns = {
            'method_call': r'(\w+(?:\.\w+)?)\s*\([^()]*(?:\([^()]*\)[^()]*)*\)',
            'qualified_call': r'(\w+)\.(\w+)\s*\(',
            'this_call': r'this\.(\w+)\s*\(',
            'super_call': r'super\.(\w+)\s*\(',
        }
        self.class_methods = {}  # Cache of class -> methods mapping
    
    def close(self):
        self.driver.close()
    
    def _load_existing_methods(self):
        """Load existing methods from Neo4j database"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Method)
                RETURN m.class as class, m.signature as signature
            """)
            
            for record in result:
                class_name = record['class']
                signature = record['signature']
                if class_name not in self.class_methods:
                    self.class_methods[class_name] = []
                self.class_methods[class_name].append(signature)
            
            print(f"Loaded {sum(len(methods) for methods in self.class_methods.values())} methods from {len(self.class_methods)} classes")
    
    def _extract_method_body(self, content, signature):
        """Extract the body of a specific method"""
        # Escape special characters in signature for regex
        escaped_sig = re.escape(