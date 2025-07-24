/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * SimpleJavaRefactor.java - Basic Java refactoring without external dependencies
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-08
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class SimpleJavaRefactor {
    
    private static class Scope {
        String type; // "class", "method", "block"
        String name;
        int startLine;
        int endLine;
        int braceLevel;
        Scope parent;
        List<Scope> children = new ArrayList<>();
        
        boolean contains(int line) {
            return line >= startLine && line <= endLine;
        }
    }
    
    public static void main(String[] args) throws Exception {
        if (args.length < 4) {
            System.err.println("Usage: java SimpleJavaRefactor <file_path> <line_number> <old_name> <new_name>");
            System.exit(1);
        }
        
        String filePath = args[0];
        int targetLine = Integer.parseInt(args[1]);
        String oldName = args[2];
        String newName = args[3];
        
        // Read file content
        List<String> lines = Files.readAllLines(Paths.get(filePath));
        
        // Build scope tree
        Scope rootScope = buildScopeTree(lines);
        
        // Find the scope containing the declaration
        Scope declarationScope = findDeclarationScope(lines, targetLine, oldName, rootScope);
        
        if (declarationScope == null) {
            System.err.println("Could not find declaration of '" + oldName + "' at line " + targetLine);
            // Print original content
            for (String line : lines) {
                System.out.println(line);
            }
            System.exit(0);
        }
        
        // Perform renaming within the scope
        List<String> modifiedLines = performScopeAwareRename(lines, oldName, newName, declarationScope);
        
        // Print modified content
        for (String line : modifiedLines) {
            System.out.println(line);
        }
    }
    
    private static Scope buildScopeTree(List<String> lines) {
        Scope root = new Scope();
        root.type = "file";
        root.startLine = 1;
        root.endLine = lines.size();
        root.braceLevel = 0;
        
        Stack<Scope> scopeStack = new Stack<>();
        scopeStack.push(root);
        
        int braceLevel = 0;
        boolean inString = false;
        boolean inChar = false;
        boolean inComment = false;
        boolean inMultilineComment = false;
        
        for (int i = 0; i < lines.size(); i++) {
            String line = lines.get(i);
            int lineNum = i + 1;
            
            // Skip empty lines
            if (line.trim().isEmpty()) continue;
            
            // Handle comments
            if (line.trim().startsWith("//")) continue;
            
            // Parse character by character
            for (int j = 0; j < line.length(); j++) {
                char ch = line.charAt(j);
                char prevCh = j > 0 ? line.charAt(j - 1) : '\0';
                char nextCh = j < line.length() - 1 ? line.charAt(j + 1) : '\0';
                
                // Handle multiline comments
                if (!inString && !inChar) {
                    if (ch == '/' && nextCh == '*') {
                        inMultilineComment = true;
                        j++; // Skip next char
                        continue;
                    }
                    if (inMultilineComment && ch == '*' && nextCh == '/') {
                        inMultilineComment = false;
                        j++; // Skip next char
                        continue;
                    }
                }
                
                if (inMultilineComment) continue;
                
                // Handle strings and chars
                if (!inString && ch == '\'' && prevCh != '\\') {
                    inChar = !inChar;
                } else if (!inChar && ch == '"' && prevCh != '\\') {
                    inString = !inString;
                }
                
                // Count braces outside strings/chars
                if (!inString && !inChar) {
                    if (ch == '{') {
                        braceLevel++;
                        
                        // Check if this starts a new scope (class or method)
                        String trimmedLine = line.substring(0, j).trim();
                        Scope newScope = detectScope(trimmedLine, lineNum);
                        
                        if (newScope != null) {
                            newScope.braceLevel = braceLevel;
                            newScope.parent = scopeStack.peek();
                            scopeStack.peek().children.add(newScope);
                            scopeStack.push(newScope);
                        }
                    } else if (ch == '}') {
                        braceLevel--;
                        
                        // Close scope if needed
                        if (!scopeStack.isEmpty() && scopeStack.peek().braceLevel > braceLevel) {
                            Scope closedScope = scopeStack.pop();
                            closedScope.endLine = lineNum;
                        }
                    }
                }
            }
        }
        
        // Close remaining scopes
        while (scopeStack.size() > 1) {
            Scope scope = scopeStack.pop();
            scope.endLine = lines.size();
        }
        
        return root;
    }
    
    private static Scope detectScope(String line, int lineNum) {
        // Detect class declaration
        Pattern classPattern = Pattern.compile("\\b(public|private|protected)?\\s*(static)?\\s*class\\s+(\\w+)");
        Matcher classMatcher = classPattern.matcher(line);
        if (classMatcher.find()) {
            Scope scope = new Scope();
            scope.type = "class";
            scope.name = classMatcher.group(3);
            scope.startLine = lineNum;
            return scope;
        }
        
        // Detect method declaration
        Pattern methodPattern = Pattern.compile("\\b(public|private|protected)?\\s*(static)?\\s*(\\w+\\s+)?(\\w+)\\s*\\(");
        Matcher methodMatcher = methodPattern.matcher(line);
        if (methodMatcher.find() && !line.contains("new ") && !line.contains("if ") && 
            !line.contains("while ") && !line.contains("for ") && !line.contains("switch ")) {
            Scope scope = new Scope();
            scope.type = "method";
            scope.name = methodMatcher.group(4);
            scope.startLine = lineNum;
            return scope;
        }
        
        return null;
    }
    
    private static Scope findDeclarationScope(List<String> lines, int targetLine, String varName, Scope root) {
        if (targetLine < 1 || targetLine > lines.size()) return null;
        
        String line = lines.get(targetLine - 1);
        
        // Check if this line contains a declaration of the variable
        if (!line.contains(varName)) return null;
        
        // Simple patterns for variable declarations
        String[] patterns = {
            "\\b(\\w+)\\s+" + Pattern.quote(varName) + "\\s*[=;,)]",  // Type varName
            "\\b(\\w+)\\s+" + Pattern.quote(varName) + "\\s*\\[",      // Type varName[]
            "\\(" + ".*\\b(\\w+)\\s+" + Pattern.quote(varName) + "\\b", // Method parameter
            "\\bfor\\s*\\(.*\\b(\\w+)\\s+" + Pattern.quote(varName) + "\\b" // For loop variable
        };
        
        boolean isDeclaration = false;
        for (String pattern : patterns) {
            if (Pattern.compile(pattern).matcher(line).find()) {
                isDeclaration = true;
                break;
            }
        }
        
        if (!isDeclaration) return null;
        
        // Find the innermost scope containing this line
        return findInnermostScope(root, targetLine);
    }
    
    private static Scope findInnermostScope(Scope scope, int line) {
        if (!scope.contains(line)) return null;
        
        // Check children first
        for (Scope child : scope.children) {
            Scope result = findInnermostScope(child, line);
            if (result != null) return result;
        }
        
        // If no child contains the line, this scope is the innermost
        return scope;
    }
    
    private static List<String> performScopeAwareRename(List<String> lines, String oldName, 
                                                       String newName, Scope scope) {
        List<String> result = new ArrayList<>();
        Pattern varPattern = Pattern.compile("\\b" + Pattern.quote(oldName) + "\\b");
        
        for (int i = 0; i < lines.size(); i++) {
            int lineNum = i + 1;
            String line = lines.get(i);
            
            // Only rename within the scope
            if (scope.contains(lineNum)) {
                // Don't rename in comments or strings
                StringBuilder modifiedLine = new StringBuilder();
                boolean inString = false;
                boolean inChar = false;
                boolean inComment = false;
                
                for (int j = 0; j < line.length(); j++) {
                    char ch = line.charAt(j);
                    char prevCh = j > 0 ? line.charAt(j - 1) : '\0';
                    char nextCh = j < line.length() - 1 ? line.charAt(j + 1) : '\0';
                    
                    // Handle comments
                    if (!inString && !inChar && ch == '/' && nextCh == '/') {
                        // Rest of line is comment
                        modifiedLine.append(line.substring(j));
                        break;
                    }
                    
                    // Handle strings and chars
                    if (!inComment) {
                        if (!inString && ch == '\'' && prevCh != '\\') {
                            inChar = !inChar;
                        } else if (!inChar && ch == '"' && prevCh != '\\') {
                            inString = !inString;
                        }
                    }
                    
                    // Check if we're at the start of the old name
                    if (!inString && !inChar && !inComment) {
                        String remaining = line.substring(j);
                        Matcher matcher = varPattern.matcher(remaining);
                        if (matcher.lookingAt()) {
                            // Found the variable name, replace it
                            modifiedLine.append(newName);
                            j += oldName.length() - 1; // Skip the old name
                            continue;
                        }
                    }
                    
                    modifiedLine.append(ch);
                }
                
                result.add(modifiedLine.toString());
            } else {
                result.add(line);
            }
        }
        
        return result;
    }
}