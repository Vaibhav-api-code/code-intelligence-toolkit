#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
JUnit 4 to JUnit 5 Migration Script

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import re
import sys
from pathlib import Path

class JUnit5Migrator:
    def __init__(self):
        self.conversion_stats = {
            'files_processed': 0,
            'imports_changed': 0,
            'annotations_changed': 0,
            'assertions_changed': 0,
            'exceptions_changed': 0
        }
        
    def migrate_file(self, filepath):
        """Migrate a single Java test file from JUnit 4 to JUnit 5"""
        print(f"Processing: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Step 1: Update imports
        content = self.update_imports(content)
        
        # Step 2: Update annotations
        content = self.update_annotations(content)
        
        # Step 3: Update assertions (parameter order)
        content = self.update_assertions(content)
        
        # Step 4: Update exception testing
        content = self.update_exception_tests(content)
        
        # Step 5: Update Mockito runner
        content = self.update_mockito_runner(content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated: {filepath}")
            self.conversion_stats['files_processed'] += 1
        else:
            print(f"  No changes needed: {filepath}")
            
    def update_imports(self, content):
        """Update JUnit 4 imports to JUnit 5"""
        import_mappings = [
            # JUnit imports
            (r'import\s+org\.junit\.Test;', 'import org.junit.jupiter.api.Test;'),
            (r'import\s+org\.junit\.Before;', 'import org.junit.jupiter.api.BeforeEach;'),
            (r'import\s+org\.junit\.After;', 'import org.junit.jupiter.api.AfterEach;'),
            (r'import\s+org\.junit\.BeforeClass;', 'import org.junit.jupiter.api.BeforeAll;'),
            (r'import\s+org\.junit\.AfterClass;', 'import org.junit.jupiter.api.AfterAll;'),
            (r'import\s+org\.junit\.Ignore;', 'import org.junit.jupiter.api.Disabled;'),
            (r'import\s+static\s+org\.junit\.Assert\.\*;', 'import static org.junit.jupiter.api.Assertions.*;'),
            (r'import\s+org\.junit\.Assert;', 'import org.junit.jupiter.api.Assertions;'),
            
            # Individual assert imports
            (r'import\s+static\s+org\.junit\.Assert\.assertEquals;', 'import static org.junit.jupiter.api.Assertions.assertEquals;'),
            (r'import\s+static\s+org\.junit\.Assert\.assertTrue;', 'import static org.junit.jupiter.api.Assertions.assertTrue;'),
            (r'import\s+static\s+org\.junit\.Assert\.assertFalse;', 'import static org.junit.jupiter.api.Assertions.assertFalse;'),
            (r'import\s+static\s+org\.junit\.Assert\.assertNull;', 'import static org.junit.jupiter.api.Assertions.assertNull;'),
            (r'import\s+static\s+org\.junit\.Assert\.assertNotNull;', 'import static org.junit.jupiter.api.Assertions.assertNotNull;'),
            (r'import\s+static\s+org\.junit\.Assert\.assertSame;', 'import static org.junit.jupiter.api.Assertions.assertSame;'),
            (r'import\s+static\s+org\.junit\.Assert\.assertNotSame;', 'import static org.junit.jupiter.api.Assertions.assertNotSame;'),
            (r'import\s+static\s+org\.junit\.Assert\.assertArrayEquals;', 'import static org.junit.jupiter.api.Assertions.assertArrayEquals;'),
            (r'import\s+static\s+org\.junit\.Assert\.fail;', 'import static org.junit.jupiter.api.Assertions.fail;'),
            
            # RunWith and Rule imports
            (r'import\s+org\.junit\.runner\.RunWith;', ''),
            (r'import\s+org\.junit\.Rule;', ''),
            (r'import\s+org\.junit\.rules\.[^;]+;', ''),
            
            # Mockito updates
            (r'import\s+org\.mockito\.runners\.MockitoJUnitRunner;', 'import org.mockito.junit.jupiter.MockitoExtension;'),
        ]
        
        for pattern, replacement in import_mappings:
            if pattern in content or re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                self.conversion_stats['imports_changed'] += 1
                
        return content
        
    def update_annotations(self, content):
        """Update JUnit 4 annotations to JUnit 5"""
        annotation_mappings = [
            (r'@Before\b', '@BeforeEach'),
            (r'@After\b', '@AfterEach'),
            (r'@BeforeClass\b', '@BeforeAll'),
            (r'@AfterClass\b', '@AfterAll'),
            (r'@Ignore\b', '@Disabled'),
            (r'@RunWith\s*\(\s*MockitoJUnitRunner\.class\s*\)', '@ExtendWith(MockitoExtension.class)'),
        ]
        
        for pattern, replacement in annotation_mappings:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                self.conversion_stats['annotations_changed'] += 1
                
        # Add ExtendWith import if needed
        if '@ExtendWith(MockitoExtension.class)' in content and 'import org.junit.jupiter.api.extension.ExtendWith;' not in content:
            # Add after the last import
            import_section_end = content.rfind('import ')
            if import_section_end != -1:
                line_end = content.find('\n', import_section_end)
                content = content[:line_end+1] + 'import org.junit.jupiter.api.extension.ExtendWith;\n' + content[line_end+1:]
                
        return content
        
    def update_assertions(self, content):
        """Update assertion parameter order from JUnit 4 to JUnit 5"""
        # Pattern to match assertions with message as first parameter
        # JUnit 4: assertEquals(message, expected, actual)
        # JUnit 5: assertEquals(expected, actual, message)
        
        assertion_patterns = [
            # assertEquals with message
            (r'assertEquals\s*\(\s*"([^"]+)"\s*,\s*([^,]+)\s*,\s*([^)]+)\)', r'assertEquals(\2, \3, "\1")'),
            # assertTrue with message
            (r'assertTrue\s*\(\s*"([^"]+)"\s*,\s*([^)]+)\)', r'assertTrue(\2, "\1")'),
            # assertFalse with message
            (r'assertFalse\s*\(\s*"([^"]+)"\s*,\s*([^)]+)\)', r'assertFalse(\2, "\1")'),
            # assertNull with message
            (r'assertNull\s*\(\s*"([^"]+)"\s*,\s*([^)]+)\)', r'assertNull(\2, "\1")'),
            # assertNotNull with message
            (r'assertNotNull\s*\(\s*"([^"]+)"\s*,\s*([^)]+)\)', r'assertNotNull(\2, "\1")'),
            # assertSame with message
            (r'assertSame\s*\(\s*"([^"]+)"\s*,\s*([^,]+)\s*,\s*([^)]+)\)', r'assertSame(\2, \3, "\1")'),
            # assertNotSame with message
            (r'assertNotSame\s*\(\s*"([^"]+)"\s*,\s*([^,]+)\s*,\s*([^)]+)\)', r'assertNotSame(\2, \3, "\1")'),
        ]
        
        for pattern, replacement in assertion_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                self.conversion_stats['assertions_changed'] += 1
                
        return content
        
    def update_exception_tests(self, content):
        """Update exception testing from JUnit 4 to JUnit 5"""
        # Pattern: @Test(expected = Exception.class)
        pattern = r'@Test\s*\(\s*expected\s*=\s*([^)]+)\s*\)'
        
        if re.search(pattern, content):
            print("  Warning: Found @Test(expected=...) - manual review needed for assertThrows")
            # Add a TODO comment
            content = re.sub(pattern, r'@Test\n    // TODO: Convert to assertThrows(\1, () -> { ... })', content)
            self.conversion_stats['exceptions_changed'] += 1
            
        return content
        
    def update_mockito_runner(self, content):
        """Update Mockito runner usage"""
        # Already handled in annotations, but ensure we catch any edge cases
        if 'MockitoJUnitRunner' in content and 'MockitoExtension' not in content:
            content = content.replace('MockitoJUnitRunner', 'MockitoExtension')
            
        return content
        
    def migrate_directory(self, directory):
        """Migrate all test files in a directory"""
        test_files = list(Path(directory).rglob('*Test.java'))
        
        print(f"Found {len(test_files)} test files to process")
        
        for test_file in test_files:
            self.migrate_file(str(test_file))
            
        self.print_summary()
        
    def print_summary(self):
        """Print migration summary"""
        print("\n=== Migration Summary ===")
        for key, value in self.conversion_stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_junit5.py <test_directory>")
        sys.exit(1)
        
    test_dir = sys.argv[1]
    migrator = JUnit5Migrator()
    migrator.migrate_directory(test_dir)