import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict

# A set of common text file extensions for quick lookups. Case-insensitive.
KNOWN_TEXT_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', 
    '.scss', '.json', '.yml', '.yaml', '.xml', '.csv', '.sh', '.bat', 
    '.ps1', '.ini', '.cfg', '.conf', '.log', 'dockerfile', '.sql'
}

def format_size(size_bytes: int) -> str:
    """Converts a size in bytes to a human-readable string (KB, MB, GB)."""
    if size_bytes == 0:
        return "0 B"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size_bytes >= power and n < len(power_labels) - 1:
        size_bytes /= power
        n += 1
    return f"{size_bytes:.2f} {power_labels[n]}" if n > 0 else f"{int(size_bytes)} {power_labels[n]}"

def analyze_directory(root_path: Path):
    """
    Analyzes files recursively, grouping them by type, summing their sizes,
    and finding the largest file of each type.
    """
    # Use defaultdict with a factory function for a more complex data structure.
    # The value for each extension will be a dictionary holding all relevant stats.
    def stats_factory():
        return {
            'total_size': 0,
            'count': 0,
            'largest_file_size': -1,
            'largest_file_path': None
        }
    file_stats = defaultdict(stats_factory)
    
    print(f"🔍 Scanning directory: {root_path}...")

    files_generator = root_path.rglob('*')
    
    total_files_scanned = 0
    for path in files_generator:
        try:
            if path.is_file():
                total_files_scanned += 1
                extension = path.suffix.lower() if path.suffix else '(no extension)'
                if path.name.lower() == 'dockerfile':
                    extension = 'dockerfile'

                size = path.stat().st_size
                stats_for_ext = file_stats[extension]
                
                # Update aggregate stats
                stats_for_ext['total_size'] += size
                stats_for_ext['count'] += 1
                
                # Check if this is the largest file of its type so far
                if size > stats_for_ext['largest_file_size']:
                    stats_for_ext['largest_file_size'] = size
                    stats_for_ext['largest_file_path'] = path
        
        except (PermissionError, FileNotFoundError) as e:
            print(f"⚠️  Skipping due to error: {e}")

    print(f"✅ Scan complete. Found {total_files_scanned} files.")
    
    # Sort the dictionary items by total size in descending order
    sorted_stats = sorted(file_stats.items(), key=lambda item: item[1]['total_size'], reverse=True)
    
    return sorted_stats

def print_report(stats: list, root_path: Path):
    """Prints the final formatted report table."""
    if not stats:
        print("\nNo files found to analyze.")
        return

    # Define column widths
    type_w, size_w, count_w, text_w, file_w = 15, 12, 8, 10, 50

    print("\n--- Folder Content Analysis Report ---")
    header = (
        f"{'File Type':<{type_w}} | {'Total Size':>{size_w}} | {'Count':>{count_w}} | "
        f"{'Is Text?':>{text_w}} | {'Largest File Example':<{file_w}}"
    )
    print(header)
    print(f"{'-'*type_w}-+-{'-'*size_w}-+-{'-'*count_w}-+-{'-'*text_w}-+-{'-'*file_w}")

    total_size = 0
    total_count = 0

    for ext, ext_stats in stats:
        total_size += ext_stats['total_size']
        total_count += ext_stats['count']
        
        formatted_size = format_size(ext_stats['total_size'])
        is_text = "Yes" if ext in KNOWN_TEXT_EXTENSIONS else "No"
        
        # Get and format the largest file path
        largest_path = ext_stats['largest_file_path']
        if largest_path:
            relative_path_str = str(largest_path.relative_to(root_path))
            # Truncate long paths to fit the column
            if len(relative_path_str) > file_w:
                relative_path_str = "..." + relative_path_str[-(file_w - 3):]
        else:
            relative_path_str = "N/A"
            
        row = (
            f"{ext:<{type_w}} | {formatted_size:>{size_w}} | {ext_stats['count']:>{count_w}} | "
            f"{is_text:>{text_w}} | {relative_path_str:<{file_w}}"
        )
        print(row)

    # Footer
    print(f"{'-'*type_w}-+-{'-'*size_w}-+-{'-'*count_w}-+-{'-'*text_w}-+-{'-'*file_w}")
    formatted_total_size = format_size(total_size)
    footer = (
        f"{'TOTAL':<{type_w}} | {formatted_total_size:>{size_w}} | {total_count:>{count_w}} | "
        f"{'':>{text_w}} | {'':<{file_w}}"
    )
    print(footer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scans a directory to report total file sizes grouped by type, including the largest file of each type.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "directory",
        nargs='?',
        default='.',
        help="The directory to analyze (default: current directory)."
    )
    args = parser.parse_args()
    
    root_path = Path(args.directory).resolve()
    
    if not root_path.is_dir():
        print(f"❌ Error: The path '{root_path}' is not a valid directory.")
        sys.exit(1)
        
    final_stats = analyze_directory(root_path)
    print_report(final_stats, root_path)
