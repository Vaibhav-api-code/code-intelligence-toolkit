/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * Test Java File
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-20
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */

package com.example.test;

import java.util.List;
import java.util.ArrayList;

/**
 * Test Java file for find_text_v3.py functionality
 */
public class TestJavaFile {
    private String name;
    private int value;
    
    public TestJavaFile(String name) {
        this.name = name;
        this.value = 42;
    }
    
    public void processOrder(String orderId) {
        System.out.println("Processing order: " + orderId);
        // This contains SEARCH_PATTERN
        String pattern = "SEARCH_PATTERN in processOrder";
        validateOrder(orderId);
    }
    
    private void validateOrder(String orderId) {
        if (orderId == null || orderId.isEmpty()) {
            System.out.println("Invalid order ID");
            return;
        }
        System.out.println("Order validated: " + orderId);
    }
    
    public List<String> findPatterns() {
        List<String> patterns = new ArrayList<>();
        patterns.add("SEARCH_PATTERN in list");
        patterns.add("Another pattern");
        
        // Nested class example
        class LocalClass {
            void localMethod() {
                String local = "SEARCH_PATTERN in nested class";
                System.out.println(local);
            }
        }
        
        return patterns;
    }
    
    static class StaticNestedClass {
        public void staticMethod() {
            // Another occurrence of pattern
            System.out.println("SEARCH_PATTERN in static nested class");
        }
    }
}