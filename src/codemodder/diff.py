import difflib


def create_diff(original_lines: list[str], new_lines: list[str]) -> str:
    diff_lines = list(difflib.unified_diff(original_lines, new_lines))

    # All but the last diff line should end with a newline
    # The last diff line should be preserved as-is (with or without a newline)
    diff_lines = [
        line if line.endswith("\n") else line + "\n" for line in diff_lines[:-1]
    ] + [diff_lines[-1]]
    return "".join(diff_lines)
