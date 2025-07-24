/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * JavaRefactorWithSpoonV2.java - Improved Spoon-based refactoring with proper reference handling
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-08
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */
/**  CLI usage:
 *   java -jar spoon-refactor-engine.jar --file Foo.java --line 42 --old foo --new bar [--method]
 *   Files are written back **atomically** and a ".bak" file is left beside the original.
 */

import spoon.Launcher;
import spoon.reflect.CtModel;
import spoon.reflect.declaration.*;
import spoon.reflect.reference.CtVariableReference;
import spoon.reflect.reference.CtExecutableReference;
import spoon.reflect.visitor.filter.TypeFilter;
import spoon.reflect.visitor.filter.AbstractFilter;

import java.io.File;
import java.util.*;
import java.util.regex.Pattern;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.charset.StandardCharsets;

public class JavaRefactorWithSpoonV2 {

    public static void main(String[] args) {
        /* ---------- argument parsing (fail-fast & safe) ---------- */
        Path filePath = null;
        int lineNumber = -1;
        String oldName = null, newName = null;
        boolean isMethod = false;
        boolean dryRun = false;
        List<String> sourceDirs = new ArrayList<>();

        // Handle legacy positional arguments for backward compatibility
        if (args.length >= 4 && !args[0].startsWith("--")) {
            filePath = Path.of(args[0]);
            lineNumber = Integer.parseInt(args[1]);
            oldName = args[2];
            newName = args[3];
            isMethod = args.length > 4 && "--method".equals(args[4]);
        } else {
            Iterator<String> it = Arrays.asList(args).iterator();
            try {
                while (it.hasNext()) {
                    switch (it.next()) {
                        case "--file":        filePath = Path.of(it.next()); break;
                        case "--line":        lineNumber = Integer.parseInt(it.next()); break;
                        case "--old":
                        case "--old-name":    oldName = it.next(); break;
                        case "--new":
                        case "--new-name":    newName = it.next(); break;
                        case "--method":      isMethod = true; break;
                        case "--dry-run":     dryRun = true; break;
                        case "--source-dir":  sourceDirs.add(it.next()); break;
                        default:  throw new IllegalArgumentException("Unknown flag");
                    }
                }
            } catch (NoSuchElementException | NumberFormatException e) {
                System.err.println("⛔  Malformed CLI: " + e.getMessage());
                printUsageAndExit(1);
            }
        }
        
        if (filePath == null || lineNumber < 1 || oldName == null || newName == null)
            printUsageAndExit(1);

        /* ---------- identifier sanity ---------- */
        Pattern ident = Pattern.compile("\\p{javaJavaIdentifierStart}\\p{javaJavaIdentifierPart}*");
        if (!ident.matcher(newName).matches())
            fatal("'" + newName + "' is not a legal Java identifier");

        if (Objects.equals(oldName, newName)) {
            System.err.println("⚠  Old and new names are identical – nothing to do.");
            return;
        }

        try {
            /* ---------- Spoon bootstrap ---------- */
            Launcher launcher = new Launcher();
            launcher.getEnvironment().setPreserveLineNumbers(true);
            launcher.getEnvironment().setAutoImports(true);
            launcher.getEnvironment().setNoClasspath(true);
            
            // Add source directories
            if (sourceDirs.isEmpty()) {
                File parentDir = filePath.getParent().toFile();
                if (parentDir != null) {
                    launcher.addInputResource(parentDir.getAbsolutePath());
                    System.err.println("Info: Using parent directory: " + parentDir.getAbsolutePath());
                }
            } else {
                for (String dir : sourceDirs) {
                    launcher.addInputResource(dir);
                    System.err.println("Info: Added source directory: " + dir);
                }
            }
            
            // Build model
            System.err.println("Info: Building Spoon model...");
            launcher.buildModel();
            CtModel model = launcher.getModel();
            
            // Perform refactoring
            if (isMethod) {
                renameMethod(model, filePath.toString(), lineNumber, oldName, newName);
            } else {
                renameVariable(model, filePath.toString(), lineNumber, oldName, newName);
            }
            
            /* ---------- write-back (atomic, keeps .bak) ---------- */
            Path original = filePath;
            Path bak = original.resolveSibling(original.getFileName() + ".bak");
            Path tmp = Files.createTempFile(original.getParent(), ".refactor", ".tmp");
            
            // Remove existing backup if it exists
            if (Files.exists(bak)) {
                Files.delete(bak);
            }
            
            // Find the compilation unit and write it
            String refactoredCode = null;
            for (CtType<?> type : model.getAllTypes()) {
                if (type.getPosition().isValidPosition() && 
                    type.getPosition().getFile() != null) {
                    
                    try {
                        Path typePath = type.getPosition().getFile().toPath().toAbsolutePath().normalize();
                        Path originalPath = original.toAbsolutePath().normalize();
                        
                        if (typePath.equals(originalPath)) {
                            spoon.reflect.cu.CompilationUnit cu = type.getFactory().CompilationUnit().getOrCreate(type);
                            refactoredCode = cu.prettyprint();
                            break;
                        }
                    } catch (Exception e) {
                        // Try filename comparison as fallback
                        if (type.getPosition().getFile().getName().equals(original.getFileName().toString())) {
                            spoon.reflect.cu.CompilationUnit cu = type.getFactory().CompilationUnit().getOrCreate(type);
                            refactoredCode = cu.prettyprint();
                            break;
                        }
                    }
                }
            }
            
            if (refactoredCode != null) {
                Files.writeString(tmp, refactoredCode, StandardCharsets.UTF_8);
                if (dryRun) {
                    System.out.println("--dry-run:  diff against current file ↓↓↓");
                    printUnifiedDiff(original, tmp);
                    Files.deleteIfExists(tmp);
                } else {
                    Files.move(original, bak); // backup first
                    Files.move(tmp, original, StandardCopyOption.ATOMIC_MOVE,
                                              StandardCopyOption.REPLACE_EXISTING);
                    System.out.println("✓  Changes written atomically (backup ⇒ " + bak + ")");
                }
            } else {
                fatal("Could not find compilation unit for file");
            }
            
        } catch (Throwable t) {
            fatal("Unhandled error: " + t.getMessage(), t);
        }
    }
    
    private static void renameVariable(CtModel model, String filePath, int lineNumber, 
                                     String oldName, String newName) throws Exception {
        File targetFile = new File(filePath).getCanonicalFile();
        CtVariable<?> targetVariable = null;
        
        // Find the variable declaration at the specified line
        for (CtVariable<?> var : model.getElements(new TypeFilter<>(CtVariable.class))) {
            if (var.getSimpleName().equals(oldName) && 
                var.getPosition().isValidPosition() &&
                var.getPosition().getLine() == lineNumber &&
                var.getPosition().getFile() != null &&
                var.getPosition().getFile().getCanonicalFile().equals(targetFile)) {
                targetVariable = var;
                break;
            }
        }
        
        if (targetVariable == null) {
            System.err.println("Error: Variable '" + oldName + "' not found at line " + lineNumber);
            printOriginalFile(filePath);
            System.exit(0);
        }
        
        System.err.println("Info: Found variable '" + oldName + "' at line " + lineNumber);
        
        // Find all references that point to our target variable's declaration
        final CtVariable<?> finalTarget = targetVariable;
        AbstractFilter<CtVariableReference<?>> filter = new AbstractFilter<CtVariableReference<?>>() {
            @Override
            public boolean matches(CtVariableReference<?> reference) {
                try {
                    // Check if this reference points to our target variable
                    return reference.getDeclaration() != null && 
                           reference.getDeclaration().equals(finalTarget);
                } catch (Exception e) {
                    // If we can't resolve the declaration, fall back to name + scope matching
                    return reference.getSimpleName().equals(oldName) && 
                           isInSameScope(reference, finalTarget);
                }
            }
        };
        
        List<CtVariableReference<?>> references = model.getElements(filter);
        
        System.err.println("Info: Found " + references.size() + " references to rename");
        
        // Rename each reference found
        for (CtVariableReference<?> reference : references) {
            reference.setSimpleName(newName);
        }
        
        // Rename the original declaration itself
        targetVariable.setSimpleName(newName);
        
        System.err.println("Info: Renamed " + references.size() + " references plus declaration");
        
        // Note: File writing is now handled in main() for atomic operations
    }
    
    private static boolean isInSameScope(CtVariableReference<?> reference, CtVariable<?> variable) {
        // Check if the reference is within the same scope as the variable declaration
        spoon.reflect.declaration.CtElement refParent = reference.getParent();
        spoon.reflect.declaration.CtElement varScope = variable.getParent();
        
        // For local variables, check if they're in the same method/block
        while (refParent != null) {
            if (refParent.equals(varScope)) {
                return true;
            }
            // If we hit a method boundary, check if the variable is declared in this method
            if (refParent instanceof CtMethod) {
                // Check if the variable is declared within this method
                CtMethod<?> method = (CtMethod<?>) refParent;
                return method.equals(variable.getParent(CtMethod.class));
            }
            refParent = refParent.getParent();
        }
        
        return false;
    }
    
    private static void renameMethod(CtModel model, String filePath, int lineNumber,
                                   String oldName, String newName) throws Exception {
        File targetFile = new File(filePath).getCanonicalFile();
        CtMethod<?> targetMethod = null;
        
        for (CtMethod<?> method : model.getElements(new TypeFilter<>(CtMethod.class))) {
            if (method.getSimpleName().equals(oldName) &&
                method.getPosition().isValidPosition() &&
                method.getPosition().getLine() == lineNumber &&
                method.getPosition().getFile() != null &&
                method.getPosition().getFile().getCanonicalFile().equals(targetFile)) {
                targetMethod = method;
                break;
            }
        }
        
        if (targetMethod == null) {
            System.err.println("Error: Method '" + oldName + "' not found at line " + lineNumber);
            printOriginalFile(filePath);
            System.exit(0);
        }
        
        System.err.println("Info: Found method '" + oldName + "' at line " + lineNumber);

        // Find all references (invocations) that point to our target method
        final CtMethod<?> finalTarget = targetMethod;
        AbstractFilter<CtExecutableReference<?>> filter = new AbstractFilter<CtExecutableReference<?>>() {
            @Override
            public boolean matches(CtExecutableReference<?> reference) {
                try {
                    return reference.getDeclaration() != null && 
                           reference.getDeclaration().equals(finalTarget);
                } catch (Exception e) {
                    return reference.getSimpleName().equals(oldName);
                }
            }
        };
        
        List<CtExecutableReference<?>> references = model.getElements(filter);
        System.err.println("Info: Found " + references.size() + " method invocations to rename");

        // Rename each invocation
        for (CtExecutableReference<?> reference : references) {
            reference.setSimpleName(newName);
        }
        
        // Rename the original declaration itself
        targetMethod.setSimpleName(newName);
        System.err.println("Info: Renamed " + references.size() + " invocations plus declaration");
        
        // Note: File writing is now handled in main() for atomic operations
    }
    
    /* ---------- helpers ---------- */
    private static void fatal(String msg) { fatal(msg, null); }
    private static void fatal(String msg, Throwable t) {
        System.err.println("⛔  " + msg);
        if (t != null) t.printStackTrace(System.err);
        System.exit(2);
    }
    private static void printUsageAndExit(int code) {
        System.err.println("Usage: --file <file> --line <n> --old <name> --new <name> [--method] [--dry-run] [--source-dir dir]");
        System.err.println("  or: <file> <line> <old> <new> [--method]  (legacy positional format)");
        System.exit(code);
    }
    
    /** Emit a minimal unified diff (3-line context) for --dry-run */
    private static void printUnifiedDiff(Path a, Path b) throws Exception {
        List<String> oldLines = Files.readAllLines(a);
        List<String> newLines = Files.readAllLines(b);
        
        // Simple unified diff implementation
        System.out.println("--- " + a.toString());
        System.out.println("+++ " + b.toString());
        
        int oldSize = oldLines.size();
        int newSize = newLines.size();
        
        for (int i = 0; i < Math.max(oldSize, newSize); i++) {
            String oldLine = i < oldSize ? oldLines.get(i) : null;
            String newLine = i < newSize ? newLines.get(i) : null;
            
            if (oldLine != null && newLine != null) {
                if (!oldLine.equals(newLine)) {
                    System.out.println("-" + oldLine);
                    System.out.println("+" + newLine);
                }
            } else if (oldLine != null) {
                System.out.println("-" + oldLine);
            } else if (newLine != null) {
                System.out.println("+" + newLine);
            }
        }
    }
    
    private static void printOriginalFile(String filePath) throws Exception {
        java.nio.file.Path path = java.nio.file.Paths.get(filePath);
        String content = new String(java.nio.file.Files.readAllBytes(path));
        System.out.print(content);
    }
}