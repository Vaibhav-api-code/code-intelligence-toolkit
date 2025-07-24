/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * SpoonVariableRenamer.java - Processor for renaming variables with Spoon
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-08
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */
import spoon.processing.AbstractProcessor;
import spoon.reflect.code.CtLocalVariable;
import spoon.reflect.code.CtVariableRead;
import spoon.reflect.code.CtVariableWrite;
import spoon.reflect.declaration.CtVariable;
import spoon.reflect.reference.CtVariableReference;
import spoon.reflect.declaration.CtParameter;
import spoon.reflect.declaration.CtField;

public class SpoonVariableRenamer extends AbstractProcessor<CtVariableReference<?>> {
    private final CtVariable<?> targetVariable;
    private final String newName;
    private int renameCount = 0;
    
    public SpoonVariableRenamer(CtVariable<?> targetVariable, String newName) {
        this.targetVariable = targetVariable;
        this.newName = newName;
    }
    
    @Override
    public void process(CtVariableReference<?> variableRef) {
        // Check if this reference points to our target variable
        if (variableRef.getDeclaration() != null && 
            variableRef.getDeclaration().equals(targetVariable)) {
            // Rename the reference
            variableRef.setSimpleName(newName);
            renameCount++;
        }
    }
    
    public int getRenameCount() {
        return renameCount;
    }
}