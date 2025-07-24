/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * Test Java Refactoring
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-08
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */
public class TestJavaRefactoring {
    private int counter = 0;
    private String name;
    
    public TestJavaRefactoring(String name) {
        this.name = name;
        this.counter = 1;
    }
    
    public void processItem(String item) {
        int counter = 10; // Local variable shadows instance field
        System.out.println("Processing: " + item);
        System.out.println("Local counter: " + counter);
        System.out.println("Instance counter: " + this.counter);
        
        for (int i = 0; i < counter; i++) {
            performAction(i);
        }
        
        this.counter++; // Increment instance field
    }
    
    private void performAction(int index) {
        System.out.println("Action " + index + " with counter " + this.counter);
    }
    
    public int getCounter() {
        return this.counter;
    }
    
    // Another method with its own counter variable
    public void anotherMethod() {
        int counter = 999; // Different scope, should not be renamed
        System.out.println("Another counter: " + counter);
    }
}