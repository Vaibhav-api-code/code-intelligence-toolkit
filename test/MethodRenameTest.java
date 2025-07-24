/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * Method Rename Test
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-08
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */
public class MethodRenameTest {
    public void computePrice() {
        System.out.println("Calculating price...");
    }

    public void processOrder() {
        computePrice();
        System.out.println("Processing order");
        computePrice();
    }

    public void validateOrder() {
        processOrder();
        computePrice();
    }
}