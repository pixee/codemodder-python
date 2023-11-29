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
    return difflines_to_str(diff_lines), calc_new_line_nums(diff_lines)


def calc_new_line_nums(diff_lines: list[str]) -> list[int]:
    if not diff_lines:
        return []

    added_line_nums = []
    current_line_number = 0

    for line in diff_lines:
        if line.startswith("@@"):
            # Extract the starting line number for the updated file from the diff metadata.
            # The format is @@ -x,y +a,b @@, where a is the starting line number in the updated file.
            start_line = line.split(" ")[2]
            current_line_number = (
                int(start_line.split(",")[0][1:]) - 1
            )  # Subtract 1 because line numbers are 1-indexed

        elif line.startswith("+"):
            # Increment line number for each line in the updated file
            current_line_number += 1
            if not line.startswith("++"):  # Ignore the diff metadata lines
                added_line_nums.append(current_line_number)

        elif not line.startswith("-"):
            # Increment line number for unchanged/context lines
            current_line_number += 1

    return added_line_nums


def difflines_to_str(diff_lines: list[str]) -> str:
    if not diff_lines:
        return ""
    # All but the last diff line should end with a newline
    # The last diff line should be preserved as-is (with or without a newline)
    diff_lines = [
        line if line.endswith("\n") else line + "\n" for line in diff_lines[:-1]
    ] + [diff_lines[-1]]
    return "".join(diff_lines)
