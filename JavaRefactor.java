/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * JavaRefactor.java - Scope-aware Java refactoring engine
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-08
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.VariableDeclarator;
import com.github.javaparser.ast.body.Parameter;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.expr.NameExpr;
import com.github.javaparser.ast.expr.FieldAccessExpr;
import com.github.javaparser.ast.expr.SimpleName;
import com.github.javaparser.resolution.declarations.ResolvedValueDeclaration;
import com.github.javaparser.resolution.declarations.ResolvedMethodDeclaration;
import com.github.javaparser.symbolsolver.JavaSymbolSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.CombinedTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.ReflectionTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.JavaParserTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.JarTypeSolver;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class JavaRefactor {

    public static void main(String[] args) throws Exception {
        // --- Enhanced Argument Parsing ---
        String filePath = null;
        Integer lineNumber = null;
        String oldName = null;
        String newName = null;
        boolean isMethod = false;
        List<String> sourceDirs = new ArrayList<>();
        List<String> jarPaths = new ArrayList<>();

        // Parse arguments - support both old and new format for backward compatibility
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
            System.err.println("Usage: java -jar java-refactor-engine.jar <file_path> <line_number> <old_name> <new_name> [--method]");
            System.err.println("   OR: java -jar java-refactor-engine.jar --file <path> --line <num> --old-name <name> --new-name <name> [--method] [--source-dir <path>]* [--jar <path>]*");
            System.err.println("\nOptions:");
            System.err.println("  --method        Indicates renaming a method instead of a variable");
            System.err.println("  --source-dir    Add a source directory for better symbol resolution (can be specified multiple times)");
            System.err.println("  --jar           Add a JAR file for dependency resolution (can be specified multiple times)");
            System.exit(1);
        }

        // --- Enhanced Type Solver Configuration ---
        CombinedTypeSolver typeSolver = new CombinedTypeSolver();
        
        // 1. Solver for the Java standard library
        typeSolver.add(new ReflectionTypeSolver());
        
        // 2. Solvers for the project's own source code
        if (sourceDirs.isEmpty()) {
            // If no source dirs specified, use the file's parent directory as a fallback
            File sourceFile = new File(filePath);
            File projectDir = sourceFile.getParentFile();
            if (projectDir != null && projectDir.exists()) {
                typeSolver.add(new JavaParserTypeSolver(projectDir));
                System.err.println("Info: Using parent directory as source path: " + projectDir.getAbsolutePath());
            }
        } else {
            // Use specified source directories for better accuracy
            for (String sourceDir : sourceDirs) {
                File dir = new File(sourceDir);
                if (dir.exists() && dir.isDirectory()) {
                    typeSolver.add(new JavaParserTypeSolver(dir));
                    System.err.println("Info: Added source directory: " + dir.getAbsolutePath());
                } else {
                    System.err.println("Warning: Source directory not found: " + sourceDir);
                }
            }
        }
        
        // 3. Solvers for external libraries (JARs)
        for (String jarPath : jarPaths) {
            File jarFile = new File(jarPath);
            if (jarFile.exists() && jarFile.isFile()) {
                try {
                    typeSolver.add(new JarTypeSolver(jarFile));
                    System.err.println("Info: Added JAR: " + jarFile.getAbsolutePath());
                } catch (Exception e) {
                    System.err.println("Warning: Could not add JAR: " + jarPath + " - " + e.getMessage());
                }
            } else {
                System.err.println("Warning: JAR file not found: " + jarPath);
            }
        }
        
        JavaSymbolSolver symbolSolver = new JavaSymbolSolver(typeSolver);
        StaticJavaParser.getConfiguration().setSymbolResolver(symbolSolver);

        // Parse the file
        File sourceFile = new File(filePath);
        CompilationUnit cu = StaticJavaParser.parse(sourceFile);

        int replacementCount;
        if (isMethod) {
            replacementCount = renameMethod(cu, lineNumber, oldName, newName, filePath);
        } else {
            replacementCount = renameVariable(cu, lineNumber, oldName, newName, filePath);
        }

        // Print the modified code. JavaParser preserves most original formatting.
        System.err.println("Info: Made " + replacementCount + " replacements");
        System.out.print(cu.toString());
    }

    private static int renameVariable(CompilationUnit cu, int lineNumber, String oldName, 
                                     String newName, String filePath) throws Exception {
        // 1. Find the specific declaration of the variable we want to rename.
        final ResolvedValueDeclaration[] targetDeclaration = {null};
        
        // Check for variable declarations
        cu.walk(VariableDeclarator.class, vd -> {
            if (vd.getNameAsString().equals(oldName) && 
                vd.getBegin().isPresent() && vd.getBegin().get().line == lineNumber) {
                try {
                    targetDeclaration[0] = vd.resolve();
                } catch (Exception e) {
                    // Could not resolve symbol, likely a syntax issue or incomplete classpath.
                    System.err.println("Warning: Could not resolve variable declarator: " + e.getMessage());
                }
            }
        });

        // Also check for method parameters
        if (targetDeclaration[0] == null) {
            cu.walk(Parameter.class, param -> {
                if (param.getNameAsString().equals(oldName) && 
                    param.getBegin().isPresent() && param.getBegin().get().line == lineNumber) {
                    try {
                        targetDeclaration[0] = param.resolve();
                    } catch (Exception e) {
                        System.err.println("Warning: Could not resolve parameter: " + e.getMessage());
                    }
                }
            });
        }
        
        // If still not found, try field declarations (for renaming instance variables)
        if (targetDeclaration[0] == null) {
            cu.walk(com.github.javaparser.ast.body.FieldDeclaration.class, fd -> {
                fd.getVariables().forEach(var -> {
                    if (var.getNameAsString().equals(oldName) && 
                        var.getBegin().isPresent() && var.getBegin().get().line == lineNumber) {
                        try {
                            targetDeclaration[0] = var.resolve();
                        } catch (Exception e) {
                            System.err.println("Warning: Could not resolve field: " + e.getMessage());
                        }
                    }
                });
            });
        }

        if (targetDeclaration[0] == null) {
            System.err.println("Error: Could not resolve variable '" + oldName + "' at line " + lineNumber);
            System.err.println("Debug: Searched for variable declarations, parameters, and fields");
            // Print original content and exit so Python script can handle it
            System.out.print(Files.readString(Paths.get(filePath)));
            System.exit(0);
        }
        
        System.err.println("Info: Found declaration of '" + oldName + "' at line " + lineNumber);
        
        final int[] replacementCount = {0};

        // 2. Rename all references to that specific variable declaration.
        cu.walk(NameExpr.class, nameExpr -> {
            if (nameExpr.getNameAsString().equals(oldName)) {
                try {
                    if (targetDeclaration[0].equals(nameExpr.resolve())) {
                        nameExpr.setName(newName);
                        replacementCount[0]++;
                    }
                } catch (Exception e) {
                    // Cannot resolve this expression, skip it.
                }
            }
        });
        
        // Handle field access expressions (e.g., this.variable)
        cu.walk(FieldAccessExpr.class, fieldAccess -> {
            if (fieldAccess.getNameAsString().equals(oldName)) {
                try {
                    // With proper type solving, we can accurately resolve field accesses
                    if (targetDeclaration[0].equals(fieldAccess.resolve())) {
                        fieldAccess.setName(newName);
                    }
                } catch (Exception e) {
                    // Cannot resolve this field access, skip it
                }
            }
        });
        
        // 3. Rename the declaration itself
        cu.walk(VariableDeclarator.class, vd -> {
            try {
                if (targetDeclaration[0].equals(vd.resolve())) {
                    vd.setName(newName);
                }
            } catch (Exception e) {
                // Cannot resolve this declarator, skip it.
            }
        });
        
        // Also rename parameter declarations
        cu.walk(Parameter.class, param -> {
            try {
                if (targetDeclaration[0].equals(param.resolve())) {
                    param.setName(newName);
                }
            } catch (Exception e) {
                // Cannot resolve this parameter, skip it.
            }
        });
        
        return replacementCount[0];
    }

    private static int renameMethod(CompilationUnit cu, int lineNumber, String oldName, 
                                   String newName, String filePath) throws Exception {
        // Find the specific method declaration
        final ResolvedMethodDeclaration[] targetMethod = {null};
        
        cu.walk(MethodDeclaration.class, md -> {
            if (md.getNameAsString().equals(oldName) && 
                md.getBegin().isPresent() && md.getBegin().get().line == lineNumber) {
                try {
                    targetMethod[0] = md.resolve();
                } catch (Exception e) {
                    System.err.println("Warning: Could not resolve method: " + e.getMessage());
                }
            }
        });

        if (targetMethod[0] == null) {
            System.err.println("Error: Could not resolve method '" + oldName + "' at line " + lineNumber);
            System.out.print(Files.readString(Paths.get(filePath)));
            System.exit(0);
        }

        // Rename method declaration
        cu.walk(MethodDeclaration.class, md -> {
            try {
                if (targetMethod[0].equals(md.resolve())) {
                    md.setName(newName);
                }
            } catch (Exception e) {
                // Skip if cannot resolve
            }
        });

        // Rename method calls
        cu.walk(com.github.javaparser.ast.expr.MethodCallExpr.class, methodCall -> {
            if (methodCall.getNameAsString().equals(oldName)) {
                try {
                    if (targetMethod[0].equals(methodCall.resolve())) {
                        methodCall.setName(newName);
                    }
                } catch (Exception e) {
                    // Cannot resolve this call, skip it.
                }
            }
        });
        
        return 0; // TODO: Add proper counting for method renames
    }
}