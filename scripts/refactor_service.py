#!/usr/bin/env python3
import ast
import sys
import os

def refactor_file(filepath):
    """
    Reads a Python file, finds `try...except` blocks that call `self.supabase_client`,
    and replaces them with `self.execute_query` pattern using BaseRepository.
    """
    with open(filepath, 'r') as f:
        source_code = f.read()

    lines = source_code.splitlines()
    tree = ast.parse(source_code)
    
    # Extract structural Try blocks that talk to Supabase
    try_nodes = []
    
    class SupabaseTryVisitor(ast.NodeVisitor):
        def visit_Try(self, node):
            # Check if body contains supabase_client
            has_supabase = False
            for stmt in node.body:
                # Poor man's AST check for Supabase query
                if isinstance(stmt, ast.Assign) and hasattr(stmt, 'value') and isinstance(stmt.value, ast.Call):
                    node_str = ast.unparse(stmt.value)
                    if 'self.supabase_client.table' in node_str or 'self.supabase_client.rpc' in node_str:
                        has_supabase = True
                        stmt.supabase_call = stmt.value
                        break
                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                     node_str = ast.unparse(stmt.value)
                     if 'self.supabase_client.table' in node_str or 'self.supabase_client.rpc' in node_str:
                        has_supabase = True
                        stmt.supabase_call = stmt.value
                        break
            
            if has_supabase:
                try_nodes.append(node)
            self.generic_visit(node)

    visitor = SupabaseTryVisitor()
    visitor.visit(tree)

    if not try_nodes:
        print(f"No Supabase try...except blocks found in {filepath} to refactor.")
        return False

    # Perform replacements from bottom to top to preserve line offsets
    try_nodes.sort(key=lambda n: n.lineno, reverse=True)
    
    modified = False
    for node in try_nodes:
        # Step 1: Find the actual query node text
        query_node = None
        for stmt in node.body:
            if hasattr(stmt, 'supabase_call'):
                query_node = stmt.supabase_call
                break
                
        if not query_node:
            continue
            
        # Get exact lines belonging to the query statement for accuracy instead of unparse which rips out newlines
        query_lines = lines[query_node.lineno - 1 : query_node.end_lineno]
        # Re-indent query lines relative to closure
        query_code = "\n".join(query_lines).strip()
        
        # Determine error context by looking at the except block if available
        error_context = "Database operation failed"
        for handler in node.handlers:
            for stmt in handler.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    if hasattr(stmt.value.func, 'attr') and stmt.value.func.attr == 'error':
                        # Example: logger.error(f"Failed to fetch task: {e}") 
                        if stmt.value.args and isinstance(stmt.value.args[0], ast.JoinedStr):
                            # Approximate string
                            error_context = "DB operation logged error"
                        elif stmt.value.args and isinstance(stmt.value.args[0], ast.Constant):
                            error_context = stmt.value.args[0].value

        # Calculate leading indentation
        leading_ws = len(lines[node.lineno - 1]) - len(lines[node.lineno - 1].lstrip())
        indent = " " * leading_ws
        inner_indent = indent + "    "
        inner_inner_indent = inner_indent + "    "

        # Construct replacement string
        lines_to_insert = [
            f"{indent}def _query():",
            f"{inner_indent}return (",
            f"{inner_inner_indent}{query_code}",
            f"{inner_indent})",
            f"",
            f"{indent}success, result = self.execute_query(",
            f"{inner_indent}query_func=_query,",
            f"{inner_indent}error_context=\"{error_context}\"",
            f"{indent})",
            f"{indent}if success:",
            f"{inner_indent}# TODO: Extract properties via 'result[\"data\"]' as per original logic",
            f"{inner_indent}return True, {{\"data\": result[\"data\"]}}",
            f"{indent}return False, result",
        ]

        start_idx = node.lineno - 1
        end_idx = node.end_lineno
        lines[start_idx:end_idx] = lines_to_insert
        modified = True
        print(f"Refactored try block at line {node.lineno} in {filepath}")

    if modified:
        with open(filepath, 'w') as f:
            f.write("\n".join(lines) + "\n")
        print(f"Successfully wrote refactored AST changes to {filepath}.")
        print(f"Remember to adjust the BaseRepository inheritance and exact 'return' logic!")
        return True
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python refactor_service.py <path_to_python_file>")
        sys.exit(1)
        
    for path in sys.argv[1:]:
        if os.path.exists(path):
            refactor_file(path)
        else:
            print(f"File not found: {path}")
