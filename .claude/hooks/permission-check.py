#!/usr/bin/env python3
"""
Permission Check Hook

Validates write permissions before agent delegation to prevent wasted operations.
Blocks agent delegation when target paths lack write access.
"""

import json
import os
import sys
from pathlib import Path
import re


def extract_file_paths(agent_args: str) -> list[str]:
    """Extract potential file paths from agent arguments."""
    paths = []

    # Look for common file path patterns in agent arguments
    file_patterns = [
        r'--file[^"\s]*["\s]+([^"\s]+)',  # --file path or --file "path"
        r'file[_-]?path[^"\s]*[:\s=]+([^"\s]+)',  # file_path: path
        r'([^"\s]+\.(?:md|py|ts|js|json|yaml|yml|txt))',  # File extensions
        r'(/[^"\s]+)',  # Unix-style absolute paths
        r'([A-Za-z]:[^"\s]+)',  # Windows-style paths
    ]

    for pattern in file_patterns:
        matches = re.findall(pattern, agent_args, re.IGNORECASE)
        paths.extend(matches)

    # Clean up paths - remove quotes and normalize
    cleaned_paths = []
    for path in paths:
        path = path.strip('\'"')
        if path and not path.startswith('http'):  # Skip URLs
            cleaned_paths.append(path)

    return cleaned_paths


def check_write_permissions(file_path: str) -> tuple[bool, str]:
    """
    Check if we have write permissions for a file path.
    Returns (has_permission, error_message)
    """
    try:
        path = Path(file_path).resolve()

        # If file exists, check if we can write to it
        if path.exists():
            if not os.access(path, os.W_OK):
                return False, f"No write permission to existing file: {path}"
        else:
            # If file doesn't exist, check if we can write to parent directory
            parent = path.parent
            if not parent.exists():
                # Try to find the closest existing parent
                while parent and not parent.exists():
                    parent = parent.parent
                if not parent:
                    return False, f"Cannot determine write permissions for: {path}"

            if not os.access(parent, os.W_OK):
                return False, f"No write permission to directory: {parent}"

        return True, ""

    except Exception as e:
        return False, f"Permission check failed for {file_path}: {str(e)}"


def main():
    """Main hook execution."""
    try:
        # Read tool usage data from stdin
        input_data = sys.stdin.read()
        if not input_data.strip():
            # No data to process
            sys.exit(0)

        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            # Not JSON data, ignore
            sys.exit(0)

        # Check if this is an Agent tool call
        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})

        if tool_name != 'Agent':
            # Not an agent delegation, no permission check needed
            sys.exit(0)

        # Extract potential file paths from agent prompt and description
        agent_prompt = tool_input.get('prompt', '')
        agent_description = tool_input.get('description', '')
        combined_text = f"{agent_prompt} {agent_description}"

        file_paths = extract_file_paths(combined_text)

        if not file_paths:
            # No file paths detected, allow delegation
            sys.exit(0)

        # Deduplicate file paths to avoid duplicate error messages
        unique_file_paths = list(set(file_paths))

        # Check write permissions for all detected paths
        permission_errors = []
        for file_path in unique_file_paths:
            has_permission, error_msg = check_write_permissions(file_path)
            if not has_permission:
                permission_errors.append(error_msg)

        if permission_errors:
            # Block delegation due to permission issues
            error_message = "❌ Agent delegation blocked - Write permission errors:\n"
            for error in permission_errors[:5]:  # Limit to first 5 errors
                error_message += f"  • {error}\n"

            if len(permission_errors) > 5:
                error_message += f"  ... and {len(permission_errors) - 5} more permission issues\n"

            error_message += "\n💡 Fix file permissions before delegating to agents."

            print(error_message, file=sys.stderr)
            sys.exit(2)  # Block the delegation

        # All paths have valid permissions
        sys.exit(0)

    except Exception as e:
        # Hook failed, but don't block the operation
        print(f"Permission check hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()