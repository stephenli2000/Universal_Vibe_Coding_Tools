#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def run_command(command):
    """
    Executes a shell command and returns its output.
    Exits the script if the command fails.
    """
    try:
        # Execute the command. We use text=True to get stdout/stderr as strings.
        # check=True will raise a CalledProcessError if the command returns a non-zero exit code.
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Handle errors, such as invalid commit IDs or not being in a git repo.
        print(f"Error executing command: {e.cmd}", file=sys.stderr)
        print(f"Return code: {e.returncode}", file=sys.stderr)
        err_msg = f"{e.stderr.strip()}"
        print(f"{err_msg}", file=sys.stderr)
        return err_msg
    except FileNotFoundError:
        # Handle the case where 'git' is not installed or not in the system's PATH.
        print("Error: 'git' command not found.", file=sys.stderr)
        print("Please ensure Git is installed and accessible in your system's PATH.", file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main function to parse arguments and generate the output file.
    """
    # Using RawTextHelpFormatter to allow for newlines in the description.
    parser = argparse.ArgumentParser(
        description="""A utility to capture a snapshot of Git commits.

This script can operate in two modes:

1. Range Mode (with --base and --this):
   - Generates a git log for the entire commit range.
   - Finds all unique files changed within that range.
   - Saves the contents of those files as they exist in the final '--this' commit.
   - Output file is named like 'base_id-this_id.txt'.

2. Single Commit Mode (with only --this):
   - Generates a git log for only the single specified commit.
   - Finds all files changed specifically in that commit.
   - Saves the contents of those files.
   - Output file is named like 'this_id.txt'.""",
        epilog="""Example (Range Mode): ./save_files.py --base a1b2c3d --this f9e8d7c
Example (Single Commit Mode): ./save_files.py --this f9e8d7c""",
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
        print(f"Running in single commit mode for {this_commit}...")
        short_this_id = run_command(f"git rev-parse --short {this_commit}")
        output_filename = f"{short_this_id}.txt"
        history_command = f"git log --oneline -n 1 {this_commit}"
        files_changed_command = f"git diff --name-only {this_commit}^ {this_commit}"
        files_header = f"=== CHANGED FILES AND THEIR CONTENTS (in commit {short_this_id}) ===\n"
    else:
        print(f"Running in range mode between {base_commit} and {this_commit}...")
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

    if not changed_files:
        print("Warning: No files were found in the specified commit(s).")

    # 3. Write all the collected information to the output file.
    print(f"Writing information to {output_filename}...")
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write("=== GIT HISTORY ===\n")
            f.write(history_command + '\n\n')
            f.write(git_history)
            f.write("\n\n" + "====================" + "\n\n")

            if not changed_files:
                f.write("No files were changed in the specified commit(s).\n")
            else:
                f.write(files_header)
                f.write(files_changed_command + '\n')
                for file_path in changed_files:
                    try:
                        print(f"  - Reading content of: {file_path}")
                        # Use `git show` to get the content of a file as it exists in the target commit.
                        file_content_command = f"git show {this_commit}:{file_path}"
                        file_content = run_command(file_content_command)
                    except Exception as e:
                        file_content = f'{e}'

                    f.write("\n" + "===" + f" FILE: {file_path} " + "===" + "\n")
                    f.write(file_content)
                    f.write("\n" + "===" + "=" * len(f" FILE: {file_path} ") + "===" + "\n")

        print(f"\nSuccessfully created {output_filename}")

    except IOError as e:
        print(f"Error writing to file {output_filename}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

