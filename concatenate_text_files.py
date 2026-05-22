import os
import sys
import argparse
from pathlib import Path
from typing import Optional

from shared_utils import summary, write_concatenated_artifact

# --- Configuration ---
ALLOWED_EXTENSIONS = {
    '.py', '.tsx', '.css', '.js', '.conf', '.json',
    '.html', '.yml', '.yaml', '.txt', '.sh', '.md', '.ini', '.ts'
}
CODE_EXTENSIONS = {
    '.py', '.tsx', '.js', '.ts', '.html', '.css', '.sh',
}
PYTHON_EXTENSIONS = {'.py'}
ALLOWED_FILENAMES = {'dockerfile'}
EXCLUDED_FILENAMES = {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'gmail_token.json', 'gmail_credentials.json'}
EXCLUDED_DIRS = {
    'node_modules', '.git', 'dist', 'build', 'out',
    '.vscode', '__pycache__', '.idea', '.venv'
}

def get_display_path(file_path: Path, base_dir: Optional[Path]) -> Path:
    """Returns a relative path if possible, otherwise the absolute path."""
    try:
        if base_dir:
            return file_path.relative_to(base_dir)
        else:
            return file_path.relative_to(Path.cwd())
    except ValueError:
        return file_path.absolute()

def find_files_to_process(input_dir: Path, code_only: bool, py_only: bool, recursive: bool) -> list[tuple[Path, int, Path]]:
    """
    Finds all files in the directory that match the allowlist and are not in the blocklist.
    Returns a list of tuples containing (file_path, file_size, origin_base_directory).
    """
    files_with_info = []
    print(f"\n🔍 Searching for files in directory '{input_dir}'...")
    
    if recursive:
        print(f"   (Including subfolders, ignoring: {', '.join(EXCLUDED_DIRS)})")
    else:
        print("   (Skipping subfolders)")

    if py_only:
        extensions_to_check = PYTHON_EXTENSIONS
        print("   (Filtering for Python files only)")
    elif code_only:
        extensions_to_check = CODE_EXTENSIONS
        print("   (Filtering for code files only)")
    else:
        extensions_to_check = ALLOWED_EXTENSIONS

    for root, dirs, files in os.walk(input_dir):
        if not recursive:
            dirs[:] = []  # Prevent os.walk from descending into subdirectories
        else:
            dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED_DIRS]
        
        for filename in files:
            if filename.lower() in EXCLUDED_FILENAMES:
                continue
            
            file_path = Path(root) / filename
            if file_path.name.lower() in ALLOWED_FILENAMES or file_path.suffix.lower() in extensions_to_check:
                try:
                    size = file_path.stat().st_size
                    files_with_info.append((file_path, size, input_dir))
                except OSError as e:
                    print(f"--> [Warning] Could not access file stats for '{file_path}': {e}")

    return files_with_info

def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(
        description="Concatenate specified text-based files and folders into a single text file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Unified input handles both files and folders natively
    parser.add_argument("inputs", nargs="+", help="Files and/or directories to include.")
    
    # Execution Modifiers
    parser.add_argument("-r", "--recursive", action="store_true", help="Include subfolders recursively for directory inputs.")

    # Content filters (Only apply to folders)
    filter_group = parser.add_mutually_exclusive_group()
    filter_group.add_argument("--code-only", action="store_true", help="Only include code extensions when scanning directories.")
    filter_group.add_argument("--py-only", action="store_true", help="Only include Python (.py) files when scanning directories.")
    
    parser.add_argument("-o", "--output", help="Specify the output file name.")
    
    args = parser.parse_args()
    
    found_files = []

    # Process all unified inputs (Files + Folders)
    for input_str in args.inputs:
        input_path = Path(input_str).resolve()
        
        if not input_path.exists():
            print(f"❌ Error: '{input_str}' not found. Skipping.")
            continue
            
        if input_path.is_file():
            # Explicitly added files skip the extension filter checks
            found_files.append((input_path, input_path.stat().st_size, None))
            
        elif input_path.is_dir():
            found_files.extend(find_files_to_process(input_path, args.code_only, args.py_only, args.recursive))

    # Remove duplicates (in case explicitly listed files overlap with directory searches)
    unique_files = {}
    for path, size, base_dir in found_files:
        if path not in unique_files:
            unique_files[path] = (size, base_dir)
            
    # Rebuild list and sort files by size in descending order
    files_to_process = [(path, size, base_dir) for path, (size, base_dir) in unique_files.items()]
    files_to_process.sort(key=lambda item: item[1], reverse=True)

    if not files_to_process:
        print("\n🤷 No matching files found to concatenate.")
        return

    first_input = Path(args.inputs[0]).resolve()
    target_dir_for_git = str(first_input if first_input.is_dir() else first_input.parent)

    if args.output:
        output_file = Path(args.output)
    else:
        output_name = first_input.name if first_input.is_dir() else first_input.stem
        output_file = Path(f"{output_name}_concat.txt")

    file_data_for_summary = []
    file_items = []
    for f_path, size, base_dir in files_to_process:
        display_path = get_display_path(f_path, base_dir)
        if base_dir:
            display_path = Path(base_dir.name) / display_path
        file_data_for_summary.append((str(display_path), size))
        file_items.append((str(display_path), f_path))
        
    summary_text = summary(
        command_args=sys.argv, 
        files_with_sizes=file_data_for_summary,
        target_dir=target_dir_for_git
    )
    print(summary_text)
    
    write_concatenated_artifact(str(output_file), file_items, summary_text)
    

if __name__ == "__main__":
    main()
