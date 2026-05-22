#!/usr/bin/env python3
import argparse
import sys
import os

from shared_utils import summary, format_size, run_command

def main():
    """
    Main function to parse arguments and generate the output file.
    """
    # Using RawTextHelpFormatter to allow for newlines in the description.
    parser = argparse.ArgumentParser(
        description="""A utility to capture a snapshot of Git commits.\n
This script can operate in two modes:\n
1. Range Mode (with --base and --this):\n   - Generates a git log for the entire commit range.\n   - Finds all unique files changed within that range.\n   - Saves the contents of those files as they exist in the final '--this' commit.\n   - Output file is named like 'base_id-this_id.txt'.\n
2. Single Commit Mode (with only --this):\n   - Generates a git log for only the single specified commit.\n   - Finds all files changed specifically in that commit.\n   - Saves the contents of those files.\n   - Output file is named like 'this_id.txt'.""",
        epilog="""Example (Range Mode): ./save_commits.py --base a1b2c3d --this f9e8d7c\nExample (Single Commit Mode): ./save_commits.py --this f9e8d7c""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--base',
        help="Optional: The base commit ID (older commit). If omitted, runs in single commit mode."
    )
    parser.add_argument(
        '--this',
        required=True,
        help="The target commit ID (newer commit). This is always required."
    )

    args = parser.parse_args()

    this_commit = args.this
    # If base is not provided, default to this_commit to enter single-commit logic.
    base_commit = args.base if args.base else this_commit

    is_single_commit_mode = (base_commit == this_commit)

    if is_single_commit_mode:
        short_this_id = run_command(f"git rev-parse --short {this_commit}")
        output_filename = f"{short_this_id}.txt"
        history_command = f"git log --oneline -n 1 {this_commit}"
        files_changed_command = f"git diff --name-only {this_commit}^ {this_commit}"
        files_header = f"=== CHANGED FILES AND THEIR CONTENTS (in commit {short_this_id}) ===\n"
    else:
        short_base_id = run_command(f"git rev-parse --short {base_commit}")
        short_this_id = run_command(f"git rev-parse --short {this_commit}")
        output_filename = f"{short_base_id}-{short_this_id}.txt"
        history_command = f"git log --oneline {base_commit}..{this_commit}"
        files_changed_command = f"git diff --name-only {base_commit} {this_commit}"
        files_header = f"=== CHANGED FILES AND THEIR CONTENTS (between commits {short_base_id} and {short_this_id}) ===\n"

    # 1. Get the git history.
    git_history = run_command(history_command)

    # 2. Get the list of changed files.
    changed_files_str = run_command(files_changed_command)
    changed_files = changed_files_str.splitlines() if changed_files_str else []

    file_data = []
    
    # Read file contents BEFORE opening the output file to generate the summary first
    for file_path in changed_files:
        try:
            file_content_command = f"git show {this_commit}:{file_path}"
            file_content = run_command(file_content_command)
            size = len(file_content.encode('utf-8', errors='replace'))
        except Exception as e:
            file_content = f'{e}'
            size = 0
        file_data.append((file_path, file_content, size))

    commit_id_str = short_this_id if is_single_commit_mode else f"{short_base_id}..{short_this_id}"
    
    file_data_for_summary = [(fp, sz) for fp, _, sz in file_data]

    summary_text = summary(
        command_args=sys.argv,
        files_with_sizes=file_data_for_summary,
        commit_id=commit_id_str
    )

    print(summary_text)

    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(summary_text + "\n")
            f.write("=== GIT HISTORY ===\n")
            f.write(history_command + '\n\n')
            f.write(git_history)
            f.write("\n\n" + "====================" + "\n\n")

            if not file_data:
                f.write("No files were changed in the specified commit(s).\n")
            else:
                f.write(files_header)
                f.write(files_changed_command + '\n')
                for path, content, size in file_data:
                    f.write("\n" + "===" + f" FILE: {path} (Size: {format_size(size)}) " + "===" + "\n")
                    f.write(content)
                    f.write("\n" + "===" + "=" * len(f" FILE: {path} (Size: {format_size(size)}) ") + "===" + "\n")

        print(f"Successfully created {output_filename}")

    except IOError as e:
        print(f"Error writing to file {output_filename}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

