/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * Test A S T Context
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-08
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */

package com.example.test;

/**
 * Test class for AST context functionality
 */
public class TestASTContext {
    private String testField = "test";
    private int counter = 0;
    
    public TestASTContext() {
        this.counter = 1;
    }
    
    public void processOrder(String orderId) {
        // This is a test method
        String localVar = "processing: " + orderId;
        System.out.println(localVar);
        counter++;
        helperMethod();
    }
    
    private void helperMethod() {
        String helperVar = "helper";
        System.out.println(helperVar);
        unusedPrivateMethod();
    }
    
    private void unusedPrivateMethod() {
        // This method is never called
        System.out.println("Never called");
    }
    
    public int getCounter() {
        return counter;
    }
    
    public static void main(String[] args) {
        TestASTContext test = new TestASTContext();
        test.processOrder("ORDER123");
        System.out.println("Counter: " + test.getCounter());
    }
}