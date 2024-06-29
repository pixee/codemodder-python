import difflib

import libcst as cst


def create_diff(original_lines: list[str], new_lines: list[str]) -> str:
    diff_lines = list(difflib.unified_diff(original_lines, new_lines))
    return difflines_to_str(diff_lines)


def create_diff_from_tree(original_tree: cst.Module, new_tree: cst.Module) -> str:
    """
    Create a diff between the original and output trees.
    """
    return create_diff(
        original_tree.code.splitlines(keepends=True),
        new_tree.code.splitlines(keepends=True),
    )


def create_diff_and_linenums(
    original_lines: list[str], new_lines: list[str]
) -> tuple[str, list[int]]:
    diff_lines = list(difflib.unified_diff(original_lines, new_lines))
    return difflines_to_str(diff_lines), calc_line_num_changes(diff_lines)


def calc_line_num_changes(diff_lines: list[str]) -> list[int]:
    """
    Calculates the line numbers changed from a list of diff lines
    Returns a list with unique elements.
    """
    if not diff_lines:
        return []

    changed_line_nums: list[int] = []
    current_line_number = 0
    original_line_number = 0

    for line in diff_lines:
        if line.startswith("@@"):
            # Extract the starting line number for the updated file from the diff metadata.
            # The format is @@ -x,y +a,b @@, where a is the starting line number in the updated file.
            start_line_original, start_line_updated = line.split(" ")[1:3]
            original_line_number = int(start_line_original.split(",")[0][1:]) - 1
            current_line_number = int(start_line_updated.split(",")[0][1:]) - 1

        elif line.startswith("+"):
            # Increment line number for each line in the updated file
            current_line_number += 1
            if not line.startswith("+++"):  # Ignore the diff metadata lines
                changed_line_nums.append(current_line_number)

        elif line.startswith("-"):
            # Increment line number for each line in the original file
            original_line_number += 1
            if not line.startswith("---"):  # Ignore the diff metadata lines
                changed_line_nums.append(original_line_number)

        else:
            # Increment line numbers for unchanged/context lines
            original_line_number += 1
            current_line_number += 1

    return list(set(changed_line_nums))


def difflines_to_str(diff_lines: list[str]) -> str:
    if not diff_lines:
        return ""
    # All but the last diff line should end with a newline
    # The last diff line should be preserved as-is (with or without a newline)
    diff_lines = [
        line if line.endswith("\n") else line + "\n" for line in diff_lines[:-1]
    ] + [diff_lines[-1]]
    return "".join(diff_lines)
