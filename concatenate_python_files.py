#!/usr/bin/env python3

import os
import sys
import ast
import argparse
from collections import deque
from typing import List, Set

def is_local_module(module_path: str, search_folder: str) -> bool:
    """Check if a resolved module path is within the specified search folder."""
    abs_search_folder = os.path.realpath(search_folder)
    abs_module_path = os.path.realpath(module_path)
    return os.path.commonpath([abs_search_folder, abs_module_path]) == abs_search_folder

def resolve_import_path(module_name: str, current_file_dir: str, search_folder: str, level: int = 0) -> str or None:
    """Resolve an import name into a potential file or package path."""
    base_path = ""
    if level > 0:
        base_path = current_file_dir
        for _ in range(level - 1):
            base_path = os.path.dirname(base_path)
    else:
        base_path = search_folder

    rel_path_parts = module_name.split('.')
    
    potential_path_py = os.path.join(base_path, *rel_path_parts) + '.py'
    if os.path.isfile(potential_path_py) and is_local_module(potential_path_py, search_folder):
        return os.path.realpath(potential_path_py)
    
    potential_path_pkg = os.path.join(base_path, *rel_path_parts, '__init__.py')
    if os.path.isfile(potential_path_pkg) and is_local_module(potential_path_pkg, search_folder):
        return os.path.realpath(potential_path_pkg)
        
    return None

class ImportVisitor(ast.NodeVisitor):
    """AST visitor to find all local import statements."""
    def __init__(self, current_file_path: str, search_folder: str):
        self.current_file_dir = os.path.dirname(current_file_path)
        self.search_folder = search_folder
        self.dependencies = set()

    def visit_Import(self, node):
        for alias in node.names:
            module_path = resolve_import_path(alias.name, self.current_file_dir, self.search_folder)
            if module_path:
                self.dependencies.add(module_path)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # [THE FIX] A much simpler and more robust approach.
        if not node.module:
            # Handles relative imports like `from . import foo`
            # Here, the module is the package containing the current file.
            module_base_name = ''
        else:
            module_base_name = node.module

        # For each name in the import (e.g., 'speaker_mgr' in 'from worker.module import speaker_mgr')
        for alias in node.names:
            # Try to resolve the most specific path first.
            # e.g., 'worker.module.speaker_mgr'
            full_module_name = f"{module_base_name}.{alias.name}" if module_base_name else alias.name
            
            resolved_path = resolve_import_path(full_module_name, self.current_file_dir, self.search_folder, node.level)
            if resolved_path:
                self.dependencies.add(resolved_path)

        # Always try to resolve the base module as well (e.g., 'worker.module')
        if module_base_name:
            base_path = resolve_import_path(module_base_name, self.current_file_dir, self.search_folder, node.level)
            if base_path:
                self.dependencies.add(base_path)

        self.generic_visit(node)


def find_all_dependencies(start_scripts: List[str], search_folder: str) -> Set[str]:
    """Finds all local dependencies for the starting scripts, searching recursively."""
    initial_paths = {os.path.realpath(p) for p in start_scripts}
    to_process = deque(initial_paths)
    all_found_dependencies = set(initial_paths)
    
    while to_process:
        current_file = to_process.popleft()
        
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
                tree = ast.parse(source_code, filename=current_file)
        except (IOError, SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read or parse '{current_file}'. Skipping. Error: {e}", file=sys.stderr)
            continue
            
        visitor = ImportVisitor(current_file, search_folder)
        visitor.visit(tree)
        
        new_dependencies = visitor.dependencies - all_found_dependencies
        for dep in new_dependencies:
            all_found_dependencies.add(dep)
            # Only add actual files to the processing queue
            if os.path.isfile(dep):
                 to_process.append(dep)
            
    return all_found_dependencies

def create_concatenated_file(file_list: List[str], search_folder: str, output_filename: str):
    """Creates the final text file with all the file contents and headers."""
    header = "=" * 80
    try:
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            outfile.write(f"--- START OF FILE {output_filename} ---\n\n")
            for file_path in file_list:
                relative_path = os.path.relpath(file_path, search_folder)
                outfile.write(f"{header}\ncat {relative_path}\n{header}\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                    outfile.write("\n\n")
                except IOError as e:
                    outfile.write(f"!!! ERROR: Could not read file {relative_path}: {e} !!!\n\n")
        print(f"Successfully created concatenated file: {output_filename}")
    except IOError as e:
        print(f"Error: Could not write to output file {output_filename}. {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main function to parse arguments and drive the process."""
    parser = argparse.ArgumentParser(
        description="Concatenates Python script(s) and all their local dependencies into a single text file.\n"
                    "It recursively finds modules imported by the script(s) within the specified project root folder.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(f"Example:\n"
               f"  python3 {os.path.basename(sys.argv[0])} project_root/ src/main.py")
    )

    parser.add_argument("folder", help="The top-level project root folder to search for dependencies.")
    parser.add_argument("python_scripts", nargs='+', help="One or more Python scripts to start the search from.")

    args = parser.parse_args()
    folder = args.folder
    python_scripts = args.python_scripts
    
    initial_script_paths = {os.path.realpath(p) for p in python_scripts}

    if not os.path.isdir(folder):
        parser.error(f"The project root folder '{folder}' does not exist or is not a directory.")

    for script in python_scripts:
        if not os.path.isfile(script):
            parser.error(f"The script '{script}' does not exist or is not a file.")

    print(f"Searching for dependencies in project root: {os.path.realpath(folder)}")
    print("Starting scripts:")
    for script in python_scripts:
        print(f"  - {script}")
    print("")

    all_files = find_all_dependencies(python_scripts, folder)

    sorted_deps = sorted(
        list(all_files),
        key=lambda x: (x not in initial_script_paths, x)
    )

    print("Found the following python files to concatenate:")
    for dep in sorted_deps:
        print(f"  - {os.path.relpath(dep, folder)}")
    print("-" * 20)
    
    folder_name = os.path.basename(os.path.normpath(folder))
    output_filename = f"{folder_name}_concatenated.txt"

    create_concatenated_file(sorted_deps, folder, output_filename)


if __name__ == "__main__":
    main()