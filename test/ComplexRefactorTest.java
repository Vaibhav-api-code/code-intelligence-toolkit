/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * Complex Refactor Test
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-08
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */
public class ComplexRefactorTest {
    public void processOrder(String orderData) {
        String data = orderData.trim();
        System.out.println("Processing: " + data);
        
        if (data.length() > 0) {
            validateData(data);
            String result = transformData(data);
            System.out.println("Result: " + result);
        }
    }
    
    private void validateData(String data) {
        System.out.println("Validating: " + data);
    }
    
    private String transformData(String data) {
        return data.toUpperCase();
    }
}