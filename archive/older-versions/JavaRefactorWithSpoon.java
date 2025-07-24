/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * JavaRefactorWithSpoon.java - Java refactoring engine using Spoon
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-08
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */
import spoon.Launcher;
import spoon.reflect.CtModel;
import spoon.reflect.declaration.CtVariable;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.visitor.filter.TypeFilter;
import spoon.reflect.cu.SourcePosition;

import java.io.File;
import java.util.List;
import java.util.ArrayList;

public class JavaRefactorWithSpoon {

    public static void main(String[] args) {
        // --- Enhanced Argument Parsing ---
        String filePath = null;
        Integer lineNumber = null;
        String oldName = null;
        String newName = null;
        boolean isMethod = false;
        List<String> sourceDirs = new ArrayList<>();
        List<String> jarPaths = new ArrayList<>();

        // Parse arguments - support both old and new format for consistency
        if (args.length >= 4 && !args[0].startsWith("--")) {
            // Legacy format: <file_path> <line_number> <old_name> <new_name> [--method]
            filePath = args[0];
            lineNumber = Integer.parseInt(args[1]);
            oldName = args[2];
            newName = args[3];
            isMethod = args.length > 4 && "--method".equals(args[4]);
        } else {
            // New format with named arguments
            for (int i = 0; i < args.length; i++) {
                switch (args[i]) {
                    case "--file":
                        filePath = args[++i];
                        break;
                    case "--line":
                        lineNumber = Integer.parseInt(args[++i]);
                        break;
                    case "--old-name":
                        oldName = args[++i];
                        break;
                    case "--new-name":
                        newName = args[++i];
                        break;
                    case "--method":
                        isMethod = true;
                        break;
                    case "--source-dir":
                        sourceDirs.add(args[++i]);
                        break;
                    case "--jar":
                    case "--jar-path":
                        jarPaths.add(args[++i]);
                        break;
                    default:
                        System.err.println("Unknown argument: " + args[i]);
                }
            }
        }

        if (filePath == null || lineNumber == null || oldName == null || newName == null) {
            System.err.println("Usage: java -jar spoon-refactor-engine.jar <file_path> <line_number> <old_name> <new_name> [--method]");
            System.err.println("   OR: java -jar spoon-refactor-engine.jar --file <path> --line <num> --old-name <name> --new-name <name> [--method] [--source-dir <path>]*");
            System.err.println("\nOptions:");
            System.err.println("  --method        Indicates renaming a method instead of a variable");
            System.err.println("  --source-dir    Add a source directory for better context (can be specified multiple times)");
            System.exit(1);
        }

        try {
            // --- Spoon Configuration ---
            Launcher launcher = new Launcher();
            
            // Configure Spoon environment
            launcher.getEnvironment().setPreserveLineNumbers(true);
            launcher.getEnvironment().setAutoImports(true);
            launcher.getEnvironment().setNoClasspath(false);
            launcher.getEnvironment().setCommentEnabled(true);
            
            // Add source directories
            if (sourceDirs.isEmpty()) {
                // If no source dirs specified, use the file's parent directory
                File sourceFile = new File(filePath);
                File parentDir = sourceFile.getParentFile();
                if (parentDir != null && parentDir.exists()) {
                    launcher.addInputResource(parentDir.getAbsolutePath());
                    System.err.println("Info: Using parent directory as source path: " + parentDir.getAbsolutePath());
                }
            } else {
                // Add all specified source directories
                for (String sourceDir : sourceDirs) {
                    File dir = new File(sourceDir);
                    if (dir.exists() && dir.isDirectory()) {
                        launcher.addInputResource(sourceDir);
                        System.err.println("Info: Added source directory: " + dir.getAbsolutePath());
                    } else {
                        System.err.println("Warning: Source directory not found: " + sourceDir);
                    }
                }
            }
            
            // Build the model
            System.err.println("Info: Building Spoon model...");
            launcher.buildModel();
            CtModel model = launcher.getModel();
            
            if (isMethod) {
                renameMethod(model, filePath, lineNumber, oldName, newName, launcher);
            } else {
                renameVariable(model, filePath, lineNumber, oldName, newName, launcher);
            }
            
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace(System.err);
            System.exit(1);
        }
    }
    
    private static void renameVariable(CtModel model, String filePath, int lineNumber, 
                                     String oldName, String newName, Launcher launcher) throws Exception {
        // Find the specific variable declaration
        CtVariable<?> targetVariable = null;
        File targetFile = new File(filePath).getCanonicalFile();
        
        for (CtVariable<?> variable : model.getElements(new TypeFilter<>(CtVariable.class))) {
            if (variable.getSimpleName().equals(oldName) && 
                variable.getPosition().isValidPosition() &&
                variable.getPosition().getLine() == lineNumber) {
                
                // Check if it's in the target file
                File varFile = variable.getPosition().getFile();
                if (varFile != null && varFile.getCanonicalFile().equals(targetFile)) {
                    targetVariable = variable;
                    System.err.println("Info: Found variable '" + oldName + "' at line " + lineNumber);
                    break;
                }
            }
        }
        
        if (targetVariable == null) {
            System.err.println("Error: Could not find variable '" + oldName + "' at line " + lineNumber);
            System.err.println("Debug: Searched for variable declarations in file: " + filePath);
            // Print original file content
            printOriginalFile(filePath);
            System.exit(0);
        }
        
        // Use Spoon's refactoring - first rename the declaration
        System.err.println("Info: Renaming variable and all its references...");
        targetVariable.setSimpleName(newName);
        
        // Now use a processor to rename all references
        SpoonVariableRenamer renamer = new SpoonVariableRenamer(targetVariable, newName);
        launcher.addProcessor(renamer);
        launcher.process();
        
        System.err.println("Info: Renamed " + renamer.getRenameCount() + " references");
        
        // Print the modified content of just the target file
        printModifiedFile(model, targetFile);
    }
    
    private static void renameMethod(CtModel model, String filePath, int lineNumber,
                                   String oldName, String newName, Launcher launcher) throws Exception {
        // Find the specific method declaration
        CtMethod<?> targetMethod = null;
        File targetFile = new File(filePath).getCanonicalFile();
        
        for (CtMethod<?> method : model.getElements(new TypeFilter<>(CtMethod.class))) {
            if (method.getSimpleName().equals(oldName) &&
                method.getPosition().isValidPosition() &&
                method.getPosition().getLine() == lineNumber) {
                
                // Check if it's in the target file
                File methodFile = method.getPosition().getFile();
                if (methodFile != null && methodFile.getCanonicalFile().equals(targetFile)) {
                    targetMethod = method;
                    System.err.println("Info: Found method '" + oldName + "' at line " + lineNumber);
                    break;
                }
            }
        }
        
        if (targetMethod == null) {
            System.err.println("Error: Could not find method '" + oldName + "' at line " + lineNumber);
            printOriginalFile(filePath);
            System.exit(0);
        }
        
        // Use Spoon's refactoring - set the new name directly
        System.err.println("Info: Renaming method and all its references...");
        targetMethod.setSimpleName(newName);
        
        // Print the modified content
        printModifiedFile(model, targetFile);
    }
    
    private static void printOriginalFile(String filePath) throws Exception {
        // Read and print the original file content
        java.nio.file.Path path = java.nio.file.Paths.get(filePath);
        String content = new String(java.nio.file.Files.readAllBytes(path));
        System.out.print(content);
    }
    
    private static void printModifiedFile(CtModel model, File targetFile) throws Exception {
        // Find the compilation unit for the target file and print it
        boolean found = false;
        
        // Get all types (classes) in the model and find the one from our file
        for (spoon.reflect.declaration.CtType<?> type : model.getAllTypes()) {
            if (type.getPosition().isValidPosition() && 
                type.getPosition().getFile() != null &&
                type.getPosition().getFile().getCanonicalFile().equals(targetFile)) {
                
                // Get the compilation unit from the type
                spoon.reflect.cu.CompilationUnit cu = type.getFactory().CompilationUnit().getOrCreate(type);
                System.out.print(cu.prettyprint());
                found = true;
                break;
            }
        }
        
        if (!found) {
            System.err.println("Warning: Could not find compilation unit for file: " + targetFile);
            printOriginalFile(targetFile.getAbsolutePath());
        }
    }
}